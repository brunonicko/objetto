# -*- coding: utf-8 -*-

from collections import Counter as ColCounter
from weakref import WeakKeyDictionary
from contextlib import contextmanager
from threading import RLock
from typing import TYPE_CHECKING, NamedTuple

from slotted import Slotted
from six import raise_from, iteritems

from ._bases import INITIALIZING_TAG, Base
from ._data.base import BaseData
from .utils.immutable import ImmutableDict, ImmutableList, ImmutableSet
from .utils.weak_reference import WeakReference
from .utils.dummy_context import DummyContext

if TYPE_CHECKING:
    from typing import (
        Any, Counter, MutableMapping, Mapping, Iterator, ContextManager, Set, Tuple,
        Optional, Union, AbstractSet, List
    )

    from ._objects.base import BaseObject
    from ._objects.history import History

    # assert (
    #     Any,
    #     ImmutableDict,
    #     ImmutableList,
    #     ImmutableSet,
    #     BaseData,
    #     Optional,
    # )

__all__ = ["Application"]


class Action(
    NamedTuple(
        "Action", (
            ("sender", "BaseObject"),
            ("receiver", "BaseObject"),
            ("locations", "Tuple"),
            ("change", "BaseChange"),
        )
    )
):
    """Holds information about a change and where it happened in the hierarchy."""


class Storage(
    NamedTuple(
        "Storage", (
            ("state", "Any"),
            ("data", "Optional[BaseData]"),
            ("metadata", "ImmutableDict[str, Any]"),
            ("children", "ImmutableSet[BaseObject]"),
            ("parent_ref", "WeakReference[Optional[BaseObject]]"),
            ("history_provider_ref", "WeakReference[Optional[BaseObject]]"),
            ("last_parent_history_ref", "WeakReference[Optional[BaseObject]]"),
            ("history", "Optional[History]"),
        )
    )
):
    """Holds an object's state, data, metadata, hierarchy, and history information."""


_INITIAL_STORAGE = Storage(
    state=None,
    data=None,
    metadata=ImmutableDict(),
    children=ImmutableSet(),
    parent_ref=WeakReference(),
    history_provider_ref=WeakReference(),
    last_parent_history_ref=WeakReference(),
    history=None,
)


class Store(object):
    """Holds storages for all objects within an application."""

    __slots__ = ("__history_cls", "__storages")

    def __init__(self):
        self.__history_cls = None
        self.__storages = WeakKeyDictionary(
            {}
        )  # type: MutableMapping[BaseObject, Storage]

    def init(self, obj):
        # type: (BaseObject) -> None

        # Init state and data.
        obj_cls = type(obj)
        state = obj_cls._state_factory()
        data_type = obj_cls.Data
        if data_type is not None:
            data = data_type.__make__()
        else:
            data = None

        # Init history if object has descriptor.
        kwargs = {}
        history_descriptor = obj_cls._history_descriptor
        if history_descriptor is not None:
            if self.__history_cls is None:
                from ._objects.history import History

                self.__history_cls = History
            kwargs.update(
                history_provider_ref=WeakReference(obj),
                history=self.__history_cls(obj.app, size=history_descriptor.size),
            )

        self.__storages[obj] = _INITIAL_STORAGE._replace(
            state=state,
            data=data,
            **kwargs
        )

    def merge(self, commit):
        # type: (Commit) -> None
        self.__storages.update(commit.storages)

    def read(self, obj):
        # type: (BaseObject) -> Storage
        return self.__storages[obj]


class ActionContextResult(
    NamedTuple(
        "ActionContextResult", (
            ("hierarchy", "Tuple[BaseObject, ...]"),
            ("actions", "Tuple[Action, ...]"),
            ("locations", "Tuple"),
        )
    )
):
    """Result of action context."""


class Commit(
    NamedTuple(
        "Commit", (
            ("store", "Store"),
            ("storages", "ImmutableDict[BaseObject, Storage]"),
            ("actions", "Tuple[Action, ...]"),
        )
    )
):
    """Holds unmerged changes to objects' storages."""

    def read(self, obj):
        # type: (BaseObject) -> Storage
        try:
            storage = self.storages[obj]
        except KeyError:
            storage = self.store.read(obj)
        return storage


class ApplicationInternals(Base):
    __slots__ = (
        "__app_ref",
        "__thread_safe",
        "__lock",
        "__store",
        "__commits",
        "__reading",
        "__writing",
        "__writing_objs",
        "__hierarcy_locked_objs",
    )

    def __init__(self, app, thread_safe=False):
        # type: (Application, bool) -> None
        self.__app_ref = WeakReference(app)
        self.__thread_safe = bool(thread_safe)
        self.__lock = RLock() if thread_safe else DummyContext()  # type: ContextManager
        self.__store = Store()
        self.__commits = []  # type: List[Commit]
        self.__reading = False
        self.__writing = False
        self.__writing_objs = set()  # type: Set[BaseObject]
        self.__hierarcy_locked_objs = ColCounter()  # type: Counter[BaseObject]

    def __read(self, obj):
        # type: (BaseObject) -> Storage
        try:
            commit = self.__commits[-1]
        except IndexError:
            return self.__store.read(obj)
        else:
            return commit.read(obj)

    def __read_history(self, obj):
        # type: (BaseObject) -> Optional[History]
        storage = self.__read(obj)
        if storage.history is not None:
            return storage.history
        provider = storage.history_provider_ref()
        if provider is not None:
            return self.__read_history(provider)
        return None

    def __write(
        self,
        obj,  # type: BaseObject
        state,  # type: Any
        data,  # type: Optional[BaseData]
        metadata,  # type: ImmutableDict[str, Any]
        child_counter,  # type: Counter[BaseObject]
        change,  # type: BaseChange
        reach,  # type: Optional[int]
    ):
        # type: (...) -> None
        if obj in self.__writing_objs:
            error = "reaction cycle detected on {}".format(obj)
            raise RuntimeError(error)
        self.__writing_objs.add(obj)
        try:
            with self.__action_context(obj, change, reach) as (
                hierarchy, actions, locations
            ):
                self.__pre_parent_check(obj, hierarchy, child_counter)
                with self.__new_children_context(change.new_children):

                    # Send PRE actions.
                    for action in actions:
                        for reaction in type(action.receiver)._reactions:
                            getattr(type(action.receiver), reaction)(
                                action.receiver, action, "PRE"
                            )

                    # Flush histories and filter history adopters.
                    history = self.__read_history(obj)
                    new_children_last_parent_history_updates = set()
                    histories_to_flush = set()
                    filtered_history_adopters = set()
                    for new_child in change.new_children:
                        last_parent_history = self.__read(
                            new_child
                        ).last_parent_history_ref()
                        if last_parent_history is not history:
                            if last_parent_history is not None:
                                histories_to_flush.add(last_parent_history)
                            new_children_last_parent_history_updates.add(
                                new_child
                            )
                    for adopter in change.history_adopters:
                        if type(adopter)._history_descriptor is not None:
                            continue
                        filtered_history_adopters.add(adopter)
                        adopter_old_history = self.__read_history(adopter)
                        if adopter_old_history is not history:
                            if adopter_old_history is not None:
                                histories_to_flush.add(adopter_old_history)
                    for history_to_flush in histories_to_flush:
                        history_to_flush.flush()

                    # Compute updates to the storages.
                    try:
                        storages = self.__commits[-1].storages
                    except IndexError:
                        storages = ImmutableDict(
                            {}
                        )  # type: ImmutableDict[BaseObject, Storage]
                    storages_update = {}
                    obj_storage = self.__read(obj)
                    obj_storage_update = {
                        "state": state,
                        "data": data,
                        "metadata": metadata,
                    }
                    storages_update[obj] = obj_storage_update

                    # Children updates.
                    if change.old_children or change.new_children:
                        children = obj_storage.children
                        for old_child in change.old_children:
                            children = children.remove(old_child)
                            child_storage = self.__read(old_child)._replace(
                                parent_ref=WeakReference(),
                            )
                            storages_update[old_child] = child_storage
                        for new_child in change.new_children:
                            children = children.add(new_child)
                            child_storage = self.__read(new_child)._replace(
                                parent_ref=WeakReference(obj),
                            )
                            if new_child in new_children_last_parent_history_updates:
                                child_storage = child_storage._replace(
                                    last_parent_history_ref=WeakReference(history),
                                )
                            storages_update[new_child] = child_storage
                        obj_storage_update["children"] = children

                    # History propagation.
                    for adopter in filtered_history_adopters:
                        try:
                            adopter_storage = storages[adopter]
                        except KeyError:
                            adopter_storage = self.__read(adopter)
                        adopter_storage = adopter_storage._replace(
                            history_provider_ref=WeakReference(obj)
                        )
                        storages_update[adopter] = adopter_storage

                    # Upstream data changes.
                    if data is not obj_storage.data:
                        child_data = data
                        child = None
                        for location, parent in zip((None,) + locations, hierarchy):
                            if child is None:
                                child = parent
                                continue

                            relationship = parent._get_relationship(location)
                            if not relationship.data:
                                break

                            parent_storage = self.__read(parent)
                            parent_data_type = type(parent).Data
                            assert parent_data_type is not None

                            parent_data = parent_storage.data
                            parent_new_data = type(
                                parent
                            ).__functions__.replace_child_data(
                                parent_data,
                                child_data,
                                location,
                                relationship.data_relationship,
                            )
                            if parent_new_data is parent_data:
                                break

                            storages_update[parent] = parent_storage._replace(
                                data=parent_new_data
                            )

                            child = parent
                            child_data = parent_new_data

                    # Commit changes.
                    commit = Commit(
                        store=self.__store,
                        storages=storages.update(storages_update),
                        actions=actions,
                    )
                    self.__commits.append(commit)

                    # Add to history.
                    if history is not None and not getattr(obj, INITIALIZING_TAG):
                        history.__push_change__(change)

                    # Send POST actions.
                    for action in actions:
                        for reaction in type(action.receiver)._reactions:
                            getattr(type(action.receiver), reaction)(
                                action.receiver, action, "POST"
                            )
        finally:
            self.__writing_objs.remove(obj)

    def __merge(self):
        # type: () -> None
        if self.__commits:
            commits, self.__commits = self.__commits, []

            exception_infos = []  # type: List[ObserverExceptionInfo]
            for commit in commits:
                if isinstance(commit, _BatchCommit):
                    for action in commit.actions:
                        exception_infos.extend(
                            action.receiver.__.subject.send(action, commit.phase)
                        )
                else:
                    for action in commit.actions:
                        exception_infos.extend(
                            action.receiver.__.subject.send(action, Phase.PRE)
                        )

                    self.__store.merge(commit)

                    for action in commit.actions:
                        exception_infos.extend(
                            action.receiver.__.subject.send(action, Phase.POST)
                        )

            if exception_infos:
                raise ListenersFailedError(tuple(exception_infos))

    def __pre_parent_check(
        self,
        obj,  # type: BaseObject
        hierarchy,  # type: Tuple[BaseObject, ...]
        child_counter,  # type: Counter[BaseObject]
    ):
        # type: (...) -> None
        if not child_counter:
            return
        children = None
        for child, count in iteritems(child_counter):
            if count:
                if self.__history_cls is not None:
                    if isinstance(child, self.__history_cls):
                        error = (
                            "can't have '{}' objects as children of other objects"
                        ).format(self.__history_cls.__name__)
                        raise ValueError(error)
                if self.__busy_hierarchy.get(child):
                    error = (
                        "can't change parent for '{}' object while its hierarchy is "
                        "locked"
                    ).format(type(child).__name__)
                    raise ValueError(error)
                if getattr(child, INITIALIZING_TAG):
                    error = (
                        "can't change parent for '{}' object during its initialization"
                    ).format(type(child).__name__)
                    raise ValueError(error)
            if count == 1:
                child_parent = self.__read(child).parent_ref()
                if child_parent is not None:
                    error = (
                        "'{}' object is already parented to a '{}' object, can't "
                        "parent it to '{}' object"
                    ).format(
                        type(child).__name__,
                        type(child_parent).__name__,
                        type(obj).__name__,
                    )
                    raise ValueError(error)
                for parent in hierarchy:
                    if parent is child:
                        error = (
                            "parent cycle between '{}' object and '{}' object"
                        ).format(type(child).__name__, type(obj).__name__)
                        raise ValueError(error)
            elif count == -1:
                if children is None:
                    children = self.__read(obj).children
                if child not in children:
                    error = "'{}' object is not a child of '{}' object".format(
                        type(child).__name__, type(obj).__name__
                    )
                    raise ValueError(error)
            elif count > 1:
                error = (
                    "'{}' object can't be parented to '{}' object more than once"
                ).format(type(child).__name__, type(obj).__name__)
                raise ValueError(error)
            elif count < -1:
                error = (
                    "'{}' object can't be un-parented from '{}' object more than once"
                ).format(type(child).__name__, type(obj).__name__)
                raise ValueError(error)

    @contextmanager
    def __action_context(
        self,
        obj,  # type: BaseObject
        change,  # type: BaseChange
        reach,  # type: Optional[int]
    ):
        # type: (...) -> Iterator[ActionContextResult]
        if getattr(obj, INITIALIZING_TAG):
            yield ActionContextResult(hierarchy=(), actions=(), locations=())
        else:
            hierarchy = []
            parent = obj
            child = None  # type: Optional[BaseObject]
            locations = []
            actions = []
            reach_count = 0
            while parent is not None:
                if child is not None:
                    locations.append(parent._locate(child))
                if reach is None or reach_count < reach:
                    action = Action(
                        sender=obj,
                        receiver=parent,
                        locations=tuple(locations),
                        change=change,
                    )
                    actions.append(action)
                child = parent
                reach += 1
                self.__hierarcy_locked_objs[parent] += 1
                hierarchy.append(parent)
                parent = self.__read(parent).parent_ref()

            frozen_hierarchy = tuple(hierarchy)
            frozen_actions = tuple(actions)
            frozen_locations = tuple(locations)
            try:
                yield ActionContextResult(
                    hierarchy=frozen_hierarchy,
                    actions=frozen_actions,
                    locations=frozen_locations,
                )
            finally:
                for parent in frozen_hierarchy:
                    self.__hierarcy_locked_objs[parent] -= 1
                    if not self.__hierarcy_locked_objs[parent]:
                        del self.__hierarcy_locked_objs[parent]

    @contextmanager
    def __new_children_context(self, new_children):
        # type: (AbstractSet[BaseObject]) -> Iterator
        for new_child in new_children:
            self.__hierarcy_locked_objs[new_child] += 1
        try:
            yield
        finally:
            for new_child in new_children:
                self.__hierarcy_locked_objs[new_child] -= 1
                if not self.__hierarcy_locked_objs[new_child]:
                    del self.__hierarcy_locked_objs[new_child]

    @contextmanager
    def read_context(self):
        # type: () -> Iterator
        with self.__lock:
            reading, self.__reading = self.__reading, True
            try:
                yield
            except Exception as exc:
                raise_from(exc, None)
            finally:
                self.__reading = reading

    @contextmanager
    def write_context(self):
        # type: () -> Iterator
        with self.__lock:
            if self.__reading:
                error = "can't enter a 'write' context while in a 'read' context"
                raise RuntimeError(error)
            topmost = not self.__writing
            writing, self.__writing = self.__writing, True
            index = len(self.__commits)

            try:
                yield
            except Exception as exc:
                del self.__commits[index:]
                raise_from(exc, None)
            else:
                if topmost:
                    with self.read_context():
                        self.__merge()
            finally:
                self.__writing = writing

    @contextmanager
    def obj_read_context(self, obj):
        # type: (BaseObject) -> Iterator
        with self.read_context():
            active = True

            def read():
                # type: () -> Storage
                if not active:
                    error = "out of context"
                    raise RuntimeError(error)
                return self.__read(obj)

            try:
                yield read
            finally:
                active = False

    @contextmanager
    def obj_write_context(self, obj):
        # type: (BaseObject) -> Iterator
        with self.write_context():
            active = True

            def read():
                # type: () -> Storage
                if not active:
                    error = "out of context"
                    raise RuntimeError(error)
                return self.__read(obj)

            def write(
                state,  # type: Any
                data,  # type: Optional[BaseData]
                metadata,  # type: ImmutableDict[str, Any]
                child_counter,  # type: Counter[BaseObject]
                change,  # type: BaseChange
                reach,  # type: Optional[int]
            ):
                # type: (...) -> None
                if not active:
                    error = "out of context"
                    raise RuntimeError(error)
                self.__write(obj, state, data, metadata, child_counter, change, reach)

            try:
                yield read, write
            finally:
                active = False

    @property
    def thread_safe(self):
        return self.__thread_safe


class Application(Slotted):
    __slots__ = ("__weakref__", "__")

    def __init__(self, thread_safe=False):
        # type: (bool) -> None
        self.__ = ApplicationInternals(self, thread_safe=thread_safe)

    @property
    def thread_safe(self):
        return self.__.thread_safe
