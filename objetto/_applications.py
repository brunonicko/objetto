# -*- coding: utf-8 -*-
"""Manages multiple objects under different contexts."""

from collections import Counter as ValueCounter
from contextlib import contextmanager
from copy import deepcopy
from enum import Enum, unique
from threading import RLock
from traceback import format_exception
from typing import TYPE_CHECKING, cast
from weakref import WeakKeyDictionary

from six import iteritems, string_types

from ._bases import Base, final
from ._changes import BaseChange
from ._data import BaseData, DataAttribute, InteractiveDictData
from ._states import BaseState
from .data import (
    Data,
    data_attribute,
    data_dict_attribute,
    data_list_attribute,
    data_set_attribute,
)
from .utils.reraise_context import ReraiseContext
from .utils.subject_observer import Subject
from .utils.type_checking import assert_is_callable, assert_is_instance
from .utils.weak_reference import WeakReference

if TYPE_CHECKING:
    from typing import (
        Any,
        AbstractSet,
        Callable,
        Counter,
        Dict,
        Iterator,
        List,
        Mapping,
        Optional,
        Set,
        Tuple,
        Type,
        Union,
    )

    from ._changes import BaseAtomicChange, Batch
    from ._data import InteractiveListData, InteractiveSetData
    from ._history import HistoryObject
    from ._objects import BaseObject, Relationship
    from .utils.subject_observer import ObserverExceptionInfo

    assert Relationship

    ReadFunction = Callable[[], "Store"]
    WriteFunction = Callable[
        [Any, BaseData, Mapping[str, Any], Counter[BaseObject], BaseAtomicChange], None
    ]

    ReadMetadataFunction = Callable[[], InteractiveDictData]
    UpdateMetadataFunction = Callable[[Mapping[str, Any]], None]

__all__ = ["Phase", "Action", "Store", "Application"]


@unique
class Phase(Enum):
    """Action phase."""

    PRE = "PRE"
    """Before the changes."""

    POST = "POST"
    """After the changes."""


class ObserversFailedError(Exception):
    """
    Observers fail to receive payload.

    :param exception_infos: Observer exception infos.
    """

    def __init__(self, message, exception_infos):
        # type: (str, Tuple[ObserverExceptionInfo, ...]) -> None
        message = (
            (
                message
                + ":\n\n"
                + "\n".join(
                    (
                        "{}\n".format(exception_info.observer)
                        + "".join(
                            format_exception(
                                exception_info.exception_type,
                                exception_info.exception,
                                exception_info.traceback,
                            )
                        )
                    )
                    for exception_info in exception_infos
                )
            )
            if exception_infos
            else message
        )
        super(ObserversFailedError, self).__init__(message)
        self.__exception_infos = exception_infos

    @property
    def exception_infos(self):
        # type: () -> Tuple[ObserverExceptionInfo, ...]
        """Observer exception infos."""
        return self.__exception_infos


class RejectChangeException(Exception):
    """
    Reject change exception.

    :param change: Change to reject.
    :param callback: Callback to run after change is rewound.
    """

    def __init__(self, message, change, callback):
        # type: (str, BaseChange, Callable[[], None]) -> None
        from ._changes import BaseChange

        with ReraiseContext(TypeError, "'change' parameter"):
            assert_is_instance(change, BaseChange)

        with ReraiseContext(TypeError, "'callback' parameter"):
            assert_is_callable(callback)

        message = (
            "{}; change {} was rejected but callback could not run because rejection "
            "was not raised and/or caught within the correct context"
        ).format(message, change)
        super(RejectChangeException, self).__init__(message)
        self.__change = change
        self.__callback = callback

    @property
    def change(self):
        # type: () -> BaseChange
        """Change to reject."""
        return self.__change

    @property
    def callback(self):
        # type: () -> Callable[[], None]
        """Callback to run after change is rewound."""
        return self.__callback


class TemporaryContextException(Exception):
    """Temporary write context exception."""


class ApplicationLock(Base):
    """
    Re-entrant threading lock for thread-safe applications.

      - Can be deep copied and pickled.
    """

    __slots__ = ("__lock",)

    def __init__(self):
        # type: () -> None
        self.__lock = RLock()

    def __deepcopy__(self, memo=None):
        # type: (Optional[Dict[int, Any]]) -> ApplicationLock
        """
        Make a deep copy.

        :param memo: Memo dict.
        :return: Deep copy.
        """
        if memo is None:
            memo = {}
        try:
            deep_copy = memo[id(self)]
        except KeyError:
            deep_copy = memo[id(self)] = type(self)()
        return deep_copy

    def __enter__(self):
        """Enter lock context."""
        return self.__lock.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit lock context."""
        return self.__lock.__exit__(exc_type, exc_val, exc_tb)

    def __reduce__(self):
        # type: () -> Tuple[Type[ApplicationLock], Tuple]
        """
        Reduce for pickling.

        :return: Class and init arguments.
        """
        return type(self), ()


class ApplicationStorage(WeakKeyDictionary):
    """
    Application storage.

      - Holds a store for each object in the application.
      - Can be deep copied and pickled.
    """

    def __deepcopy__(self, memo=None):
        # type: (Optional[Dict[int, Any]]) -> ApplicationStorage
        """
        Make a deep copy.

        :param memo: Memo dict.
        :return: Deep copy.
        """
        if memo is None:
            memo = {}
        try:
            deep_copy = memo[id(self)]
        except KeyError:
            deep_copy = memo[id(self)] = type(self)()
            deep_copy_args = dict(self), memo
            deep_copy.update(deepcopy(*deep_copy_args))
        return deep_copy

    def __reduce__(self):
        # type: () -> Tuple[Type[ApplicationStorage], Tuple[Dict[BaseObject, Store]]]
        """
        Reduce for pickling.

        :return: Class and init arguments.
        """
        return type(self), (dict(self),)


class Store(Data):
    """Holds an object's state, data, metadata, hierarchy, and history information."""

    state = data_attribute(
        BaseState, subtypes=True, checked=False
    )  # type: DataAttribute[BaseState]
    """State."""

    data = data_attribute(
        (BaseData, type(None)), subtypes=True, checked=False
    )  # type: DataAttribute[Optional[BaseData]]
    """Data."""

    metadata = data_dict_attribute(
        key_types=string_types, checked=False
    )  # type: DataAttribute[InteractiveDictData[str, Any]]
    """Metadata."""

    parent_ref = data_attribute(
        cast("Type[WeakReference[BaseObject]]", WeakReference),
        checked=False,
        default=WeakReference(),
    )  # type: DataAttribute[WeakReference[BaseObject]]
    """Weak reference to the parent."""

    history_provider_ref = data_attribute(
        cast("Type[WeakReference[BaseObject]]", WeakReference),
        checked=False,
        default=WeakReference(),
    )  # type: DataAttribute[WeakReference[BaseObject]]
    """Weak reference to the history provider."""

    last_parent_history_ref = data_attribute(
        cast("Type[WeakReference[HistoryObject]]", WeakReference),
        checked=False,
        default=WeakReference(),
    )  # type: DataAttribute[WeakReference[HistoryObject]]
    """Weak reference to the last history object."""

    history = data_attribute(
        (".._history|HistoryObject", type(None)), checked=False, default=None
    )  # type: DataAttribute[HistoryObject]
    """History object."""

    children = data_set_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False
    )  # type: DataAttribute[InteractiveSetData[BaseObject]]
    """Children."""


@final
class Action(Data):
    """Carries information about a change and where it happened in the hierarchy."""

    sender = data_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False
    )  # type: DataAttribute[BaseObject]
    """Object where the action originated from (where the change happened)."""

    receiver = data_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False
    )  # type: DataAttribute[BaseObject]
    """Object relaying the action up the hierarchy."""

    locations = data_list_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveListData[Any]]
    """List of relative locations from the receiver to the sender."""

    change = data_attribute(
        BaseChange, subtypes=True, checked=False
    )  # type: DataAttribute[BaseChange]
    """Change that happened in the sender."""


class Commit(Data):
    """Holds unmerged, modified stores."""

    actions = data_list_attribute(
        Action, checked=False
    )  # type: DataAttribute[InteractiveListData[Action]]
    """Actions."""

    stores = data_dict_attribute(
        Store, checked=False, key_types=".._objects|BaseObject", key_subtypes=True
    )  # type: DataAttribute[InteractiveDictData[BaseObject, Store]]
    """Modified stores."""


class BatchCommit(Commit):
    """Batch commit."""

    phase = data_attribute(Phase, checked=False)  # type: DataAttribute[Phase]
    """Batch phase."""


class ApplicationInternals(Base):
    """Internals for :class:`Application`."""

    __slots__ = (
        "__app_ref",
        "__history_cls",
        "__lock",
        "__storage",
        "__busy_writing",
        "__busy_hierarchy",
        "__commits",
        "__reading",
        "__writing",
        "__subject",
    )

    def __init__(self, app):
        # type: (Application) -> None
        self.__app_ref = WeakReference(app)
        self.__history_cls = None  # type: Optional[Type[HistoryObject]]
        self.__lock = ApplicationLock()
        self.__storage = ApplicationStorage()
        self.__busy_writing = set()  # type: Set[BaseObject]
        self.__busy_hierarchy = ValueCounter()  # type: Counter[BaseObject]
        self.__commits = []  # type: List[Commit]
        self.__reading = []  # type: List[Optional[BaseObject]]
        self.__writing = []  # type: List[Optional[BaseObject]]
        self.__subject = Subject()

    def __deepcopy__(self, memo=None):
        # type: (Optional[Dict[int, Any]]) -> ApplicationInternals
        """
        Deep copy.

        :param memo: Memo dict.
        :return: Deep copy.
        :raises RuntimeError: Can't deep copy while application is in a 'write' context.
        """
        if memo is None:
            memo = {}
        with self.read_context():
            if self.__writing:
                error = "can't deep copy while application is in a 'write' context"
                raise RuntimeError(error)
            try:
                deep_copy = memo[id(self)]
            except KeyError:
                cls = type(self)
                deep_copy = memo[id(self)] = cls.__new__(cls)
                deep_copy_state_args = self.__getstate__(), memo
                deep_copy_state = deepcopy(*deep_copy_state_args)
                deep_copy.__setstate__(deep_copy_state)
            return deep_copy

    def __getstate__(self):
        # type: () -> Dict[str, Any]
        """
        Get state for pickling.

        :return: State.
        :raises RuntimeError: Can't pickle while application is in a 'write' context.
        """
        with self.read_context():
            if self.__writing:
                error = "can't pickle while application is in a 'write' context"
                raise RuntimeError(error)
            return super(ApplicationInternals, self).__getstate__()

    def __read(self, obj):
        # type: (BaseObject) -> Store
        """
        Get current store for an object.

        :param obj: Object.
        :return: Store.
        """
        if self.__writing:
            try:
                return self.__commits[-1].stores[obj]
            except (IndexError, KeyError):
                pass
        try:
            return self.__storage[obj]
        except KeyError:
            error = "object {} is no longer valid".format(obj)
            raise RuntimeError(error)

    def __read_history(
        self,
        obj,  # type: BaseObject
    ):
        # type: (...) -> Union[Tuple[HistoryObject, BaseObject], Tuple[None, None]]
        """
        Get current history for an object.

        :param obj: Object.
        :return: History object and history provider or (None, None).
        """
        store = self.__read(obj)
        if store.history is not None:
            return store.history, obj
        provider = store.history_provider_ref()
        if provider is not None:
            return self.__read_history(provider)
        return None, None

    def __pre_parent_check(
        self,
        obj,  # type: BaseObject
        hierarchy,  # type: List[BaseObject]
        child_counter,  # type: Counter[BaseObject]
    ):
        # type: (...) -> None
        """
        Run checks before performing parenting/unparenting.

        :param obj: Object adopting/releasing children.
        :param hierarchy: Cached hierarchy.
        :param child_counter: Child object counter.
        :raises ValueError: Can't have history objects as children of other objects.
        :raises ValueError: Can't change parent while object's hierarchy is locked.
        :raises ValueError: Can't change parent while object is initializing.
        :raises ValueError: Object is already parented.
        :raises ValueError: Parent cycle detected.
        :raises ValueError: Object is not a child.
        :raises ValueError: Can't parent more than once.
        :raises ValueError: Can't unparent more than once.
        """
        if not child_counter:
            return
        children = None
        for child, count in iteritems(child_counter):
            if count:
                if self.__history_cls is not None:
                    if isinstance(child, self.__history_cls):
                        error = (
                            "can't have '{}' objects as children of other objects"
                        ).format(self.__history_cls.__fullname__)
                        raise ValueError(error)
                if self.__busy_hierarchy.get(child):
                    error = (
                        "can't change parent for {} while its hierarchy is locked"
                    ).format(child)
                    raise ValueError(error)
                if child._initializing:
                    error = (
                        "can't change parent for {} while running it's '__init__'"
                    ).format(child)
                    raise ValueError(error)
            if count == 1:
                child_parent = self.__read(child).parent_ref()
                if child_parent is not None:
                    error = (
                        "{} is already parented to {}, can't parent it to {}"
                    ).format(child, child_parent, obj)
                    raise ValueError(error)
                for parent in hierarchy:
                    if parent is child:
                        error = "parent cycle between {} and {}".format(child, obj)
                        raise ValueError(error)
            elif count == -1:
                if children is None:
                    children = self.__read(obj).children
                if child not in children:
                    error = "{} is not a child of {}".format(child, obj)
                    raise ValueError(error)
            elif count > 1:
                error = "{} can't be parented to {} more than once".format(child, obj)
                raise ValueError(error)
            elif count < -1:
                error = "{} can't be un-parented from {} more than once".format(
                    child, obj
                )
                raise ValueError(error)

    def __write(
        self,
        obj,  # type: BaseObject
        state,  # type: BaseState
        data,  # type: Optional[BaseData]
        metadata,  # type: Mapping[str, Any]
        child_counter,  # type: Counter[BaseObject]
        change,  # type: BaseAtomicChange
    ):
        # type: (...) -> None
        """
        Perform a 'write' operation.

        :param obj: Object.
        :param state: New state.
        :param data: New data.
        :param metadata: New metadata.
        :param child_counter: Child counter.
        :param change: Change.
        """

        # Lock hierarchy and cache it.
        with self.__hierarchy_context(obj) as hierarchy:
            assert hierarchy[0] is obj

            # Perform pre-parent check.
            self.__pre_parent_check(obj, hierarchy, child_counter)

            # Lock parenting for new children.
            with self.__new_children_context(change.new_children):

                # Enter history atomic batch if not in a batch.
                history, history_provider = self.__read_history(obj)
                atomic_batch_change = None
                if (
                    history is not None
                    and not obj._initializing
                    and not history.executing
                    and not history.in_batch()
                ):
                    from ._changes import Batch

                    atomic_batch_change = Batch(
                        name=change.name, obj=obj, metadata={"atomic_change": change}
                    )
                    history.__enter_batch__(atomic_batch_change)

                # Pre phase.
                child = None  # type: Optional[BaseObject]
                single_locations = []  # type: List[Any]
                single_data_locations = []  # type: List[Any]
                all_locations = []  # type: List[List[Any]]
                all_data_locations = []  # type: List[List[Any]]
                actions = []  # type: List[Action]
                for i, parent in enumerate(hierarchy):
                    if i == 0:
                        location = None
                        locations = []
                        data_location = None
                        data_locations = []
                    else:
                        assert child is not None
                        location = parent._locate(child)
                        locations = [location] + all_locations[-1]

                        relationship = cast(
                            "Relationship",
                            parent._get_relationship(location)
                        )
                        if relationship.data:
                            data_location = parent._locate_data(child)
                            data_locations = [data_location, all_data_locations[-1]]
                        else:
                            data_location = None
                            data_locations = []

                    single_locations.append(location)
                    all_locations.append(locations)

                    single_data_locations.append(data_location)
                    all_data_locations.append(data_locations)

                    action = Action(
                        sender=obj,
                        receiver=parent,
                        locations=locations,
                        change=change,
                    )
                    assert action.sender is obj
                    assert action.receiver is parent

                    actions.append(action)
                    for reaction in type(action.receiver)._reactions:
                        reaction(action.receiver, action, Phase.PRE)

                    child = parent

                # Flush histories and filter history adopters.
                new_children_last_parent_history_updates = set()
                histories_to_flush = set()
                filtered_history_adopters = set()

                # noinspection PyTypeChecker
                for new_child in change.new_children:
                    new_child_store = self.__read(new_child)
                    last_parent_history = new_child_store.last_parent_history_ref()
                    if last_parent_history is not history:
                        if last_parent_history is not None:
                            histories_to_flush.add(last_parent_history)
                        new_children_last_parent_history_updates.add(new_child)

                # noinspection PyTypeChecker
                for adopter in change.history_adopters:
                    if type(adopter)._history_descriptor is not None:
                        continue
                    filtered_history_adopters.add(adopter)
                    adopter_old_history, _ = self.__read_history(adopter)
                    if adopter_old_history is not history:
                        if adopter_old_history is not None:
                            histories_to_flush.add(adopter_old_history)

                for history_to_flush in histories_to_flush:
                    history_to_flush.flush()

                # Store changes.
                try:
                    stores = self.__commits[-1].stores
                except IndexError:
                    stores = InteractiveDictData()

                store = self.__read(obj)
                old_data = store.data
                store = store.update(
                    {
                        "state": state,
                        "data": data,
                        "metadata": metadata,
                    }
                )

                # Children changes.
                if change.old_children or change.new_children:
                    children = store.children

                    # noinspection PyTypeChecker
                    for old_child in change.old_children:
                        children = children.remove(old_child)
                        child_store = self.__read(old_child).set(
                            "parent_ref", WeakReference()
                        )
                        stores = stores.set(old_child, child_store)

                    # noinspection PyTypeChecker
                    for new_child in change.new_children:
                        children = children.add(new_child)
                        child_store = self.__read(new_child).set(
                            "parent_ref", WeakReference(obj)
                        )
                        if new_child in new_children_last_parent_history_updates:
                            child_store = child_store.set(
                                "last_parent_history_ref", WeakReference(history)
                            )
                        stores = stores.set(new_child, child_store)
                    store = store.set("children", children)
                stores = stores.set(obj, store)

                # History propagation.
                for adopter in filtered_history_adopters:
                    try:
                        adopter_store = stores[adopter]
                    except KeyError:
                        adopter_store = self.__read(adopter)
                    adopter_store = adopter_store.set(
                        "history_provider_ref", WeakReference(obj)
                    )
                    stores = stores.set(adopter, adopter_store)

                # Upstream data changes.
                if data is not old_data:
                    child_data = data
                    child = None
                    for i, parent in enumerate(hierarchy):
                        if i == 0:
                            child = parent
                            continue
                        assert child is not None

                        location = single_locations[i]
                        relationship = cast(
                            "Relationship",
                            parent._get_relationship(location)
                        )
                        if not relationship.data:
                            break

                        assert data is not None
                        assert child_data is not None

                        data_location = single_data_locations[i]

                        parent_old_store = self.__read(parent)
                        parent_new_store = type(
                            parent
                        ).__functions__.replace_child_data(
                            parent_old_store,
                            child,
                            data_location,
                            child_data,
                        )
                        if parent_new_store is parent_old_store:
                            break
                        stores = stores.set(parent, parent_new_store)

                        child = parent
                        child_data = parent_new_store.data

                # Commit!
                commit = Commit(actions=actions, stores=stores)
                self.__commits.append(commit)

                # Push change to history.
                if (
                    history is not None
                    and history_provider is not None
                    and not obj._initializing
                    and not history_provider._initializing
                ):
                    history.__push_change__(change)

                # Post phase.
                for action in actions:
                    for reaction in type(action.receiver)._reactions:
                        reaction(action.receiver, action, Phase.POST)

                # Exit history atomic batch.
                if history is not None and atomic_batch_change is not None:
                    history.__exit_batch__(atomic_batch_change)

    def __update_metadata(
        self,
        obj,  # type: BaseObject
        update,  # type: Mapping[str, Any]
    ):
        # type: (...) -> None
        """
        Update metadata.

        :param obj: Object.
        :param update: Metadata update.
        """
        # Store changes.
        try:
            stores = self.__commits[-1].stores
        except IndexError:
            stores = InteractiveDictData()
        store = self.__read(obj)
        old_metadata = store.metadata
        store = store.update({"metadata": old_metadata.update(update)})
        stores = stores.set(obj, store)

        # Commit!
        commit = Commit(actions=(), stores=stores)
        self.__commits.append(commit)

    def __revert(self, index):
        # type: (int) -> None
        """
        Revert changes to a particular index.

        :param index: Index.
        """
        del self.__commits[index:]

    def __push(self):
        # type: () -> None
        """Push and merge changes to permanent storage."""
        if self.__commits:
            commits = self.__commits
            self.__commits = []

            exception_infos = []  # type: List[ObserverExceptionInfo]
            for commit in commits:
                if type(commit) is BatchCommit:
                    for action in commit.actions:
                        phase = commit.phase  # type: ignore
                        exception_infos.extend(
                            action.receiver.__.subject.send(
                                action, cast("Phase", phase)
                            )
                        )
                else:
                    for action in commit.actions:
                        exception_infos.extend(
                            action.receiver.__.subject.send(action, Phase.PRE)
                        )

                    self.__storage.update(commit.stores)

                    for action in commit.actions:
                        exception_infos.extend(
                            action.receiver.__.subject.send(action, Phase.POST)
                        )

            if exception_infos:
                raise ObserversFailedError(
                    "external observers raised exceptions", tuple(exception_infos)
                )

    @contextmanager
    def __hierarchy_context(self, obj):
        # type: (BaseObject) -> Iterator[List[BaseObject]]
        """
        Context manager that locks and caches an object's upper hierarchy.

        :param obj: Object.
        :return: Cached upper hierarchy (starting with the object itself).
        """
        hierarchy = []  # type: List[BaseObject]
        parent = obj  # type: Optional[BaseObject]
        while parent is not None:
            self.__busy_hierarchy[parent] += 1
            hierarchy.append(parent)
            parent = self.__read(parent).parent_ref()
        try:
            yield hierarchy
        finally:
            for parent in hierarchy:
                self.__busy_hierarchy[parent] -= 1
                if not self.__busy_hierarchy[parent]:
                    del self.__busy_hierarchy[parent]

    @contextmanager
    def __new_children_context(self, new_children):
        # type: (AbstractSet[BaseObject]) -> Iterator
        """
        Context manager that locks parenting for new children.

        :param new_children: New children.
        """
        for new_child in new_children:
            self.__busy_hierarchy[new_child] += 1
        try:
            yield
        finally:
            for new_child in new_children:
                self.__busy_hierarchy[new_child] -= 1
                if not self.__busy_hierarchy[new_child]:
                    del self.__busy_hierarchy[new_child]

    def init_object(self, obj):
        # type: (BaseObject) -> None
        """
        Initialize object.

        :param obj: Object.
        """
        with self.write_context():
            try:
                stores = self.__commits[-1].stores
            except IndexError:
                stores = InteractiveDictData()

            if obj in stores or obj in self.__storage:
                error = "object {} can't be initialized more than once".format(obj)
                raise RuntimeError(error)

            cls = type(obj)  # type: Type[BaseObject]
            kwargs = {}  # type: Dict[str, Any]

            # History object.
            history_descriptor = cls._history_descriptor
            if history_descriptor is not None:
                app = self.__app_ref()
                assert app is not None

                if self.__history_cls is None:
                    from ._history import HistoryObject

                    self.__history_cls = HistoryObject

                kwargs.update(
                    history_provider_ref=WeakReference(obj),
                    history=self.__history_cls(app, size=history_descriptor.size),
                )

            # State.
            state = cls._state_factory()

            # Data.
            data_type = cls.Data
            if data_type is not None:
                data = data_type.__make__()  # type: ignore
            else:
                data = None

            # Commit!
            stores = stores.set(obj, Store(state=state, data=data, **kwargs))
            commit = Commit(stores=stores)
            self.__commits.append(commit)

    @contextmanager
    def read_context(self, obj=None):
        # type: (Optional[BaseObject]) -> Iterator[ReadFunction]
        """
        Read context manager.

        :param obj: Object.
        :return: Read handle function.
        """
        with self.__lock:
            topmost = not self.__reading
            self.__reading.append(obj)

            def read():
                # type: () -> Store
                assert obj is not None
                return self.__read(obj)

            try:
                yield read
            finally:
                self.__reading.pop()
                if topmost:
                    assert not self.__reading

    @contextmanager
    def write_context(
        self,
        obj=None,  # type: Optional[BaseObject]
    ):
        # type: (...) -> Iterator[Tuple[ReadFunction, WriteFunction]]
        """
        Write context manager.

        :param obj: Object.
        :return: Read and write handle functions.
        """
        with self.__lock:
            if self.__reading:
                error = "can't enter a 'write' context while in a 'read' context"
                raise RuntimeError(error)
            topmost = not self.__writing
            index = len(self.__commits)
            self.__writing.append(obj)

            def read():
                # type: () -> Store
                assert obj is not None
                return self.__read(obj)

            def write(
                state,  # type: Any
                data,  # type: BaseData
                metadata,  # type: Mapping[str, Any]
                child_counter,  # type: Counter[BaseObject]
                change,  # type: BaseAtomicChange
            ):
                # type: (...) -> None
                assert obj is not None
                if obj in self.__busy_writing:
                    error_ = "reaction cycle detected on {}".format(obj)
                    raise RuntimeError(error_)
                self.__busy_writing.add(obj)
                try:
                    self.__write(obj, state, data, metadata, child_counter, change)
                except RejectChangeException as e_:
                    self.__busy_writing.remove(obj)
                    if e_.change is not change:
                        raise
                    self.__revert(index)
                    e_.callback()
                except Exception:
                    self.__busy_writing.remove(obj)
                    raise
                else:
                    self.__busy_writing.remove(obj)

            try:
                yield read, write
            except Exception as e:
                self.__revert(index)
                if not topmost or type(e) is not TemporaryContextException:
                    raise
            else:
                if topmost:
                    with self.read_context():
                        self.__push()
            finally:
                self.__writing.pop()
                if topmost:
                    assert not self.__busy_hierarchy
                    assert not self.__busy_writing
                    assert not self.__commits
                    assert not self.__writing

    @contextmanager
    def update_metadata_context(
        self,
        obj,  # type: BaseObject
    ):
        # type: (...) -> Iterator[Tuple[ReadMetadataFunction, UpdateMetadataFunction]]
        """
        Update metadata context manager.

        :param obj: Object.
        :return: Read metadata and write metadata handle functions.
        """
        with self.write_context():

            def read_metadata():
                # type: () -> InteractiveDictData
                return self.__read(obj).metadata

            def update_metadata(
                update,  # type: Mapping[str, Any]
            ):
                # type: (...) -> None
                self.__update_metadata(obj, update)

            yield read_metadata, update_metadata

    @contextmanager
    def batch_context(self, obj, change):
        # type: (BaseObject, Batch) -> Iterator
        """
        Batch change context.

        :param obj: Object.
        :param change: Batch change.
        """
        with self.write_context():
            index = len(self.__commits)

            def _get_stores():
                try:
                    return self.__commits[-1].stores
                except IndexError:
                    return {}

            try:
                with self.__hierarchy_context(obj) as hierarchy:
                    assert hierarchy[0] is obj

                    # Get history.
                    history, history_provider = self.__read_history(obj)

                    # Gather actions.
                    child = None  # type: Optional[BaseObject]
                    single_locations = []  # type: List[Any]
                    all_locations = []  # type: List[List[Any]]
                    actions = []  # type: List[Action]
                    for i, parent in enumerate(hierarchy):
                        if i == 0:
                            location = None
                            locations = []
                        else:
                            assert child is not None
                            location = parent._locate(child)
                            locations = [location] + all_locations[-1]

                        single_locations.append(location)
                        all_locations.append(locations)

                        action = Action(
                            sender=obj,
                            receiver=parent,
                            locations=locations,
                            change=change,
                        )
                        assert action.sender is obj
                        assert action.receiver is parent

                        actions.append(action)
                        child = parent

                    # Commit Pre.
                    pre_commit = BatchCommit(
                        actions=actions, stores=_get_stores(), phase=Phase.PRE
                    )
                    self.__commits.append(pre_commit)

                    # History Pre.
                    if (
                        history is not None
                        and history_provider is not None
                        and not obj._initializing
                        and not history_provider._initializing
                    ):
                        history.__enter_batch__(change)

                    # Pre.
                    for action in actions:
                        for reaction in type(action.receiver)._reactions:
                            reaction(action.receiver, action, Phase.PRE)

                    yield change

                    # History Post.
                    if (
                        history is not None
                        and history_provider is not None
                        and not obj._initializing
                        and not history_provider._initializing
                    ):
                        history.__exit_batch__(change)

                    # Post.
                    for action in actions:
                        for reaction in type(action.receiver)._reactions:
                            reaction(action.receiver, action, Phase.POST)

                    # Commit Post.
                    post_commit = BatchCommit(
                        actions=actions, stores=_get_stores(), phase=Phase.POST
                    )
                    self.__commits.append(post_commit)

            # Catch rejection.
            except RejectChangeException as e:
                self.__revert(index)
                if e.change is not change:
                    raise
                e.callback()


class Application(Base):
    """
    Application.

      - Manages multiple objects under the same hierarchy.
      - Offers contexts for reading/writing/batch.
      - Reverts changes when an error occurs.
      - Manages action propagation, internally and externally.
    """

    __slots__ = ("__weakref__", "__")

    def __init__(self):
        self.__ = ApplicationInternals(self)

    @final
    @contextmanager
    def read_context(self):
        # type: () -> Iterator
        """Read context."""
        with self.__.read_context():
            yield

    @final
    @contextmanager
    def write_context(self):
        # type: () -> Iterator
        """Write context."""
        with self.__.write_context():
            yield

    @final
    @contextmanager
    def temporary_context(self):
        # type: () -> Iterator
        """Temporary write context."""
        with self.__.write_context():
            try:
                yield
            except Exception:
                raise
            else:
                raise TemporaryContextException()
