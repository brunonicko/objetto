# -*- coding: utf-8 -*-

from uuid import uuid4
from weakref import WeakSet
from threading import local
from typing import TYPE_CHECKING
from contextlib import contextmanager
from weakref import ref

from six import iteritems
from pyrsistent import pset

from .utils.base import Base, final
from .utils.storage import Storage
from .utils.namespace import Namespace
from .utils.subject_observer import Subject
from .utils.rw_lock import RWThreadingLock, RWLock
from ._structures import (
    Action,
    Snapshot,
    ObserverError,
    AbstractChange,
    BatchChange,
    InitializedChange,
    StateChange,
    State,
    Commit,
)
from ._constants import Phase
from ._exceptions import RevertException, ObserversError, RejectException

if TYPE_CHECKING:
    from typing import Any, Optional, List, Union, Iterator, Tuple, Hashable, Set

    from pyrsistent.typing import PMap

    from .utils.storage import Evolver, AbstractStorage
    from .utils.pointer import Pointer
    from .utils.rw_lock import AbstractRWLock
    from ._structures import Store
    from ._objects import AbstractObject, AbstractHistoryObject

    ObjPointer = Pointer[AbstractObject]

__all__ = ["Application", "resolve_history"]


@final
class _Writer(Base):
    """Keeps track of changes to the application evolver in the form of commits."""

    __slots__ = ("__evolver", "__commits")

    def __init__(self, evolver, commits):
        # type: (Evolver[Pointer[AbstractObject], Store], List[Commit]) -> None
        self.__evolver = evolver
        self.__commits = commits

    @contextmanager
    def _pinned_hierarcy_context(self, obj):
        # type: (AbstractObject) -> Iterator[Tuple[AbstractObject, ...]]

        # Get whether it is the first time we are pinning the hierarchy for the object.
        first = not obj._Writer__pinned_count  # type: bool

        # It is the first time pinning the hierarchy from this object.
        cached_parents = []  # type: List[AbstractObject]
        if first:
            assert obj._Writer__pinned_hierarchy is None

            # Traverse up the hierarchy.
            hierarchy = []  # type: List[AbstractObject]
            _parent = obj  # type: Optional[AbstractObject]
            i = -1
            while _parent is not None:

                # The parent has pinned its hierarchy already, utilize its cache.
                if _parent._Writer__pinned_hierarchy is not None:
                    assert i > -1
                    hierarchy.extend(_parent._Writer__pinned_hierarchy)
                    break
                else:

                    # The parent doesn't have its hierarchy pinned, we will do it.
                    hierarchy.append(_parent)
                    if _parent is obj:
                        _parent_store = self.__evolver.get(obj.pointer, None)
                        if _parent_store is None:
                            _parent_ref = None
                        else:
                            _parent_ref = _parent_store.parent_ref
                    else:
                        _parent_ref = self.query(_parent).parent_ref
                    if _parent_ref is not None:
                        _parent = _parent_ref()
                        if _parent is None:
                            error = "parent is no longer in memory, can't mutate"
                            raise RuntimeError(error)
                    else:
                        _parent = None
                    i += 1

            # Cache the hierarchy as a tuple.
            pinned_hierarchy = obj._Writer__pinned_hierarchy = tuple(hierarchy)

            # Cache the hierarchy in the parents which didn't have it pinned.
            assert i >= 0
            while i > 0:
                _parent = pinned_hierarchy[i]
                assert _parent is not None
                if not _parent._Writer__pinned_count:
                    cached_parents.append(_parent)
                    _parent._Writer__pinned_count += 1
                    _parent._Writer__pinned_hierarchy = pinned_hierarchy[i:]
                i -= 1

        # Not the first time, just use the cached pinned hierarchy.
        else:
            assert obj._Writer__pinned_hierarchy is not None
            pinned_hierarchy = obj._Writer__pinned_hierarchy

        # Increment the pinned count for the pinned hierarchy going up.
        for parent in pinned_hierarchy:
            parent._Writer__pinned_count += 1
        try:
            yield pinned_hierarchy
        finally:

            # Decrement the pinned count for the pinned hierarchy going up.
            for parent in pinned_hierarchy:
                parent._Writer__pinned_count -= 1

            # If previously we pinned any of the parents for caching, decrement them.
            for parent in cached_parents:
                parent._Writer__pinned_count -= 1

                # If we reached zero pinned count for parent, clear cached hierarchy.
                if not parent._Writer__pinned_count:
                    assert first
                    parent._Writer__pinned_hierarchy = None

            # If we reached zero pinned count for the object, clear cached hierarchy.
            if first:
                obj._Writer__pinned_hierarchy = None

    @contextmanager
    def _action_context(self, obj, change, set_acting_flag):
        # type: (AbstractObject, AbstractChange, bool) -> Iterator

        # Can't act if already acting.
        if obj._Writer__acting:
            error = "'{}' object already acting".format(type(obj).__fullname__)
            raise RuntimeError(error)

        with self._pinned_hierarcy_context(obj) as hierarchy:

            # Remember current storage and commit index.
            storage = self.__evolver.storage()
            commit_index = len(self.__commits) - 1

            # Prepare actions.
            previous_parent = obj
            previous_locations = ()  # type: Tuple[Hashable, ...]
            action_uuid = uuid4()
            app_action = Action(
                uuid=action_uuid,
                app=obj.app,
                sender=None,
                source=obj,
                change=change,
                locations=previous_locations,
            )
            previous_action = app_action.set(sender=obj)
            actions = [previous_action]
            for parent in hierarchy[1:]:

                # Get state and location of previous parent.
                parent_state = self.__evolver.query(parent.pointer).state
                location = parent.__locate_child__(previous_parent, parent_state)

                # Make next action.
                previous_locations = previous_locations + (location,)
                action = previous_action.set(
                    sender=parent, locations=previous_locations
                )
                actions.append(action)
                previous_parent = parent

            # Start acting.
            if set_acting_flag:
                obj._Writer__acting = True
            try:

                # Run PRE reactions.
                for action in actions:
                    assert action.sender is not None
                    sender_cls = type(action.sender)
                    for reaction_descriptor in sender_cls._reaction_descriptors:
                        reaction_descriptor.__get__(
                            action.sender, sender_cls
                        )(action, Phase.PRE)

                # Store PRE commits.
                pre_storage = self.__evolver.storage()
                for action in actions + [app_action]:
                    commit = Commit(
                        storage=pre_storage,
                        action=action,
                        phase=Phase.PRE,
                    )
                    self.__commits.append(commit)

                # Perform changes.
                yield

                # Store POST commits.
                post_storage = self.__evolver.storage()
                for action in actions + [app_action]:
                    commit = Commit(
                        storage=post_storage,
                        action=action,
                        phase=Phase.POST,
                    )
                    self.__commits.append(commit)

                # Run POST reactions.
                for action in actions:
                    assert action.sender is not None
                    sender_cls = type(action.sender)
                    for reaction_descriptor in sender_cls._reaction_descriptors:
                        reaction_descriptor.__get__(
                            action.sender, sender_cls
                        )(action, Phase.POST)

            # Reject action.
            except RejectException as reject_exception:
                if reject_exception.action_uuid != action_uuid:
                    raise
                self.__evolver = storage.evolver()
                del self.__commits[commit_index + 1:]
                obj._Writer__acting = False
                reject_exception.callback()

            # Stop acting.
            finally:
                if set_acting_flag:
                    obj._Writer__acting = False

    def _prepare_parent(
        self,
        obj,  # type: AbstractObject
        new_state,  # type: State
        old_state=None,  # type: Optional[State]
        hierarchy=None,  # type: Optional[Tuple[AbstractObject, ...]]
    ):
        # type: (...) -> Tuple[Set[ObjPointer], Set[ObjPointer], Set[ObjPointer]]
        app = obj.app

        # No hierarchy provided, consider the obj only.
        if hierarchy is None:
            hierarchy = (obj,)

        # Get old and new children, releases and adoptions.
        if old_state is not None:
            old_children_pointers = set(old_state.children_pointers)
        else:
            old_children_pointers = set()
        new_children_pointers = set(new_state.children_pointers)
        release_pointers = old_children_pointers.difference(new_children_pointers)
        adoption_pointers = new_children_pointers.difference(old_children_pointers)

        # Check if hierarchy changes are allowed.
        if release_pointers:
            for release_pointer in release_pointers:
                release = release_pointer.obj
                if release._Writer__pinned_count:
                    error = "can't change parent while hierarchy is locked"
                    raise RuntimeError(error)

        hierarchy_pointers = set()  # type: Set[Pointer[AbstractObject]]
        if adoption_pointers:
            hierarchy_pointers.update(o.pointer for o in hierarchy)

        for adoption_pointer in adoption_pointers:
            adoption = adoption_pointer.obj

            if adoption.pointer in hierarchy_pointers:
                error = "parent cycle detected"
                raise RuntimeError(error)

            child_app = adoption.app
            if child_app is not app:
                error = "child/parent app mismatch"
                raise RuntimeError(error)

            child_store = self.query(adoption)
            if child_store.parent_ref is not None:
                error = "{} already parented".format(adoption)
                raise RuntimeError(error)

            if adoption._Writer__pinned_count:
                error = "can't change parent while hierarchy is locked"
                raise RuntimeError(error)

        # Get old and new historical children, and adoptions.
        if old_state is not None:
            old_historical_pointers = set(
                cp for cp, r in iteritems(old_state.children_pointers) if r.historical
            )
        else:
            old_historical_pointers = set()
        new_historical_pointers = set(
            cp for cp, r in iteritems(new_state.children_pointers) if r.historical
        )
        historical_adoption_pointers = new_historical_pointers.difference(
            old_historical_pointers
        )

        return adoption_pointers, release_pointers, historical_adoption_pointers

    def _parent(
        self,
        obj,  # type: AbstractObject
        history,  # type: Optional[AbstractHistoryObject]
        adoption_pointers,  # type: Set[Pointer[AbstractObject]]
        release_pointers,  # type: Set[Pointer[AbstractObject]]
        historical_adoption_pointers,  # type: Set[Pointer[AbstractObject]]
    ):
        # type: (...) -> None

        # Get weak references to obj and history.
        obj_ref = ref(obj)
        if history is None:
            history_ref = None
        else:
            history_ref = ref(history)

        # For new adoptions, mark their last parents' histories to be flushed.
        history_pointers_to_flush = set()
        for adoption_pointer in adoption_pointers:
            child_store = self.__evolver.query(adoption_pointer)
            if child_store.last_parent_history_ref is None:
                continue
            child_last_parent_history = child_store.last_parent_history_ref()
            if child_last_parent_history is None:
                continue
            if child_last_parent_history is not history:
                history_pointers_to_flush.add(child_last_parent_history.pointer)

        # Mark the historical adoptions' old history to be flushed.
        true_historical_adoption_pointers = set()
        for historical_adoption_pointer in historical_adoption_pointers:
            adoption_store = self.__evolver.query(historical_adoption_pointer)

            # Historied adoption has its own history, skip it.
            if adoption_store.history is not None:
                continue
            true_historical_adoption_pointers.add(historical_adoption_pointer)

            # Historied adoption has a provided history, mark to flush it.
            adoption_old_history = resolve_history(
                historical_adoption_pointer.obj, self.__evolver
            )
            if adoption_old_history is None:
                continue
            if adoption_old_history is not history:
                history_pointers_to_flush.add(adoption_old_history.pointer)

        # Flush histories.
        for history_pointer_to_flush in history_pointers_to_flush:
            history_to_flush = history_pointer_to_flush.obj
            history_to_flush.flush()

        # Update reference to parent in releases and adoptions.
        for release_pointer in release_pointers:
            adoption_store = self.__evolver.query(release_pointer)
            self.__evolver.update({
                release_pointer: adoption_store.set(
                    parent_ref=None,
                )
            })
        for adoption_pointer in adoption_pointers:
            adoption_store = self.__evolver.query(adoption_pointer)
            self.__evolver.update({
                adoption_pointer: adoption_store.set(
                    parent_ref=obj_ref,
                    last_parent_history_ref=history_ref,
                )
            })

        # History propagation.
        for historical_adoption_pointer in true_historical_adoption_pointers:
            historical_adoption_store = self.__evolver.query(
                historical_adoption_pointer
            )
            self.__evolver.update({
                historical_adoption_pointer: historical_adoption_store.set(
                    history_provider_ref=obj_ref
                )
            })

    @contextmanager
    def batch_context(self, obj, name, kwargs):
        # type: (AbstractObject, str, PMap[str, Any]) -> Iterator
        self.query(obj)
        change = BatchChange(name=name, kwargs=kwargs)
        with self._action_context(obj, change, False):
            yield

    def query(self, obj):
        # type: (AbstractObject) -> Store
        store = self.__evolver.get(obj.pointer, None)
        if store is None:
            error = "'{}' state not initialized".format(type(obj).__fullname__)
            raise RuntimeError(error)
        return store

    def init_store(self, obj, store):
        # type: (AbstractObject, Store) -> None

        # Already initialized.
        if self.__evolver.get(obj.pointer, None) is not None:
            error = "'{}' state already initialized".format(type(obj).__fullname__)
            raise RuntimeError(error)

        # Can't be acting.
        if obj._Writer__acting:
            error = "'{}' object is acting, can't initialize".format(
                type(obj).__fullname__
            )
            raise RuntimeError(error)

        change = InitializedChange(state=store.state)
        with self._action_context(obj, change, True):

            # Parent.
            adoption_pointers, release_pointers, historical_adoption_pointers = (
                self._prepare_parent(obj, store.state)
            )
            self._parent(
                obj,
                store.history,
                adoption_pointers,
                release_pointers,
                historical_adoption_pointers,
            )

            # Update evolver.
            self.__evolver.update({obj.pointer: store})

    def act(self, obj, new_state, event=None, undo_event=None):
        # type: (AbstractObject, State, Any, Any) -> None

        # Get store.
        store = self.query(obj)

        # Pin the hierarchy.
        with self._pinned_hierarcy_context(obj) as hierarchy:

            # Get history and old state.
            history = resolve_history(obj, self.__evolver)
            old_state = store.state

            # Prepare parent.
            adoption_pointers, release_pointers, historical_adoption_pointers = (
                self._prepare_parent(
                    obj,
                    new_state,
                    old_state=old_state,
                    hierarchy=hierarchy,
                )
            )

            # Prepare state change.
            change = StateChange(
                event=event,
                undo_event=undo_event,
                old_state=old_state,
                new_state=new_state,
                adoption_pointers=pset(adoption_pointers),
                release_pointers=pset(release_pointers),
            )

            # Enter an action context.
            with self._action_context(obj, change, True):

                # Perform parenting.
                self._parent(
                    obj,
                    history,
                    adoption_pointers,
                    release_pointers,
                    historical_adoption_pointers,
                )

                # Update object store.
                self.__evolver.update({obj.pointer: store.set(state=new_state)})

            # Push changes to history.
            if history is not None:
                history.__push_change__(change)


@final
class Application(Base):
    """
    Provides contexts for reading from and writing to object's states.

    :param type_safe: Whether should perform runtime type checks.
    :param thread_safe: Whether should acquire thread locks.
    """

    __slots__ = (
        "__weakref__",
        "__lock",
        "__local",
        "__type_safe",
        "__thread_safe",
        "__context_safe",
        "__storage",
        "__evolver",
        "__commits",
        "__snapshot_storages",
        "__subject",
    )

    def __init__(self, type_safe=True, thread_safe=False, context_safe=True):
        # type: (bool, bool, bool) -> None

        if thread_safe:
            if not context_safe:
                error = "application has to be context safe in order to be thread safe"
                raise ValueError(error)
            self.__lock = RWThreadingLock()  # type: AbstractRWLock
            self.__local = local()  # type: Union[local, Namespace]
        else:
            self.__lock = RWLock()
            self.__local = Namespace()

        self.__type_safe = bool(type_safe)  # type: bool
        self.__thread_safe = bool(thread_safe)  # type: bool
        self.__context_safe = bool(context_safe)  # type: bool
        self.__storage = Storage()  # type: Storage[Pointer[AbstractObject], Store]
        self.__evolver = None  # type: Optional[Evolver[Pointer[AbstractObject], Store]]
        self.__commits = []  # type: List[Commit]
        self.__snapshot_storages = WeakSet()  # type: WeakSet[Storage]
        self.__subject = Subject(self)  # type: Subject[Application]

    @contextmanager
    def _AbstractObject__read_context(
        self,
        snapshot=None,  # type: Optional[Snapshot]
    ):
        # type: (...) -> Iterator[Storage[Pointer[AbstractObject], Store]]
        with self.__lock.read_context():
            try:
                previous_snapshot = self.__local.snapshot  # type: Optional[Snapshot]
            except AttributeError:
                previous_snapshot = None

            if snapshot is not None:
                if snapshot.storage not in self.__snapshot_storages:
                    error = "snapshot can't be used or no longer valid"
                    raise ValueError(error)
                self.__local.snapshot = snapshot
                storage = (
                    snapshot.storage
                )  # type: Storage[Pointer[AbstractObject], Store]
            elif previous_snapshot is not None:
                storage = previous_snapshot.storage
            elif self.__evolver is not None:
                storage = self.__evolver.storage()
            else:
                storage = self.__storage

            try:
                yield storage
            finally:
                if previous_snapshot is None:
                    if snapshot is not None:
                        del self.__local.snapshot
                else:
                    self.__local.snapshot = previous_snapshot

    @contextmanager
    def _AbstractObject__write_context(self):
        # type: () -> Iterator[_Writer]
        with self.__lock.write_context():
            first = self.__evolver is None  # type: bool
            if first:
                self.__evolver = self.__storage.evolver()

            assert self.__evolver is not None

            storage = self.__evolver.storage()
            commit_index = len(self.__commits) - 1
            writer = _Writer(self.__evolver, self.__commits)
            try:
                yield writer
            except Exception as e:
                if first:
                    self.__evolver = None
                    assert commit_index == -1
                else:
                    self.__evolver = storage.evolver()
                del self.__commits[commit_index + 1:]

                if isinstance(e, RevertException):
                    pass
                else:
                    raise
            else:
                if first:

                    # Get last storage and commits.
                    last_storage = self.__evolver.storage()
                    commits = tuple(self.__commits)

                    # Reset evolver and commits.
                    self.__evolver = None
                    self.__commits = []

                    observer_errors = []  # type: List[ObserverError]
                    with self._AbstractObject__read_context():
                        for commit in commits:

                            # Update storage.
                            self.__storage = commit.storage

                            # Send from subject and collect exception information.
                            if commit.action.sender is None:
                                subject = commit.action.app._subject
                            else:
                                subject = commit.action.sender._subject
                            exception_infos = subject.send(commit.action, commit.phase)
                            for exception_info in exception_infos:
                                observer_errors.append(
                                    ObserverError(
                                        exception_info=exception_info,
                                        action=commit.action,
                                        phase=commit.phase,
                                    )
                                )

                        # After all commits, make sure storage is finally updated.
                        self.__storage = last_storage

                    # If we had exceptions raised by observers, raise.
                    if observer_errors:
                        raise ObserversError(observer_errors=observer_errors)

    def take_snapshot(self):
        # type: () -> Snapshot
        with self.__lock.read_context():
            if self.__evolver is not None:
                error = "can't take snapshot while in a write context"
                raise RuntimeError(error)

            try:
                return self.__local.snapshot
            except AttributeError:
                snapshot = Snapshot(storage=self.__storage)
                self.__snapshot_storages.add(snapshot.storage)
                return snapshot

    @property
    def type_safe(self):
        # type: () -> bool
        return self.__type_safe

    @property
    def thread_safe(self):
        # type: () -> bool
        return self.__thread_safe

    @property
    def context_safe(self):
        # type: () -> bool
        return self.__context_safe

    @contextmanager
    def require_context(self):
        # type: () -> Iterator
        if self.__context_safe:
            with self.__lock.require_context():
                yield
        else:
            with self.__lock.read_context():
                yield

    @contextmanager
    def require_read_context(self):
        # type: () -> Iterator
        if self.__context_safe:
            with self.__lock.require_read_context():
                yield
        else:
            with self.__lock.read_context():
                yield

    @contextmanager
    def require_write_context(self):
        # type: () -> Iterator
        if self.__context_safe:
            with self.__lock.require_write_context():
                yield
        else:
            with self.__lock.write_context():
                yield

    @contextmanager
    def read_context(self, snapshot=None):
        # type: (Optional[Snapshot]) -> Iterator
        with self._AbstractObject__read_context(snapshot=snapshot):
            yield

    @contextmanager
    def write_context(self, temporary=False):
        # type: (bool) -> Iterator
        with self._AbstractObject__write_context():
            yield
            if temporary:
                raise RevertException()

    @property
    def _subject(self):
        # type: () -> Subject[Application]
        return self.__subject


def resolve_history(
    obj,  # type: AbstractObject
    storage,  # type: AbstractStorage[Pointer[AbstractObject], Store]
):
    # type: (...) -> Optional[AbstractHistoryObject]
    store = storage.query(obj.pointer)
    if store.history is not None:
        return store.history

    history_provider_ref = store.history_provider_ref
    if history_provider_ref is None:
        history_provider = None
    else:
        history_provider = history_provider_ref()

    while history_provider is not None:
        store = storage.query(history_provider.pointer)
        if store.history is not None:
            return store.history

        history_provider_ref = store.history_provider_ref
        if history_provider_ref is None:
            history_provider = None
        else:
            history_provider = history_provider_ref()

    return None
