# -*- coding: utf-8 -*-
"""Manages multiple objects under different contexts."""

from collections import Counter as ValueCounter
from contextlib import contextmanager
from copy import deepcopy
from enum import Enum, unique
from inspect import getmro
from threading import RLock
from traceback import format_exception
from typing import TYPE_CHECKING, TypeVar, cast, overload
from weakref import WeakKeyDictionary

from six import iteritems, itervalues, string_types, with_metaclass

from ._bases import Base, BaseMeta, Generic, final
from ._changes import BaseChange
from ._data import BaseData, DataAttribute, InteractiveDictData
from ._exceptions import BaseObjettoException
from ._states import BaseState, DictState
from .data import (
    Data,
    DictData,
    InteractiveData,
    ListData,
    data_attribute,
    data_dict_attribute,
    data_protected_dict_attribute,
    data_protected_list_attribute,
    data_set_attribute,
)
from .utils.custom_repr import custom_mapping_repr
from .utils.recursive_repr import recursive_repr
from .utils.reraise_context import ReraiseContext
from .utils.storage import Storage
from .utils.type_checking import (
    assert_is_callable,
    assert_is_instance,
    assert_is_subclass,
)
from .utils.weak_reference import WeakReference

if TYPE_CHECKING:
    from typing import (
        AbstractSet,
        Any,
        Callable,
        Counter,
        Dict,
        Final,
        Iterator,
        List,
        Mapping,
        MutableMapping,
        Optional,
        Set,
        Tuple,
        Type,
        Union,
    )

    from ._changes import BaseAtomicChange, Batch
    from ._data import InteractiveSetData
    from ._history import HistoryObject
    from ._objects import BaseObject, Relationship
    from ._observers import ActionObserverExceptionData, InternalObserver
    from .utils.subject_observer import ObserverExceptionInfo

    assert Relationship
    assert InternalObserver

    ReadFunction = Callable[[], "Store"]
    WriteFunction = Callable[
        [Any, BaseData, Mapping[str, Any], Counter[BaseObject], BaseAtomicChange], None
    ]

    ReadMetadataFunction = Callable[[], InteractiveDictData]
    UpdateMetadataFunction = Callable[[Mapping[str, Any]], None]

__all__ = [
    "ActionObserversFailedError",
    "RejectChangeException",
    "Phase",
    "Action",
    "Store",
    "BO",
    "ApplicationMeta",
    "Application",
    "ApplicationRoot",
    "ApplicationSnapshot",
]


@unique
class Phase(Enum):
    """Action phase."""

    PRE = "PRE"
    """Before the changes."""

    POST = "POST"
    """After the changes."""


class ActionObserversFailedError(BaseObjettoException):
    """
    Action observers failed while observing action.

    Inherits from:
      - :class:`objetto.bases.BaseObjettoException`

    :param exception_infos: Observer exception infos.
    :type exception_infos: tuple[objetto.observers.ActionObserverExceptionData]
    """

    def __init__(self, message, exception_infos):
        # type: (str, Tuple[ActionObserverExceptionData, ...]) -> None
        message = (
            (
                message
                + "\n\n"
                + "\n".join(
                    (
                        ("Observer: {}\n" "Change: {}\n" "Phase: {}\n").format(
                            exception_info.observer,
                            type(exception_info.action.change).__fullname__,
                            exception_info.phase.name,
                        )
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
        super(ActionObserversFailedError, self).__init__(message)
        self.__exception_infos = exception_infos

    @property
    def exception_infos(self):
        # type: () -> Tuple[ActionObserverExceptionData, ...]
        """
        Observer exception infos.

        :rtype: tuple[objetto.observers.ActionObserverExceptionData]
        """
        return self.__exception_infos


class RejectChangeException(BaseObjettoException):
    """
    Exception to be raised from within a reaction. This will cause the change to be
    reverted and and the custom callback function to run after that.

    Inherits from:
      - :class:`objetto.bases.BaseObjettoException`

    :param change: Change to reject.
    :type change: objetto.bases.BaseChange

    :param callback: Callback to run after change is rewound.
    :type callback: function or collections.abc.Callable
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
        """
        Change to reject.

        :rtype: objetto.bases.BaseChange
        """
        return self.__change

    @property
    def callback(self):
        # type: () -> Callable[[], None]
        """
        Callback to run after change is rewound.

        :rtype: function or collections.abc.Callable
        """
        return self.__callback


class TemporaryContextException(BaseObjettoException):
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


class Store(InteractiveData):
    """Holds an object's state, data, metadata, hierarchy, and history information."""

    state = data_attribute(
        BaseState, subtypes=True, checked=False
    )  # type: DataAttribute[BaseState]
    """State."""

    data = data_attribute(
        (BaseData, None), subtypes=True, checked=False
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
        (".._history|HistoryObject", None), checked=False, default=None
    )  # type: DataAttribute[HistoryObject]
    """History object."""

    children = cast(
        "DataAttribute[InteractiveSetData[BaseObject]]",
        data_set_attribute(".._objects|BaseObject", subtypes=True, checked=False),
    )  # type: DataAttribute[InteractiveSetData[BaseObject]]
    """Children."""


@final
class Action(Data):
    """
    Carries information about a change and where it happened in the hierarchy.

    Inherits from:
      - :class:`objetto.data.Data`
    """

    sender = data_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False
    )  # type: DataAttribute[BaseObject]
    """
    Object where the action originated from (where the change happened).

    :type: objetto.bases.BaseObject
    """

    receiver = data_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False
    )  # type: DataAttribute[BaseObject]
    """
    Object relaying the action up the hierarchy.

    :type: objetto.bases.BaseObject
    """

    locations = data_protected_list_attribute(
        checked=False
    )  # type: DataAttribute[ListData[Any]]
    """
    List of relative locations from the receiver to the sender.

    :type: list[str or int or collections.abc.Hashable]
    """

    change = data_attribute(
        BaseChange, subtypes=True, checked=False
    )  # type: DataAttribute[BaseChange]
    """
    Change that happened in the sender.

    :type: objetto.bases.BaseChange
    """


class Commit(Data):
    """Holds unmerged, modified stores."""

    actions = data_protected_list_attribute(
        Action, checked=False, finalized=True
    )  # type: Final[DataAttribute[ListData[Action]]]
    """Actions."""

    stores = cast(
        "DataAttribute[DictData[BaseObject, Store]]",
        data_protected_dict_attribute(
            Store,
            checked=False,
            key_types=".._objects|BaseObject",
            key_subtypes=True,
        ),
    )  # type: Final[DataAttribute[DictData[BaseObject, Store]]]
    """Modified stores."""


@final
class BatchCommit(Commit):
    """Batch commit."""

    phase = data_attribute(Phase, checked=False)  # type: DataAttribute[Phase]
    """Batch phase."""


# noinspection PyTypeChecker
_AR = TypeVar("_AR", bound="ApplicationRoot")

# noinspection PyTypeChecker
BO = TypeVar("BO", bound="BaseObject")


@final
class ApplicationRoot(Base, Generic[BO]):
    """
    Describes a root object that gets initialized with the application.

    .. note::
        Prefer using the :func:`objetto.applications.root` factory over
        instantiating :class:`objetto.applications.ApplicationRoot` directly.

    :param obj_type: Object type.
    :type obj_type: type[objetto.bases.BaseObject]

    :param priority: Initialization priority.
    :type priority: int or None

    :param kwargs: Keyword arguments to be passed to the object's `__init__`.

    :raises ValueError: Used reserved keyword argument.
    :raises TypeError: Invalid object type.
    """

    __slots__ = ("__obj_type", "__priority", "__kwargs")

    def __init__(self, obj_type, priority=None, **kwargs):
        # type: (Type[BO], Optional[int], Any) -> None

        # Check kwargs for reserved keys.
        if "app" in kwargs:
            error = "can't use reserved keyword argument 'app'"
            raise ValueError(error)

        from ._objects import BaseObject

        with ReraiseContext(TypeError, "'obj_type' parameter"):
            assert_is_subclass(obj_type, BaseObject)
        self.__obj_type = obj_type
        self.__priority = priority
        self.__kwargs = DictState(kwargs)

    @overload
    def __get__(self, instance, owner):
        # type: (_AR, None, Type[Application]) -> _AR
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (Application, Type[Application]) -> BO
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (_AR, object, type) -> _AR
        pass

    def __get__(self, instance, owner):
        """
        Get attribute value when accessing from valid instance or this descriptor
        otherwise.

        :param instance: Instance.
        :type instance: objetto.applications.Application or None

        :param owner: Owner class.
        :type owner: type[objetto.applications.Application]

        :return: Object instance or this descriptor.
        :rtype: objetto.bases.BaseObject or objetto.applications.ApplicationRoot
        """
        if instance is not None and isinstance(instance, Application):
            return instance.__.get_root_obj(self)
        return self

    def __hash__(self):
        # type: () -> int
        """
        Get hash based on object id.

        :return: Hash based on object id.
        :rtype: int
        """
        return hash(id(self))

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare with another object for identity.

        :param other: Another object.

        :return: True if the same object.
        :rtype: bool
        """
        return other is self

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        :rtype: str
        """
        return custom_mapping_repr(
            self.to_dict(),
            prefix="{}(".format(type(self).__name__),
            template="{key}={value}",
            suffix=")",
            key_repr=str,
        )

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[str, Any]
        """
        return {
            "obj_type": self.obj_type,
            "priority": self.priority,
            "kwargs": self.kwargs,
        }

    @property
    def obj_type(self):
        # type: () -> Type[BO]
        """
        Object type.

        :rtype: type[objetto.bases.BaseObject]
        """
        return self.__obj_type

    @property
    def priority(self):
        # type: () -> Optional[int]
        """
        Initialization priority.

        :rtype: int or None
        """
        return self.__priority

    @property
    def kwargs(self):
        # type: () -> DictState[str, Any]
        """Keyword arguments to be passed to object's '__init__'."""
        return self.__kwargs


class ApplicationInternals(Base):
    """Internals for `Application`."""

    __slots__ = (
        "__app_ref",
        "__history_cls",
        "__lock",
        "__storage",
        "__snapshot",
        "__busy_writing",
        "__busy_hierarchy",
        "__commits",
        "__reading",
        "__writing",
        "__roots",
    )

    def __init__(self, app):
        # type: (Application) -> None
        self.__app_ref = WeakReference(app)
        self.__history_cls = None  # type: Optional[Type[HistoryObject]]
        self.__lock = ApplicationLock()
        self.__storage = Storage()  # type: Storage[BaseObject, Store]
        self.__snapshot = None  # type: Optional[ApplicationSnapshot]
        self.__busy_writing = set()  # type: Set[BaseObject]
        self.__busy_hierarchy = ValueCounter()  # type: Counter[BaseObject]
        self.__commits = []  # type: List[Commit]
        self.__reading = []  # type: List[Optional[BaseObject]]
        self.__writing = []  # type: List[Optional[BaseObject]]
        self.__roots = {}  # type: Dict[ApplicationRoot, BaseObject]

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
        if self.__snapshot is not None:
            try:
                return self.__snapshot._storage.query(obj)
            except KeyError:
                error = "object with id {} is not valid in snapshot".format(id(obj))
                raise RuntimeError(error)
        if self.__writing:
            try:
                return self.__commits[-1].stores[obj]
            except (IndexError, KeyError):
                pass
        try:
            return self.__storage.query(obj)
        except KeyError:
            error = "object with id {} is no longer valid".format(id(obj))
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
        :raises ValueError: Can't have root objects as children of other objects.
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
                if child.__.is_root:
                    error = "'{}' object is a root and can't be parented".format(
                        type(child).__fullname__
                    )
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
                        name=change.name,
                        obj=obj,
                        metadata={"atomic_change": change, "is_atomic": True},
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
                            "Relationship", parent._get_relationship(location)
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
                    self.__react(action.receiver, action, Phase.PRE)

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
                        stores = stores._set(old_child, child_store)

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
                        stores = stores._set(new_child, child_store)
                    store = store.set("children", children)
                stores = stores._set(obj, store)

                # History propagation.
                for adopter in filtered_history_adopters:
                    try:
                        adopter_store = stores[adopter]
                    except KeyError:
                        adopter_store = self.__read(adopter)
                    adopter_store = adopter_store.set(
                        "history_provider_ref", WeakReference(obj)
                    )
                    stores = stores._set(adopter, adopter_store)

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
                            "Relationship", parent._get_relationship(location)
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
                        stores = stores._set(parent, parent_new_store)

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
                    self.__react(action.receiver, action, Phase.POST)

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
        stores = stores._set(obj, store)

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

            action_exception_infos = []  # type: List[ActionObserverExceptionData]

            def ingest_action_exception_infos(result):
                # type: (Tuple[ObserverExceptionInfo, ...]) -> None
                """
                Ingest exception information.

                :param result: Exception information from subject-observers.
                """
                for exception_info in result:
                    internal_observer = cast(
                        "InternalObserver", exception_info.observer
                    )
                    action_observer = internal_observer.action_observer_ref()
                    if action_observer is not None:
                        from objetto._observers import ActionObserverExceptionData

                        action_exception_info = ActionObserverExceptionData(
                            observer=action_observer,
                            action=cast("Action", exception_info.payload[0]),
                            phase=cast("Phase", exception_info.payload[1]),
                            exception_type=exception_info.exception_type,
                            exception=exception_info.exception,
                            traceback=exception_info.traceback,
                        )
                        action_exception_infos.append(action_exception_info)

            for commit in commits:
                if type(commit) is BatchCommit:
                    for action in commit.actions:
                        phase = commit.phase  # type: ignore
                        ingest_action_exception_infos(
                            action.receiver.__.subject.send(
                                action, cast("Phase", phase)
                            )
                        )
                else:
                    for action in commit.actions:
                        ingest_action_exception_infos(
                            action.receiver.__.subject.send(action, Phase.PRE)
                        )

                    self.__storage = self.__storage.update(commit.stores)

                    for action in commit.actions:
                        ingest_action_exception_infos(
                            action.receiver.__.subject.send(action, Phase.POST)
                        )

            if action_exception_infos:
                raise ActionObserversFailedError(
                    "external observers raised exceptions (see tracebacks below)",
                    tuple(action_exception_infos),
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
            # noinspection PyCallingNonCallable
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

    @staticmethod
    def __react(obj, action, phase):
        # type: (BaseObject, Action, Phase) -> None
        """
        Run object's reactions.

        :param obj: Object.
        :param action: Action.
        :param phase: Phase.
        """
        for reaction in type(obj)._reactions:
            reaction(obj, action, phase)

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

            def _obj_in_storage():
                try:
                    self.__storage.query(obj)
                except KeyError:
                    return False
                else:
                    return True

            if obj in stores or _obj_in_storage():
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
            stores = stores._set(obj, Store(state=state, data=data, **kwargs))
            commit = Commit(stores=stores)
            self.__commits.append(commit)

    @contextmanager
    def snapshot_context(self, snapshot):
        # type: (ApplicationSnapshot) -> Iterator
        """
        Snapshot read context manager.

        :param snapshot: Snapshot.
        """
        with self.read_context():
            self.__snapshot = snapshot
            try:
                yield
            finally:
                self.__snapshot = None

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
                """Read object store."""
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
                """Read object store."""
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
                """Write changes to object."""
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
                """Read metadata."""
                return self.__read(obj).metadata

            def update_metadata(
                update,  # type: Mapping[str, Any]
            ):
                # type: (...) -> None
                """Update metadata."""
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
                        self.__react(action.receiver, action, Phase.PRE)

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
                        self.__react(action.receiver, action, Phase.POST)

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

    def init_root_objs(self):
        # type: () -> None
        """Initialize root objects."""
        app = self.__app_ref()
        assert app is not None
        assert not self.__roots
        roots = type(app)._roots
        if roots:
            with self.write_context():
                sorted_roots = sorted(
                    itervalues(roots), key=lambda r: (r.priority is None, r.priority)
                )
                for root in sorted_roots:
                    root_obj = root.obj_type(app, **root.kwargs)
                    self.__roots[root] = root_obj
                    root_obj.__.set_root()

    def get_root_obj(self, root):
        # type: (ApplicationRoot) -> BaseObject
        """
        Get root object.

        :param root: Application root descriptor.
        :return: Root object.
        """
        return self.__roots[root]

    def take_snapshot(self):
        """
        Take a snapshot of the current application state.

        :return: Application snapshot.
        :rtype: objetto.applications.ApplicationSnapshot
        """
        storage = self.__storage
        if self.__writing and self.__commits:
            storage = storage.update(self.__commits[-1].stores)
        app = self.__app_ref()
        assert app is not None
        return ApplicationSnapshot(app, storage)

    @property
    def is_writing(self):
        # type: () -> bool
        """
        Whether this application is inside a write context.

        :rtype: bool
        """
        with self.read_context():
            return bool(self.__writing)

    @property
    def is_reading(self):
        # type: () -> bool
        """
        Whether this application is inside a read context.

        :rtype: bool
        """
        with self.read_context():
            return len(self.__reading) > 1


class ApplicationMeta(BaseMeta):
    """
    Metaclass for :class:`objetto.applications.Application`.

    Inherits from:
      - :class:`objetto.bases.BaseMeta`

    Features:
      - Check and store `root descriptors <objetto.applications.root>`_.
    """

    __roots = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ApplicationMeta, Mapping[str, ApplicationRoot]]
    __root_names = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ApplicationMeta, Mapping[ApplicationRoot, str]]

    def __init__(cls, name, bases, dct):
        # type: (str, Tuple[Type, ...], Dict[str, Any]) -> None
        super(ApplicationMeta, cls).__init__(name, bases, dct)

        # Store roots.
        roots = {}
        for base in reversed(getmro(cls)):
            for member_name, member in iteritems(base.__dict__):
                if isinstance(member, ApplicationRoot):
                    roots[member_name] = member
                elif member_name in roots:
                    del roots[member_name]

        # Store root names.
        root_names = {}
        for root_name, root in iteritems(roots):
            root_names[root] = root_name

        type(cls).__roots[cls] = DictState(roots)
        type(cls).__root_names[cls] = DictState(root_names)

    @property
    def _roots(cls):
        # type: () -> Mapping[str, ApplicationRoot]
        """
        Attributes mapped by name.

        :rtype: dict[str, objetto.applications.ApplicationRoot]
        """
        return type(cls).__roots[cls]

    @property
    def _root_names(cls):
        # type: () -> Mapping[Any, str]
        """
        Names mapped by root.

        :rtype: dict[objetto.applications.ApplicationRoot, str]
        """
        return type(cls).__root_names[cls]


class Application(with_metaclass(ApplicationMeta, Base)):
    """
    Application.

    Metaclass:
      - :class:`objetto.applications.ApplicationMeta`

    Inherits from:
      - :class:`objetto.bases.Base`

    Features:
      - Manages multiple :class:`objetto.bases.BaseObject` under the same hierarchy.
      - Offers contexts for reading/writing/batch.
      - Reverts changes when an error occurs.
      - Manages :class:`objetto.objects.Action` propagation, internally and externally.

    When initializing an :class:`objetto.objects.BaseObject`, you have to pass an
    :class:`objetto.applications.Application` as its first parameter.

    .. code:: python

        >>> from objetto import Application, Object

        >>> app = Application()
        >>> obj = Object(app)  # pass application as first parameter
        >>> obj.app is app  # access it through the 'app' property
        True
    """

    __slots__ = ("__weakref__", "__")

    def __init__(self):
        self.__ = ApplicationInternals(self)
        self.__.init_root_objs()

    @final
    @contextmanager
    def read_context(self, snapshot=None):
        # type: (Optional[ApplicationSnapshot]) -> Iterator
        """
        Read context.

        :param snapshot: Application state snapshot.
        :type snapshot: objetto.applications.ApplicationSnapshot

        :return: Context manager.
        :rtype: contextlib.AbstractContextManager

        :raises ValueError: Application mismatch.
        """
        if snapshot is not None:
            with ReraiseContext((TypeError, ValueError), "'snapshot' parameter"):
                assert_is_instance(snapshot, ApplicationSnapshot)
                if snapshot.app is not self:
                    error = "application mismatch"
                    raise ValueError(error)
            with self.__.snapshot_context(snapshot):
                yield
        else:
            with self.__.read_context():
                yield

    @final
    @contextmanager
    def write_context(self):
        # type: () -> Iterator
        """
        Write context.

        :return: Context manager.
        :rtype: contextlib.AbstractContextManager
        """
        with self.__.write_context():
            yield

    @final
    @contextmanager
    def temporary_context(self):
        # type: () -> Iterator
        """
        Temporary write context.

        :return: Context manager.
        :rtype: contextlib.AbstractContextManager
        """
        with self.__.write_context():
            try:
                yield
            except Exception:
                raise
            else:
                raise TemporaryContextException()

    @final
    def take_snapshot(self):
        # type: () -> ApplicationSnapshot
        """
        Take a snapshot of the current application state.

        :return: Application snapshot.
        :rtype: objetto.applications.ApplicationSnapshot
        """
        return self.__.take_snapshot()

    @property
    def is_writing(self):
        # type: () -> bool
        """
        Whether this application is inside a write context.

        :rtype: bool
        """
        return self.__.is_writing

    @property
    def is_reading(self):
        # type: () -> bool
        """
        Whether this application is inside a read context.

        :rtype: bool
        """
        return self.__.is_reading


@final
class ApplicationSnapshot(Base):
    """
    Application snapshot.

    Inherits from:
      - :class:`objetto.bases.Base`

    Features:
      - Freezes entire application state at a moment in time.
      - Can be used with an application's read context to travel back in time.

    You can acquire a snapshot by calling the
    :meth:`objetto.applications.Application.take_snapshot` method. You can then pass it
    to a :meth:`objetto.applications.Application.read_context` in order to temporarily
    bring the whole application back to the time the snapshot was taken.

    .. code:: python

        >>> from objetto import Application, Object, attribute

        >>> class Person(Object):
        ...     name = attribute(str)
        ...
        >>> app = Application()
        >>> obj = Person(app, name="Albert")
        >>> obj.name
        'Albert'
        >>> snapshot = app.take_snapshot()
        >>> obj.name = "Einstein"
        >>> obj.name
        'Einstein'
        >>> with app.read_context(snapshot):
        ...     obj.name
        ...
        'Albert'
        >>> obj.name
        'Einstein'
    """

    __slots__ = ("__app", "__storage")

    def __init__(self, app, storage):
        # type: (Application, Storage) -> None
        self.__app = app
        self.__storage = storage

    @property
    def _storage(self):
        # type: () -> Storage
        """Internal storage."""
        return self.__storage

    @property
    def app(self):
        # type: () -> Application
        """
        Application.

        :rtype: objetto.applications.Application
        """
        return self.__app
