# -*- coding: utf-8 -*-
"""Mutable structures coordinated by an application."""

from abc import abstractmethod
from contextlib import contextmanager
from inspect import getmro
from typing import TYPE_CHECKING, TypeVar, cast, overload
from weakref import WeakKeyDictionary

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import integer_types, iteritems, itervalues, string_types, with_metaclass

from .._applications import Application
from .._bases import Base, BaseMutableCollection, final
from .._changes import Batch
from .._data import BaseAuxiliaryData, BaseData, DataRelationship
from .._states import BaseState, DictState
from .._structures import (
    BaseAuxiliaryStructure,
    BaseAuxiliaryStructureMeta,
    BaseMutableAuxiliaryStructure,
    BaseMutableStructure,
    BaseRelationship,
    BaseStructure,
    BaseStructureMeta,
    make_auxiliary_cls,
)
from ..utils.custom_repr import custom_mapping_repr
from ..utils.recursive_repr import recursive_repr
from ..utils.reraise_context import ReraiseContext
from ..utils.subject_observer import Subject
from ..utils.type_checking import assert_is_instance, import_types
from ..utils.weak_reference import WeakReference

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Dict,
        Iterator,
        Mapping,
        MutableMapping,
        Optional,
        Set,
        Tuple,
        Type,
        Union,
    )

    from .._applications import Action, Phase, Store
    from .._history import HistoryObject
    from ..utils.factoring import LazyFactory
    from ..utils.type_checking import LazyTypes

__all__ = [
    "DELETED",
    "UNIQUE_ATTRIBUTES_METADATA_KEY",
    "DATA_METHOD_TAG",
    "Relationship",
    "BaseReaction",
    "HistoryDescriptor",
    "BaseObjectFunctions",
    "BaseObjectMeta",
    "BaseObject",
    "BaseMutableObject",
    "BaseAuxiliaryObjectFunctions",
    "BaseAuxiliaryObjectMeta",
    "BaseAuxiliaryObject",
    "BaseMutableAuxiliaryObject",
    "BaseProxyObject",
]


T = TypeVar("T")  # Any type.

DELETED = object()
"""Special marker that represents a deleted value."""

UNIQUE_ATTRIBUTES_METADATA_KEY = "unique_attributes"
"""Unique attributes index cache metadata key."""

DATA_METHOD_TAG = "__isdatamethod__"
"""Data method tag."""


@final
class Relationship(BaseRelationship):
    """
    Relationship between an object structure and its values.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Value factory.
    :param serialized: Whether should be serialized.
    :param serializer: Custom serializer.
    :param deserializer: Custom deserializer.
    :param represented: Whether should be represented.
    :param child: Whether object values should be adopted as children.
    :param history: Whether to propagate the history to the child object value.
    :param data: Whether to generate data for the value.
    :param data_relationship: Data relationship (will be generated if not provided).
    :raises ValueError: Provided 'serialized' but 'child' is False.
    :raises ValueError: Provided 'history' but 'child' is False.
    :raises ValueError: Provided 'data' but 'child' is False.
    :raises ValueError: Provided 'data_relationship' but 'child' is False
    :raises ValueError: Provided 'data_relationship' but 'data' is False.
    """

    __slots__ = (
        "__child",
        "__history",
        "__data",
        "__data_relationship",
    )

    def __init__(
        self,
        types=(),  # type: LazyTypes
        subtypes=False,  # type: bool
        checked=None,  # type: Optional[bool]
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
        serialized=None,  # type: Optional[bool]
        serializer=None,  # type: LazyFactory
        deserializer=None,  # type: LazyFactory
        represented=True,  # type: bool
        child=True,  # type: bool
        history=None,  # type: Optional[bool]
        data=None,  # type: Optional[bool]
        data_relationship=None,  # type: Optional[DataRelationship]
    ):
        # type: (...) -> None

        # 'serialized', 'history', and 'data'
        if not child:
            if serialized is not None:
                error = "provided 'serialized' but 'child' is False"
                raise ValueError(error)
            else:
                serialized = False
            if history is not None:
                error = "provided 'history' but 'child' is False"
                raise ValueError(error)
            else:
                history = False
            if data is not None:
                error = "provided 'data' but 'child' is False"
                raise ValueError(error)
            else:
                data = False
        else:
            if serialized is None:
                serialized = True
            else:
                serialized = bool(serialized)
            if history is None:
                history = True
            else:
                history = bool(history)
            if data is None:
                data = True
            else:
                data = bool(data)

        # 'data_relationship'
        if data_relationship is not None:
            if not child:
                error = "provided 'data_relationship' but 'child' is False"
                raise ValueError(error)
            if not data:
                error = "provided 'data_relationship' but 'data' is False"
                raise ValueError(error)

        super(Relationship, self).__init__(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
        )

        self.__child = bool(child)
        self.__history = bool(history) and self.__child
        self.__data = bool(data) and self.__child
        self.__data_relationship = data_relationship

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        """
        dct = super(Relationship, self).to_dict()
        dct.update(
            {
                "child": self.child,
                "history": self.history,
                "data": self.data,
                "data_relationship": self.data_relationship,
            }
        )
        return dct

    @property
    def child(self):
        # type: () -> bool
        """Whether object values should be adopted as children."""
        return self.__child

    @property
    def history(self):
        # type: () -> bool
        """Whether to propagate the history to the child object value."""
        return self.__history

    @property
    def data(self):
        # type: () -> bool
        """Whether to generate data for the value."""
        return self.__data

    @property
    def data_relationship(self):
        # type: () -> Optional[DataRelationship]
        """Data relationship."""
        if self.__data and self.__data_relationship is None:
            types = set()  # type: Set[Union[Type, str]]
            for lazy, typ in zip(self.types, import_types(self.types)):
                if issubclass(typ, BaseObject):
                    if isinstance(lazy, string_types):
                        types.add(lazy + ".Data")
                    else:
                        types.add(typ.Data)
                else:
                    types.add(typ)
            self.__data_relationship = DataRelationship(
                types=types,
                subtypes=self.subtypes,
                checked=False,
                module=self.module,
                factory=None,
                serialized=self.serialized,
                serializer=None,
                deserializer=None,
                represented=self.represented,
                compared=True,
            )
        return self.__data_relationship


# noinspection PyTypeChecker
_BR = TypeVar("_BR", bound="BaseReaction")


class BaseReaction(Base):
    """
    Base method-like that gets called whenever an action is sent through the object.
    """

    __slots__ = ("__hash", "_priority")

    def __init__(self):
        self.__hash = None  # type: Optional[int]
        self._priority = None  # type: Optional[int]

    @abstractmethod
    def __call__(self, obj, action, phase):
        """
        React to actions.

        :param obj: Object.
        :param action: Action.
        :param phase: Phase.
        """
        raise NotImplementedError()

    @overload
    def __get__(self, instance, owner):
        # type: (_BR, None, Type[BaseObject]) -> _BR
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (BaseObject, Type[BaseObject]) -> Callable[[Action, Phase], None]
        pass

    @final
    def __get__(self, instance, owner):
        """
        Get bound reaction method from valid instance or this descriptor otherwise.

        :param instance: Instance.
        :param owner: Owner class.
        :return: Bound reaction method or this descriptor.
        """
        if instance is not None:

            def reaction(action, phase):
                # type: (Action, Phase) -> None
                """
                Bound reaction method.

                :param action: Action.
                :param phase: Phase.
                """
                self(instance, action, phase)

            return reaction
        else:
            return self

    @final
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        if self.__hash is None:
            dct = self.to_dict()
            del dct["priority"]
            self.__hash = hash(frozenset(iteritems(dct)))
        return self.__hash

    @final
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare with another object for equality.

        :param other: Another object.
        :return: True if considered equal.
        """
        if self is other:
            return True
        if type(self) is not type(other):
            return False
        assert isinstance(other, BaseReaction)
        dct = self.to_dict()
        del dct["priority"]
        if not dct:
            return False
        other_dct = other.to_dict()
        if not other_dct:
            return False
        del other_dct["priority"]
        return dct == other_dct

    @final
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
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
        """
        return {
            "priority": self.priority,
        }

    @final
    def set_priority(self, priority):
        # type: (_BR, int) -> _BR
        """
        Set priority and return a new reaction.

        :param priority: Priority.
        :return: New reaction.
        """

        # 'priority'
        if priority is not None:
            with ReraiseContext(TypeError, "'priority' parameter"):
                assert_is_instance(priority, integer_types)

        state = self.__getstate__()
        new_reaction = type(self).__new__(type(self))
        new_reaction.__setstate__(state)
        new_reaction._priority = priority
        return new_reaction

    @property
    @final
    def priority(self):
        # type: () -> Optional[int]
        """Priority."""
        return self._priority


@final
class HistoryDescriptor(Base):
    """
    Descriptor to be used when declaring an :class:`objetto.objects.Object` class.
    When used, every instance of the object class will hold a history that will keep
    track of its changes (and the changes of its children that define a history
    relationship), allowing for easy undo/redo operations.
    If accessed through an instance, the descriptor will return the history object.

    :param size: How many changes to remember.
    :raises TypeError: Invalid 'size' parameter type.
    """

    __slots__ = ("__size",)

    def __init__(self, size=None):
        # type: (Optional[int]) -> None
        if size is not None:
            with ReraiseContext(TypeError, "'size' parameter"):
                assert_is_instance(size, integer_types)
            size = int(size)
            if size < 0:
                size = 0
        self.__size = size

    @overload
    def __get__(self, instance, owner):
        # type: (None, Type[BaseObject]) -> HistoryDescriptor
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (BaseObject, Type[BaseObject]) -> HistoryObject
        pass

    def __get__(self, instance, owner):
        """
        Get history object when accessing from instance or this descriptor otherwise.

        :param instance: Instance.
        :param owner: Owner class.
        :return: History object or this descriptor.
        """
        if instance is not None:
            cls = type(instance)
            if isinstance(instance, BaseObject):
                if getattr(cls, "_history_descriptor", None) is self:
                    history = instance._history
                    assert history is not None
                    return history
        return self

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return hash(frozenset(iteritems(self.to_dict())))

    def __eq__(self, other):
        # type: (Any) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if self is other:
            return True
        if not isinstance(other, collections_abc.Hashable):
            return self.to_dict() == other
        if type(self) is not type(other):
            return False
        assert isinstance(other, HistoryDescriptor)
        return self.to_dict() == other.to_dict()

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
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
        """
        return {"size": self.size}

    @property
    def size(self):
        # type: () -> Optional[int]
        """How many changes to remember."""
        return self.__size


class BaseObjectFunctions(Base):
    """Base static functions for :class:`BaseObject`."""

    __slots__ = ()

    @staticmethod
    @abstractmethod
    def replace_child_data(store, child, data_location, new_child_data):
        # type: (Store, BaseObject, Any, BaseData) -> Store
        """
        Replace child data.

        :param store: Object's store.
        :param child: Child getting their data replaced.
        :param data_location: Location of the existing child's data.
        :param new_child_data: New child's data.
        :return: Updated object's store.
        """
        raise NotImplementedError()


class BaseObjectInternals(Base):
    """
    Internals for :class:`BaseObject`.

    :param obj: Object.
    :param app: Application.
    """

    __slots__ = ("__obj_ref", "__app", "__subject")

    def __init__(self, obj, app):
        # type: (BaseObject, Application) -> None
        self.__obj_ref = WeakReference(obj)
        self.__app = app
        self.__subject = Subject()

    @property
    def obj_ref(self):
        # type: () -> WeakReference[BaseObject]
        """Weak reference to object."""
        return self.__obj_ref

    @property
    def app(self):
        # type: () -> Application
        """Application."""
        return self.__app

    @property
    def subject(self):
        # type: () -> Subject
        """Subject."""
        return self.__subject


class BaseObjectMeta(BaseStructureMeta):
    """
    Metaclass for :class:`BaseObject`.

    :raises TypeError: Class has multiple history descriptors.
    """

    __history_descriptor_name = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseObjectMeta, Optional[str]]
    __history_descriptor = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseObjectMeta, Optional[HistoryDescriptor]]
    __reactions = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseObjectMeta, Tuple[BaseReaction, ...]]
    __data_methods = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseObjectMeta, DictState[str, Callable]]

    def __init__(cls, name, bases, dct):
        # type: (str, Tuple[Type, ...], Dict[str, Any]) -> None
        super(BaseObjectMeta, cls).__init__(name, bases, dct)

        # Find history descriptor, data methods, and reactions.
        history_descriptors = {}  # type: Dict[str, HistoryDescriptor]
        reactions = {}  # type: Dict[str, BaseReaction]
        data_methods = {}  # type: Dict[str, Callable]
        for base in reversed(getmro(cls)):
            for member_name, member in iteritems(base.__dict__):
                history_descriptors.pop(member_name, None)
                reactions.pop(member_name, None)
                data_methods.pop(member_name, None)

                # History descriptor.
                if isinstance(member, HistoryDescriptor):
                    history_descriptors[member_name] = member

                # Reaction.
                elif isinstance(member, BaseReaction):
                    reactions[member_name] = member

                # Data method.
                elif callable(member) and getattr(member, DATA_METHOD_TAG, False):
                    data_methods[member_name] = member

        # Can't have more than one history descriptor.
        if len(history_descriptors) > 1:
            error = "class '{}' has multiple history descriptors at {}".format(
                cls.__name__, ", ".join("'{}'".format(n) for n in history_descriptors)
            )
            raise TypeError(error)

        # Store history descriptor and its name.
        history_descriptor_name = None  # type: Optional[str]
        history_descriptor = None  # type: Optional[HistoryDescriptor]
        if len(history_descriptors) == 1:
            history_descriptor_name, history_descriptor = next(
                iteritems(history_descriptors)
            )

        type(cls).__history_descriptor_name[cls] = history_descriptor_name
        type(cls).__history_descriptor[cls] = history_descriptor

        # Store reactions in a tuple, sort them by priority.
        sorted_reactions = tuple(
            sorted(
                itervalues(reactions),
                key=lambda r: (r.priority is None, r.priority),
            )
        )
        type(cls).__reactions[cls] = sorted_reactions

        # Store data methods.
        type(cls).__data_methods[cls] = DictState(data_methods)

    @property
    @abstractmethod
    def _state_factory(cls):
        # type: () -> Callable[..., BaseState]
        """State factory."""
        raise NotImplementedError()

    @property
    @final
    def _serializable_structure_types(cls):
        # type: () -> Tuple[Type[BaseObject]]
        """Serializable structure types."""
        return (BaseObject,)

    @property
    @final
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """Relationship type."""
        return Relationship

    @property
    @final
    def _history_descriptor_name(cls):
        # type: () -> Optional[str]
        """History descriptor name or None."""
        return type(cls).__history_descriptor_name[cls]

    @property
    @final
    def _history_descriptor(cls):
        # type: () -> Optional[HistoryDescriptor]
        """History descriptor or None."""
        return type(cls).__history_descriptor[cls]

    @property
    @final
    def _reactions(cls):
        # type: () -> Tuple[BaseReaction, ...]
        """Reactions sorted by priority."""
        return type(cls).__reactions[cls]

    @property
    @final
    def _data_methods(cls):
        # type: () -> Mapping[str, Callable]
        """Data method functions."""
        return type(cls).__data_methods[cls]

    @property
    @abstractmethod
    def Data(cls):
        # type: () -> Type[BaseData]
        """Data type."""
        raise NotImplementedError()


# noinspection PyTypeChecker
_BO = TypeVar("_BO", bound="BaseObject")


class BaseObject(with_metaclass(BaseObjectMeta, BaseStructure[T])):
    """
    Base object.

      - Is a protected structure.

    :param app: Application.
    """

    __slots__ = ("__weakref__", "__")
    __functions__ = BaseObjectFunctions

    def __init__(self, app):
        # type: (Application) -> None
        with ReraiseContext(TypeError, "'app' parameter"):
            assert_is_instance(app, Application)
        self.__ = BaseObjectInternals(self, app)
        app.__.init_object(self)

    @final
    def __copy__(self):
        # type: (_BO) -> _BO
        """
        Get copy by using serialization.

        :return: Copy.
        """
        return type(self).deserialize(self.serialize())

    @final
    def _hash(self):
        """
        Get hash based on object id.

        :return: Hash based on object id.
        """
        return hash(id(self))

    @final
    def _eq(self, other):
        # type: (Any) -> bool
        """
        Compare with another object for identity.

        :param other: Another object.
        :return: True if the same object.
        """
        return self is other

    @abstractmethod
    def _locate(self, child):
        # type: (BaseObject) -> Any
        """
        Locate child object.

        :param child: Child object.
        :return: Location.
        :raises ValueError: Could not locate child.
        """
        raise NotImplementedError()

    @abstractmethod
    def _locate_data(self, child):
        # type: (BaseObject) -> Any
        """
        Locate child object's data.

        :param child: Child object.
        :return: Data location.
        :raises ValueError: Could not locate child's data.
        """
        raise NotImplementedError()

    @final
    def _in_same_application(self, value):
        # type: (Any) -> bool
        """
        Get whether a value is an object and belongs to the same application as this.

        :param value: Any value or object.
        :return: True if is an object and belongs to the same application.
        """
        return isinstance(value, BaseObject) and self.app is value.app

    @final
    @contextmanager
    def _batch_context(self, name="Batch", **metadata):
        # type: (str, Any) -> Iterator[Batch]
        """
        Batch context.

        :param name: Batch name.
        :param metadata: Metadata.
        :return: Batch context manager.
        """
        change = Batch(name=str(name), obj=self, metadata=metadata)
        with self.app.__.batch_context(self, change):
            yield change

    @classmethod
    @abstractmethod
    def deserialize(cls, serialized, app=None, **kwargs):
        # type: (Type[_BO], Dict[str, Any], Application, Any) -> _BO
        """
        Deserialize.

        :param serialized: Serialized.
        :param app: Application (required).
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        raise NotImplementedError()

    @property
    def _state(self):
        # type: () -> BaseState
        """State."""
        with self.app.__.read_context(self) as read:
            return read().state

    @property
    @final
    def _parent(self):
        # type: () -> Optional[BaseObject]
        """Parent object or None."""
        with self.app.__.read_context(self) as read:
            return read().parent_ref()

    @property
    @final
    def _children(self):
        # type: () -> Set[BaseObject]
        """Children objects."""
        with self.app.__.read_context(self) as read:
            return read().children

    @property
    @final
    def _history(self):
        # type: () -> Optional[HistoryObject]
        """History or None."""
        with self.app.__.read_context(self) as read:
            store = read()
            if store.history is not None:
                return store.history
            provider = store.history_provider_ref()
            if provider is not None:
                assert isinstance(provider, BaseObject)
                return provider._history
        return None

    @property
    @final
    def app(self):
        # type: () -> Application
        """Application."""
        return self.__.app

    @property
    def data(self):
        # type: () -> Optional[BaseData[T]]
        """Data."""
        with self.app.__.read_context(self) as read:
            return read().data


# noinspection PyAbstractClass
class BaseMutableObject(BaseObject[T], BaseMutableStructure[T]):
    """
    Base mutable object.

      - Is an mutable object structure.
    """

    __slots__ = ()


# noinspection PyAbstractClass
class BaseAuxiliaryObjectFunctions(BaseObjectFunctions):
    """Base static functions for :class:`BaseAuxiliaryObject`."""

    __slots__ = ()

    @staticmethod
    def make_data_cls_dct(auxiliary_cls):
        # type: (Type[BaseAuxiliaryObject]) -> Dict[str, Any]
        """
        Make data class member dictionary.

        :param auxiliary_cls: Base auxiliary object class.
        :return: Data class member dictionary.
        """
        return dict(auxiliary_cls._data_methods)


class BaseAuxiliaryObjectMeta(BaseObjectMeta, BaseAuxiliaryStructureMeta):
    """Metaclass for :class:`BaseAuxiliaryObject`."""

    __data_type = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseAuxiliaryObjectMeta, Type[BaseAuxiliaryData]]

    @property
    @abstractmethod
    def _base_auxiliary_type(cls):
        # type: () -> Type[BaseAuxiliaryObject]
        """Base auxiliary object type."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def _base_auxiliary_data_type(cls):
        # type: () -> Type[BaseAuxiliaryData]
        """Base auxiliary data type."""
        raise NotImplementedError()

    @property
    @final
    def Data(cls):
        # type: () -> Type[BaseAuxiliaryData]
        """Data type."""
        mcs = type(cls)
        cls_ = cast("Type[BaseAuxiliaryObject]", cls)
        try:
            data_type = mcs.__data_type[cls]
        except KeyError:
            data_relationship = cls_._relationship.data_relationship
            if data_relationship is None:
                data_type = mcs.__data_type[cls] = cls._base_auxiliary_data_type
            else:
                data_type = mcs.__data_type[cls] = make_auxiliary_cls(
                    cls._base_auxiliary_data_type,
                    data_relationship,
                    qual_name="{}.{}".format(cls.__fullname__, "Data"),
                    module=cls.__module__,
                    unique_descriptor_name=cls._unique_descriptor_name,
                    dct=cls_.__functions__.make_data_cls_dct(cls_),
                )
        return data_type


# noinspection PyAbstractClass
class BaseAuxiliaryObject(
    with_metaclass(
        BaseAuxiliaryObjectMeta,
        BaseAuxiliaryStructure[T],
        BaseObject[T],
    )
):
    """Base auxiliary object."""

    __slots__ = ()
    __functions__ = BaseAuxiliaryObjectFunctions

    _relationship = Relationship()
    """Relationship for all locations."""

    @final
    def find_with_attributes(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        with self.app.__.read_context(self) as read:
            metadata = read().metadata

            # The 'UniqueAttributes' reaction caches children with unique attributes.
            if UNIQUE_ATTRIBUTES_METADATA_KEY in metadata:
                if not attributes:
                    error = "no attributes provided"
                    raise ValueError(error)
                cache = metadata[UNIQUE_ATTRIBUTES_METADATA_KEY]
                if set(cache).issuperset(attributes):
                    match = None
                    for name, value in iteritems(attributes):
                        if value not in cache[name]:
                            break
                        this_match = cache[name][value]
                        if match is not None and this_match is not match:
                            break
                        match = this_match
                    else:
                        return match

            # Fallback to iterating over the state (slower).
            return self._state.find_with_attributes(**attributes)


# noinspection PyAbstractClass
class BaseMutableAuxiliaryObject(
    BaseAuxiliaryObject[T], BaseMutableAuxiliaryStructure[T]
):
    """Base mutable auxiliary object."""


# noinspection PyTypeChecker
_BPO = TypeVar("_BPO", bound="BaseProxyObject")


class BaseProxyObject(BaseMutableCollection[T]):
    """
    Base auxiliary proxy object.

    :param obj: Auxiliary object.
    """

    __slots__ = ("__obj",)

    @final
    def __init__(self, obj):
        # type: (BaseAuxiliaryObject[T]) -> None
        self.__obj = obj

    @final
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return "{}({})".format(type(self).__fullname__, self._obj)

    @final
    def __hash__(self):
        """
        Get hash based on object id.

        :return: Hash based on object id.
        """
        return hash(id(self))

    @final
    def __eq__(self, other):
        # type: (Any) -> bool
        """
        Compare with another object for identity.

        :param other: Another object.
        :return: True if the same object.
        """
        return self is other

    @final
    def __len__(self):
        # type: () -> int
        """
        Get count.

        :return: Count.
        """
        return self._obj.__len__()

    @final
    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over.

        :return: Iterator.
        """
        for value in self._obj.__iter__():
            yield value

    @final
    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :return: True if contains.
        """
        return value in self._obj

    @final
    def _clear(self):
        # type: (_BPO) -> _BPO
        """
        Clear.

        :return: Transformed.
        """
        self._obj._clear()
        return self

    @final
    def find_with_attributes(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        return self._obj.find_with_attributes(**attributes)

    @property
    def _obj(self):
        # type: () -> BaseAuxiliaryObject
        """Auxiliary object."""
        return self.__obj

    @property
    def _state(self):
        # type: () -> BaseState
        """State."""
        return self._obj._state

    @property
    @final
    def _parent(self):
        # type: () -> Optional[BaseObject]
        """Parent object or None."""
        return self._obj._parent

    @property
    @final
    def _children(self):
        # type: () -> Set[BaseObject]
        """Children objects."""
        return self._obj._children

    @property
    @final
    def _history(self):
        # type: () -> Optional[HistoryObject]
        """History or None."""
        return self._obj._history

    @property
    @final
    def app(self):
        # type: () -> Application
        """Application."""
        return self._obj.app

    @property
    def data(self):
        # type: () -> Optional[BaseData]
        """Data."""
        return self._obj.data
