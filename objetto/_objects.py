# -*- coding: utf-8 -*-
"""Mutable structures coordinated by an application."""

from abc import abstractmethod
from contextlib import contextmanager
from inspect import getmro
from itertools import chain
from typing import TYPE_CHECKING, TypeVar, cast, overload
from weakref import WeakKeyDictionary

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import (
    integer_types,
    iteritems,
    raise_from,
    string_types,
    with_metaclass,
    iterkeys,
    itervalues,
)

from ._application import Application
from ._bases import (
    FINAL_METHOD_TAG,
    MISSING,
    Base,
    final,
    init_context,
    make_base_cls,
    abstract_member,
)
from ._changes import (
    Batch,
    Update,
    DictUpdate,
    ListInsert,
    ListDelete,
    ListUpdate,
    ListMove,
    SetUpdate,
    SetRemove,
)
from ._data import (
    BaseData,
    Data,
    DataAttribute,
    DataRelationship,
    InteractiveDictData,
    DictData,
    InteractiveListData,
    ListData,
    InteractiveSetData,
    SetData,
)
from ._states import BaseState, DictState, ListState, SetState
from ._structures import (
    make_auxiliary_cls,
    BaseAttribute,
    BaseMutableAttributeStructure,
    BaseAttributeStructureMeta,
    BaseMutableStructure,
    BaseRelationship,
    BaseStructure,
    BaseStructureMeta,
    BaseAuxiliaryStructureMeta,
    BaseAuxiliaryStructure,
    BaseDictStructureMeta,
    BaseDictStructure,
    BaseListStructureMeta,
    BaseListStructure,
    BaseSetStructureMeta,
    BaseSetStructure,
)
from .utils.custom_repr import custom_mapping_repr
from .utils.reraise_context import ReraiseContext
from .utils.type_checking import assert_is_callable, assert_is_instance, import_types
from .utils.list_operations import resolve_index, resolve_continuous_slice, pre_move
from .utils.weak_reference import WeakReference

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Counter,
        Dict,
        Iterable,
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

    from ._application import Store
    from ._data import BaseAuxiliaryData
    from ._history import HistoryObject
    from .utils.factoring import LazyFactory
    from .utils.type_checking import LazyTypes

__all__ = []


T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.

DELETED = object()
UNIQUE_ATTRIBUTES_METADATA_KEY = "unique_attributes"
REACTION_TAG = "__isreaction__"
DATA_METHOD_TAG = "__isdatamethod__"


@final
class ObjectRelationship(BaseRelationship):
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

        super(ObjectRelationship, self).__init__(
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
        dct = super(ObjectRelationship, self).to_dict()
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
    )  # type: MutableMapping[BaseObjectMeta, Tuple[str, ...]]
    __data_methods = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseObjectMeta, DictState[str, Callable]]

    def __init__(cls, name, bases, dct):
        # type: (str, Tuple[Type, ...], Dict[str, Any]) -> None
        super(BaseObjectMeta, cls).__init__(name, bases, dct)

        # Find history descriptor, data methods, and reactions.
        history_descriptors = {}  # type: Dict[str, HistoryDescriptor]
        reactions = {}  # type: Dict[str, Optional[int]]
        data_methods = {}  # type: Dict[str, Callable]
        for base in reversed(getmro(cls)):
            for member_name, member in iteritems(base.__dict__):
                history_descriptors.pop(member_name, None)
                reactions.pop(member_name, None)
                data_methods.pop(member_name, None)
                if isinstance(member, HistoryDescriptor):
                    history_descriptors[member_name] = member
                elif hasattr(member, REACTION_TAG) and callable(member):
                    reactions[member_name] = getattr(member, REACTION_TAG)
                elif getattr(member, DATA_METHOD_TAG, False) and callable(member):
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
            r
            for r, _ in sorted(iteritems(reactions), key=lambda p: (p[1] is None, p[1]))
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
        return ObjectRelationship

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
        # type: () -> Tuple[str, ...]
        """Names of reaction methods ordered by priority."""
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
_BO = TypeVar("_BO", bound="BaseData")


class BaseObject(with_metaclass(BaseObjectMeta, BaseStructure[T])):
    """
    Base object.

      - Is a protected structure.

    :param app: Application.
    """

    __slots__ = ("__app",)
    __functions__ = BaseObjectFunctions

    def __init__(self, app):
        # type: (Application) -> None
        with ReraiseContext(TypeError, "'app' parameter"):
            assert_is_instance(app, Application)
        self.__app = app

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
        # type: (Type[_O], Dict[str, Any], Application, Any) -> _O
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


# noinspection PyTypeChecker
_OA = TypeVar("_OA", bound="ObjectAttribute")


@final
class ObjectAttribute(BaseAttribute[T]):
    """
    Object attribute.

    :param relationship: Relationship.
    :param default: Default value.
    :param default_factory: Default value factory.
    :param module: Optional module path to use in case partial paths are provided.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :param delegated: Whether attribute allows for delegates to be defined.
    :param dependencies: Attributes needed by the getter delegate.
    :param deserialize_to: Non-serialized attribute to deserialize this into.
    :raises TypeError: Invalid 'dependencies' parameter type.
    :raises ValueError: Can't declare same dependency more than once.
    :raises ValueError: Provided 'changeable' but 'delegated' is True.
    :raises ValueError: Provided 'deletable' but 'delegated' is True.
    :raises ValueError: Provided 'dependencies' but 'delegated' is False.
    :raises ValueError: Provided 'deserialize_to' but 'serialized' is False.
    :raises TypeError: Invalid 'deserialize_to' parameter type.
    :raises ValueError: Can't provide a serialized attribute to 'deserialize_to'.
    """

    __slots__ = (
        "__delegated",
        "__dependencies",
        "__deserialize_to",
        "__fget",
        "__fset",
        "__fdel",
        "__data_attribute",
    )

    def __init__(
        self,
        relationship=ObjectRelationship(),  # type: ObjectRelationship
        default=MISSING,  # type: Any
        default_factory=None,  # type: LazyFactory
        module=None,  # type: Optional[str]
        required=True,  # type: bool
        changeable=None,  # type: Optional[bool]
        deletable=None,  # type: Optional[bool]
        finalized=False,  # type: bool
        abstracted=False,  # type: bool
        delegated=False,  # type: bool
        dependencies=None,  # type: Optional[Iterable[ObjectAttribute]]
        deserialize_to=None,  # type: Optional[ObjectAttribute]
    ):
        # type: (...) -> None

        # 'changeable', 'deletable', 'delegated', and 'dependencies'
        if delegated:
            if dependencies is None:
                dependencies = ()
            else:
                with ReraiseContext(
                    (TypeError, ValueError), "'dependencies' parameter"
                ):
                    if isinstance(dependencies, collections_abc.Iterable):
                        visited_dependencies = set()
                        for dependency in dependencies:
                            assert_is_instance(
                                dependency, ObjectAttribute, subtypes=False
                            )
                            if dependency in visited_dependencies:
                                error = "can't declare same dependency more than once"
                                raise ValueError(error)
                            visited_dependencies.add(dependency)
                        dependencies = tuple(dependencies)
                    else:
                        assert_is_instance(
                            dependencies, ObjectAttribute, subtypes=False
                        )
                        dependencies = (dependencies,)
            if changeable is not None:
                error = "provided 'changeable' but 'delegated' is True"
                raise ValueError(error)
            else:
                changeable = False
            if deletable is not None:
                error = "provided 'deletable' but 'delegated' is True"
                raise ValueError(error)
            else:
                deletable = False
        else:
            if dependencies is not None:
                error = "provided 'dependencies' but 'delegated' is False"
                raise ValueError(error)
            else:
                dependencies = ()
            if changeable is None:
                changeable = True
            else:
                changeable = bool(changeable)
            if deletable is None:
                deletable = False
            else:
                deletable = bool(deletable)

        # 'deserialize_to'
        if deserialize_to is not None:
            if not relationship.serialized:
                error = "provided 'deserialize_to' but 'serialized' is False"
                raise ValueError(error)
            else:
                with ReraiseContext(TypeError, "'deserialize_to' parameter"):
                    assert_is_instance(deserialize_to, ObjectAttribute)
                if deserialize_to.relationship.serialized:
                    error = "can't provide a serialized attribute to 'deserialize_to'"
                    raise ValueError(error)

        super(ObjectAttribute, self).__init__(
            relationship=relationship,
            default=default,
            default_factory=default_factory,
            module=module,
            required=required,
            changeable=changeable,
            deletable=deletable,
            finalized=finalized,
            abstracted=abstracted,
        )

        self.__delegated = bool(delegated)
        self.__dependencies = dependencies
        self.__deserialize_to = deserialize_to
        self.__fget = None  # type: Optional[Callable]
        self.__fset = None  # type: Optional[Callable]
        self.__fdel = None  # type: Optional[Callable]
        self.__data_attribute = None  # type: Optional[DataAttribute]

    def __set__(self, instance, value):
        # type: (Object, T) -> None
        """
        Set attribute value.

        :param instance: Object instance.
        :param value: Value.
        """
        self.set_value(instance, value)

    def __delete__(self, instance):
        # type: (Object) -> None
        """
        Delete attribute value.

        :param instance: Object instance.
        """
        self.delete_value(instance)

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        """
        dct = super(ObjectAttribute, self).to_dict()
        dct.update(
            {
                "delegated": self.delegated,
                "dependencies": self.dependencies,
                "deserialize_to": self.deserialize_to,
                "fget": self.fget,
                "fset": self.fset,
                "fdel": self.fdel,
            }
        )
        return dct

    def set_value(self, instance, value):
        # type: (Object, T) -> None
        """
        Set attribute value.

        :param instance: Object instance.
        :param value: Value.
        """
        instance[self.get_name(instance)] = value

    def delete_value(self, instance):
        # type: (Object) -> None
        """
        Delete attribute value.

        :param instance: Object instance.
        """
        del instance[self.get_name(instance)]

    def getter(self, func):
        # type: (_OA, Callable) -> _OA
        """
        Define a getter delegate method.

        :param func: Delegate function.
        :return: This attribute.
        :raises ValueError: Cannot define a getter for a non-delegated attribute.
        :raises ValueError: Getter delegate already defined.
        :raises TypeError: Invalid delegate type.
        """
        if not self.__delegated:
            error = "cannot define a getter for a non-delegated attribute"
            raise ValueError(error)
        if self.__fget is not None:
            error = "getter delegate already defined"
            raise ValueError(error)
        with ReraiseContext(TypeError, "attribute 'getter' delegate"):
            assert_is_callable(func)
        self.__fget = func
        return self

    def setter(self, func):
        # type: (_OA, Callable) -> _OA
        """
        Define a setter delegate method.

        :param func: Delegate function.
        :return: This attribute.
        :raises ValueError: Cannot define a setter for a non-delegated attribute.
        :raises ValueError: Need to define a getter before defining a setter.
        :raises ValueError: Setter delegate already defined.
        :raises TypeError: Invalid delegate type.
        """
        if not self.__delegated:
            error = "cannot define a setter for a non-delegated attribute"
            raise ValueError(error)
        if self.__fget is None:
            error = "need to define a getter before defining a setter"
            raise ValueError(error)
        if self.__fset is not None:
            error = "setter delegate already defined"
            raise ValueError(error)
        with ReraiseContext(TypeError, "attribute 'setter' delegate"):
            assert_is_callable(func)
        self.__fset = func
        self._changeable = True
        return self

    def deleter(self, func):
        # type: (_OA, Callable) -> _OA
        """
        Define a deleter delegate method.

        :param func: Delegate function.
        :return: This attribute.
        :raises ValueError: Cannot define a deleter for a non-delegated attribute.
        :raises ValueError: Need to define a getter before defining a deleter.
        :raises ValueError: Deleter delegate already defined.
        :raises TypeError: Invalid delegate type.
        """
        if not self.__delegated:
            error = "cannot define a deleter for a non-delegated attribute"
            raise ValueError(error)
        if self.__fget is None:
            error = "need to define a getter before defining a deleter"
            raise ValueError(error)
        if self.__fdel is not None:
            error = "deleter delegate already defined"
            raise ValueError(error)
        with ReraiseContext(TypeError, "attribute 'deleter' delegate"):
            assert_is_callable(func)
        self.__fdel = func
        self._deletable = True
        return self

    @property
    def relationship(self):
        # type: () -> ObjectRelationship
        """Relationship."""
        return cast("ObjectRelationship", super(ObjectAttribute, self).relationship)

    @property
    def delegated(self):
        # type: () -> bool
        """Whether attribute allows for delegates to be defined."""
        return self.__delegated

    @property
    def dependencies(self):
        # type: () -> Tuple[ObjectAttribute, ...]
        """Attributes needed by the getter delegate."""
        return self.__dependencies

    @property
    def deserialize_to(self):
        # type: () -> Optional[ObjectAttribute]
        """Non-serialized attribute to deserialize this into."""
        return self.__deserialize_to

    @property
    def fget(self):
        # type: () -> Optional[Callable]
        """Getter delegate."""
        return self.__fget

    @property
    def fset(self):
        # type: () -> Optional[Callable]
        """Setter delegate."""
        return self.__fset

    @property
    def fdel(self):
        # type: () -> Optional[Callable]
        """Deleter delegate."""
        return self.__fdel

    @property
    def data_attribute(self):
        # type: () -> Optional[DataAttribute]
        """Data attribute."""
        if self.__data_attribute is None:
            data_relationship = self.relationship.data_relationship
            if data_relationship is not None:
                self.__data_attribute = DataAttribute(
                    data_relationship,
                    default=MISSING,
                    default_factory=None,
                    module=self.module,
                    required=self.required,
                    changeable=False,
                    deletable=False,
                    finalized=self.finalized,
                    abstracted=self.abstracted,
                )
        return self.__data_attribute


@final
class ObjectFunctions(BaseObjectFunctions):
    """Static functions for :class:`Object`."""

    __slots__ = ()

    @staticmethod
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
        data = store.data._set(data_location, new_child_data)
        return store.set("data", data)

    @staticmethod
    def get_initial(
        obj,  # type: Object
        input_values,  # type: Mapping[str, Any]
        factory=True,  # type: bool
    ):
        # type: (...) -> Mapping[str, Any]
        """
        Get initial values.

        :param obj: Object.
        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial values.
        """
        cls = type(obj)
        initial = {}
        kwargs = {"app": obj.app}

        for name, value in iteritems(input_values):
            try:
                attribute = cls._attributes[name]
            except KeyError:
                error = "'{}' has no attribute '{}'".format(cls.__fullname__, name)
                exc = AttributeError(error)
                raise_from(exc, None)
                raise exc
            initial[name] = attribute.relationship.fabricate_value(
                value, factory=factory, **kwargs
            )

        for name, attribute in iteritems(cls._attributes):
            if name not in initial:
                if attribute.has_default:
                    initial[name] = attribute.fabricate_default_value(**kwargs)

        return initial

    @staticmethod
    def check_missing(cls, state):
        # type: (Type[Object], DictState[str, Any]) -> None
        """
        Check for attributes with no values.

        :param cls: Object class.
        :param state: State.
        :raises TypeError: Raised when required attributes are missing.
        """
        missing_attributes = set(cls._attributes).difference(state)  # type: Set[str]
        optional_attributes = set(
            n for n, a in iteritems(cls._attributes) if not a.required
        )  # type: Set[str]
        if missing_attributes.difference(optional_attributes):
            error = "missing required attribute{} {}".format(
                "s" if len(missing_attributes) != 1 else "",
                ", ".join("'{}'".format(n) for n in missing_attributes),
            )
            raise TypeError(error)

    @staticmethod
    def update(obj, input_values, factory=True):
        # type: (Object, Mapping[str, Any], bool) -> None
        """
        Update object with values.

        :param obj: Object.
        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        """
        cls = type(obj)
        with obj.app.__.write_context(obj) as (read, write):
            if not input_values:
                return

            # Set updates through intermediary object, sort by number of dependencies.
            intermediary_object = IntermediaryObject(obj.app, type(obj), read().state)
            sorted_input_values = sorted(
                iteritems(input_values),
                key=lambda i: len(cls._attribute_flattened_dependencies.get(i[0], ())),
            )
            for name, value in sorted_input_values:
                try:
                    attribute = cls._attributes[name]
                except KeyError:
                    error = "'{}' has no attribute '{}'".format(cls.__fullname__, name)
                    exc = AttributeError(error)
                    raise_from(exc, None)
                    raise exc
                else:
                    if value is DELETED:
                        intermediary_object.__.delete_value(name)
                    else:
                        if factory:
                            value = attribute.relationship.fabricate_value(
                                value, factory=True, **{"app": obj.app}
                            )
                    intermediary_object.__.set_value(name, value, factory=False)

            # Get results from changes.
            new_values, old_values = intermediary_object.__.get_results()

            # Process raw updates.
            ObjectFunctions.raw_update(obj, new_values, old_values)

    @staticmethod
    def raw_update(
        obj,  # type: Object
        new_values,  # type: Mapping[str, Any]
        old_values,  # type: Mapping[str, Any]
    ):
        # type: (...) -> None
        """
        Raw update (without going through intermediary object).

        :param obj: Object.
        :param new_values: New values.
        :param old_values: Old values.
        :raises AttributeError: Attribute is not changeable and already has a value.
        :raises AttributeError: Attribute is not deletable.
        """
        cls = type(obj)
        with obj.app.__.write_context(obj) as (read, write):

            # Get state, data, and locations cache.
            store = read()
            state = old_state = store.state  # type: DictState[str, Any]
            data = store.data  # type: Data
            metadata = store.metadata  # type: InteractiveDictData[str, Any]
            locations = metadata.get(
                "locations", DictState()
            )  # type: DictState[BaseObject, str]

            # Prepare change information.
            child_counter = collections_abc.Counter()  # type: Counter[BaseObject]
            old_children = set()  # type: Set[BaseObject]
            new_children = set()  # type: Set[BaseObject]
            history_adopters = set()  # type: Set[BaseObject]

            # For every new value.
            for name, value in iteritems(new_values):

                # Get attribute and relationship.
                attribute = cls._attributes[name]
                relationship = attribute.relationship

                # Are we deleting it?
                delete_item = value is DELETED
                if not attribute.deletable and not attribute.delegated:
                    error = "attribute '{}' is not deletable".format(name)
                    raise AttributeError(error)

                # Get old value.
                old_value = old_values[name]

                # Child relationship.
                if relationship.child:
                    same_app = not delete_item and obj._in_same_application(value)

                    # Update children counter, old/new children sets, and locations.
                    if old_value is not DELETED:
                        if not attribute.changeable and not attribute.delegated:
                            error = (
                                "non-changeable attribute '{}' already has a value"
                            ).format(name)
                            raise AttributeError(error)
                        if obj._in_same_application(old_value):
                            child_counter[old_value] -= 1
                            old_children.add(old_value)
                            locations = locations.delete(old_value)
                    if same_app:
                        child_counter[value] += 1
                        new_children.add(value)
                        locations = locations.set(value, name)

                    # Add history adopter.
                    if relationship.history and same_app:
                        history_adopters.add(value)

                    # Update data.
                    if relationship.data:
                        if delete_item:
                            data = data._delete(name)
                        else:
                            data_relationship = relationship.data_relationship
                            if same_app:
                                with value.app.__.write_context(value) as (v_read, _):
                                    data = data._set(
                                        name,
                                        data_relationship.fabricate_value(
                                            v_read().data
                                        ),
                                    )
                            else:
                                data = data._set(
                                    name,
                                    data_relationship.fabricate_value(value),
                                )

                # Update state.
                if not delete_item:
                    state = state.set(name, value)
                else:
                    state = state.delete(name)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = Update(
                __redo__=ObjectFunctions.redo_raw_update,
                __undo__=ObjectFunctions.undo_raw_update,
                obj=obj,
                old_children=old_children,
                new_children=new_children,
                old_values=old_values,
                new_values=new_values,
                old_state=old_state,
                new_state=state,
                history_adopters=history_adopters,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_raw_update(change):
        # type: (Update) -> None
        """
        Raw update object state (REDO).

        :param change: Change.
        """
        ObjectFunctions.raw_update(
            change.obj,
            change.new_values,
            change.old_values,
        )

    @staticmethod
    def undo_raw_update(change):
        # type: (Update) -> None
        """
        Raw update object state (UNDO).

        :param change: Change.
        """
        ObjectFunctions.raw_update(
            change.obj,
            change.old_values,
            change.new_values,
        )


# Mark 'ObjectFunctions' as a final member.
type.__setattr__(cast(type, ObjectFunctions), FINAL_METHOD_TAG, True)


class ObjectMeta(BaseAttributeStructureMeta, BaseObjectMeta):
    """
    Metaclass for :class:`Object`.

    :raises TypeError: Attribute is delegated but no delegates were defined.
    :raises TypeError: Attribute declares a dependency which is not available.
    """

    __data_type = WeakKeyDictionary({})  # type: MutableMapping[ObjectMeta, Type[Data]]
    __attribute_dependencies = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ObjectMeta, DictState]
    __attribute_dependents = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ObjectMeta, DictState]
    __attribute_flattened_dependencies = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ObjectMeta, DictState]
    __attribute_flattened_dependents = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ObjectMeta, DictState]

    def __init__(cls, name, bases, dct):
        # type: (str, Tuple[Type, ...], Dict[str, Any]) -> None
        super(ObjectMeta, cls).__init__(name, bases, dct)

        # TODO: prevent attributes/methods with reserved names

        # Check and gather attribute dependencies.
        dependencies = dict(
            (n, SetState()) for n in cls._attributes
        )  # type: Dict[str, SetState[str]]
        dependents = dict(
            (n, SetState()) for n in cls._attributes
        )  # type: Dict[str, SetState[str]]
        for attribute_name, attribute in iteritems(cls._attributes):

            # Delegated, but does not define any delegate.
            if attribute.delegated and attribute.fget is None:
                error = (
                    "attribute '{}.{}' is delegated but no delegates were defined"
                ).format(name, attribute_name)
                raise TypeError(error)

            # Dependencies.
            for dependency in attribute.dependencies:

                # Dependency is not in the same object.
                if dependency not in cls._attribute_names:
                    error = (
                        "attribute '{}.{}' declares {} as a dependency, which is not a "
                        "valid attribute in the same object"
                    ).format(
                        name,
                        attribute_name,
                        dependency,
                    )
                    raise TypeError(error)

                # Store dependencies.
                dependency_name = cls._attribute_names[dependency]
                dependencies[attribute_name] = dependencies.get(
                    attribute_name, SetState()
                ).add(dependency_name)
                dependents[dependency_name] = dependents.get(
                    dependency_name, SetState()
                ).add(attribute_name)

        def _resolve(nm, deps):
            return deps[nm].update(
                chain.from_iterable(_resolve(n, deps) for n in deps[nm])
            )

        def _flatten(deps):
            flattened = {}
            for nm in deps:
                flattened[nm] = _resolve(nm, deps)
            return flattened

        # Store dependencies and dependents.
        type(cls).__attribute_dependencies[cls] = DictState(dependencies)
        type(cls).__attribute_dependents[cls] = DictState(dependents)
        type(cls).__attribute_flattened_dependencies[cls] = DictState(
            _flatten(dependencies)
        )
        type(cls).__attribute_flattened_dependents[cls] = DictState(
            _flatten(dependents)
        )

    @property
    @final
    def _attribute_type(cls):
        # type: () -> Type[ObjectAttribute]
        """Attribute type."""
        return ObjectAttribute

    @property
    @final
    def _attributes(cls):
        # type: () -> Mapping[str, ObjectAttribute]
        """Attributes mapped by name."""
        return cast("Mapping[str, ObjectAttribute]", super(ObjectMeta, cls)._attributes)

    @property
    @final
    def _attribute_names(cls):
        # type: () -> Mapping[ObjectAttribute, str]
        """Names mapped by attribute."""
        return cast(
            "Mapping[ObjectAttribute, str]", super(ObjectMeta, cls)._attribute_names
        )

    @property
    @final
    def _state_factory(cls):
        # type: () -> Callable[..., DictState]
        """State factory."""
        return DictState

    @property
    @final
    def _attribute_dependencies(cls):
        # type: () -> DictState[str, SetState[str]]
        """Attribute dependencies."""
        return type(cls).__attribute_dependencies[cls]

    @property
    @final
    def _attribute_dependents(cls):
        # type: () -> DictState[str, SetState[str]]
        """Attribute dependents."""
        return type(cls).__attribute_dependents[cls]

    @property
    @final
    def _attribute_flattened_dependencies(cls):
        # type: () -> DictState[str, SetState[str]]
        """Flattened attribute dependencies."""
        return type(cls).__attribute_flattened_dependencies[cls]

    @property
    @final
    def _attribute_flattened_dependents(cls):
        # type: () -> DictState[str, SetState[str]]
        """Flattened attribute dependents."""
        return type(cls).__attribute_flattened_dependents[cls]

    @property
    @final
    def Data(cls):
        # type: () -> Type[Data]
        """Data type."""

        # Try to get cached data type.
        mcs = type(cls)
        try:
            data_type = mcs.__data_type[cls]
        except KeyError:

            # Build data attributes.
            attributes = {}
            for attribute_name, attribute in iteritems(cls._attributes):
                if attribute.relationship.data:
                    data_attribute = attribute.data_attribute
                    if data_attribute is None:
                        continue
                    attributes[attribute_name] = data_attribute

            # Prepare dct.
            dct = {}  # type: Dict[str, Any]
            dct.update(cls._data_methods)
            dct.update(attributes)
            if cls._unique_descriptor is not None:
                dct[cls._unique_descriptor_name] = cls._unique_descriptor

            # Build data type and cache it.
            data_type = make_base_cls(
                base=Data,
                qual_name="{}.{}".format(cls.__fullname__, "Data"),
                module=cls.__module__,
                dct=dct,
            )
            mcs.__data_type[cls] = data_type

        return data_type


# noinspection PyTypeChecker
_O = TypeVar("_O", bound="Object")


class Object(
    with_metaclass(
        ObjectMeta, BaseMutableObject[str], BaseMutableAttributeStructure
    )
):
    """
    Object.

    :param app: Application.
    :param initial: Initial values.
    """

    __slots__ = ()
    __functions__ = ObjectFunctions

    def __init__(self, app, **initial):
        # type: (Application, Any) -> None
        super(Object, self).__init__(app=app)
        cls = type(self)
        with self.app.write_context():
            self.__functions__.update(
                self,
                self.__functions__.get_initial(self, initial),
                factory=False,
            )
            self.__functions__.check_missing(cls, self._state)

    @final
    def __reversed__(self):
        # type: () -> Iterator[str]
        """
        Iterate over reversed attribute names.

        :return: Reversed attribute names iterator.
        """
        return self._state.__reversed__()

    @final
    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get value for attribute name.

        :param name: Attribute name.
        :return: Value.
        :raises KeyError: Attribute does not exist or has no value.
        """
        return self._state[name]

    @final
    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[str]
        """
        Iterate over names of attributes with value.

        :return: Names of attributes with value.
        """
        for name in self._state:
            yield name

    @final
    def __contains__(self, name):
        # type: (Any) -> bool
        """
        Get whether attribute name is valid and has a value.

        :param name: Attribute name.
        :return: True if attribute name is valid and has a value.
        """
        return name in self._state

    @classmethod
    @final
    def _get_relationship(cls, location):
        # type: (str) -> ObjectRelationship
        """
        Get relationship at location (attribute name).

        :param location: Location (attribute name).
        :return: Relationship.
        :raises KeyError: Attribute does not exist.
        """
        return cast("ObjectRelationship", cls._get_attribute(location).relationship)

    @classmethod
    @final
    def _get_attribute(cls, name):
        # type: (str) -> ObjectAttribute
        """
        Get attribute by name.

        :param name: Attribute name.
        :return: Attribute.
        :raises KeyError: Attribute does not exist.
        """
        return cast("ObjectAttribute", cls._attributes[name])

    @final
    def _clear(self):
        # type: (_O) -> _O
        """
        Clear deletable attribute values.

        :return: Transformed.
        :raises AttributeError: No deletable attributes.
        """
        with self.app.write_context():
            cls = type(self)
            update = {}
            for name in self._state:
                attribute = cls._get_attribute(name)
                if attribute.deletable:
                    update[name] = DELETED
            if not update:
                error = "'{}' has no deletable attributes".format(
                    type(self).__fullname__
                )
                raise AttributeError(error)
            self._update(update)
        return self

    @overload
    def _update(self, __m, **kwargs):
        # type: (_O, Iterable[Tuple[str, Any]], Any) -> _O
        pass

    @overload
    def _update(self, **kwargs):
        # type: (_O, Any) -> _O
        pass

    @final
    def _update(self, *args, **kwargs):
        """
        Update multiple attribute values.
        Same parameters as :meth:`dict.update`.

        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        self.__functions__.update(self, dict(*args, **kwargs))
        return self

    @final
    def _set(self, name, value):
        # type: (_O, str, Any) -> _O
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        self.__functions__.update(self, {name: value})
        return self

    @final
    def _delete(self, name):
        # type: (_O, str) -> _O
        """
        Delete attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises KeyError: Attribute does not exist or has no value.
        :raises AttributeError: Attribute is not deletable.
        """
        self.__functions__.update(self, {name: DELETED})
        return self

    @final
    def _locate(self, child):
        # type: (BaseObject) -> str
        """
        Locate child object.

        :param child: Child object.
        :return: Location.
        :raises ValueError: Could not locate child.
        """
        with self.app.__.read_context(self) as read:
            metadata = read().metadata
            try:
                return metadata["locations"][child]
            except KeyError:
                error = "could not locate child {} in {}".format(child, self)
                exc = ValueError(error)
                raise_from(exc, None)
                raise exc

    @final
    def _locate_data(self, child):
        # type: (BaseObject) -> str
        """
        Locate child object's data.

        :param child: Child object.
        :return: Data location.
        :raises ValueError: Could not locate child's data.
        """
        return self._locate(child)

    @final
    def keys(self):
        # type: () -> SetState[str]
        """
        Get names of the attributes with values.

        :return: Attribute names.
        """
        return SetState(iterkeys(self._state))

    @final
    def find_with_attributes(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        return self._state.find_with_attributes(**attributes)

    @classmethod
    @final
    def deserialize(cls, serialized, app=None, **kwargs):
        # type: (Type[_O], Dict[str, Any], Application, Any) -> _O
        """
        Deserialize.

        :param serialized: Serialized.
        :param app: Application (required).
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        if app is None:
            error = (
                "missing required 'app' keyword argument for '{}.deserialize()' method"
            ).format(cls.__fullname__)
            raise ValueError(error)

        with app.write_context():
            self = cast("_O", cls.__new__(cls))
            with init_context(self):
                super(Object, self).__init__(app)

                initial = {}  # type: Dict[str, Any]
                for name, value in iteritems(serialized):
                    try:
                        attribute = cls._attributes[name]
                    except KeyError:
                        error = "'{}.deserialize'; '{}' has no attribute '{}'".format(
                            cls.__fullname__,
                            cls.__fullname__,
                            name,
                        )
                        exc = AttributeError(error)
                        raise_from(exc, None)
                        raise exc

                    if attribute.deserialize_to is not None:
                        deserialize_to_name = cls._attribute_names[
                            attribute.deserialize_to
                        ]
                    else:
                        deserialize_to_name = name

                    initial[deserialize_to_name] = cls.deserialize_value(
                        value, name, **kwargs
                    )

                self.__functions__.update(
                    self,
                    self.__functions__.get_initial(self, initial),
                    factory=False,
                )
                ObjectFunctions.check_missing(cls, self._state)
            return self

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> Dict[str, Any]
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized.
        """
        with self.app.read_context():
            return dict(
                (k, self.serialize_value(v, k, **kwargs))
                for k, v in iteritems(self._state)
                if type(self)._get_relationship(k).serialized
            )

    @property
    @final
    def _state(self):
        # type: () -> DictState[str, Any]
        """State."""
        return cast("DictState", super(Object, self)._state)

    @property
    @final
    def data(self):
        # type: () -> Data
        """Data."""
        return cast("Data", super(Object, self).data)


@final
class IntermediaryObjectInternals(Base):
    """
    Internals for :class:`IntermediaryObject`.

    :param iobj: Internal object.
    :param app: Application.
    :param cls: Object class.
    :param state: Object state.
    """

    __slots__ = (
        "__iobj_ref",
        "__app",
        "__cls",
        "__state",
        "__dependencies",
        "__in_getter",
        "__new_values",
        "__old_values",
        "__dirty",
    )

    def __init__(
        self,
        iobj,  # type: IntermediaryObject
        app,  # type: Application
        cls,  # type: Type[Object]
        state,  # type: DictState[str, Any]
    ):
        # type: (...) -> None
        self.__iobj_ref = WeakReference(iobj)
        self.__app = app
        self.__cls = cls
        self.__state = state
        self.__dependencies = None
        self.__in_getter = None  # type: Optional[ObjectAttribute]
        self.__new_values = {}
        self.__old_values = {}
        self.__dirty = set(cls._attributes).difference(state._state)

    def get_value(self, name):
        """
        Get current value for attribute.

        :param name: Attribute name.
        :return: Value.
        :raises NameError: Can't access attribute not declared as dependency.
        :raises AttributeError: Attribute has no value.
        """
        attribute = self.__get_attribute(name)
        if self.__dependencies is not None and attribute not in self.__dependencies:
            error = (
                "can't access '{}' attribute from '{}' getter delegate since it was "
                "not declared as a dependency"
            ).format(name, self.__cls._attribute_names[self.__in_getter])
            raise NameError(error)

        if name in self.__dirty:
            value = MISSING
        else:
            try:
                value = self.__new_values[name]
            except KeyError:
                try:
                    value = self.__state[name]
                except KeyError:
                    value = MISSING

        if value in (MISSING, DELETED):
            if attribute.delegated:
                with self.__getter_context(attribute):
                    value = attribute.fget(self.iobj)
                value = attribute.relationship.fabricate_value(
                    value, factory=True, **{"app": self.app}
                )
                self.__set_new_value(name, value)
                return value
            else:
                error = "attribute '{}' has no value".format(name)
                raise AttributeError(error)
        else:
            return value

    def set_value(self, name, value, factory=True):
        # type: (str, Any, bool) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :param factory: Whether to run value through factory.
        :raises AttributeError: Can't set attributes while running getter delegate.
        :raises AttributeError: Attribute is read-only.
        :raises AttributeError: Attribute already has a value and can't be changed.
        :raises AttributeError: Can't delete attributes while running getter delegate.
        :raises AttributeError: Attribute is not deletable.
        """

        if self.__in_getter is not None:
            error = "can't set attributes while running getter delegate"
            raise AttributeError(error)

        attribute = self.__get_attribute(name)
        if not attribute.changeable:
            try:
                self.get_value(name)
            except AttributeError:
                pass
            else:
                if attribute.delegated:
                    error = "attribute '{}' is read-only".format(name)
                else:
                    error = (
                        "attribute '{}' already has a value and can't be changed"
                    ).format(name)
                raise AttributeError(error)

        if factory:
            value = attribute.relationship.fabricate_value(
                value, factory=True, **{"app": self.app}
            )
        if attribute.delegated:
            attribute.fset(self.iobj, value)
        else:
            self.__set_new_value(name, value)

    def delete_value(self, name):
        """
        Delete attribute.

        :param name: Attribute name.
        :raises AttributeError: Can't delete attributes while running getter delegate.
        :raises AttributeError: Attribute is not deletable.
        """

        if self.__in_getter is not None:
            error = "can't delete attributes while running getter delegate"
            raise AttributeError(error)

        attribute = self.__get_attribute(name)
        if not attribute.deletable:
            error = "attribute '{}' is not deletable".format(name)
            raise AttributeError(error)

        if attribute.delegated:
            attribute.fdel(self.iobj)
        else:
            self.get_value(name)  # will error if has no value, which we want
            self.__set_new_value(name, DELETED)

    @contextmanager
    def __getter_context(self, attribute):
        # type: (ObjectAttribute) -> Iterator
        """
        Getter context.

        :param attribute: Attribute.
        :return: Getter context manager.
        """
        before = self.__in_getter
        before_dependencies = self.__dependencies

        self.__in_getter = attribute
        if attribute.delegated:
            self.__dependencies = attribute.dependencies
        else:
            self.__dependencies = None

        try:
            yield
        finally:
            self.__in_getter = before
            self.__dependencies = before_dependencies

    def __set_new_value(self, name, value):
        # type: (str, Any) -> None
        """
        Set new attribute value.

        :param name: Attribute name.
        :param value: Value.
        """
        try:
            old_value = self.__state[name]
        except KeyError:
            old_value = DELETED

        if value is not old_value:
            self.__old_values[name] = old_value
            self.__new_values[name] = value
        else:
            self.__old_values.pop(name, None)
            self.__new_values.pop(name, None)

        self.__dirty.discard(name)
        for dependent in self.__cls._attribute_flattened_dependents[name]:
            self.__dirty.add(dependent)
            try:
                old_value = self.__state[dependent]
            except KeyError:
                self.__new_values.pop(dependent, None)
                self.__old_values.pop(dependent, None)
            else:
                self.__old_values[dependent] = old_value
                self.__new_values[dependent] = DELETED

    def __get_attribute(self, name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param name: Attribute name.
        :return: Value.
        :raises AttributeError: Has no such attribute.
        """
        try:
            return self.cls._attributes[name]
        except KeyError:
            pass
        error = "'{}' has no attribute '{}'".format(self.cls.__fullname__, name)
        raise AttributeError(error)

    def get_results(self):
        # type: () -> Tuple[Mapping[str, Any], Mapping[str, Any]]
        """
        Get results.

        :return: New values, old values.
        """
        sorted_dirty = sorted(
            self.__dirty,
            key=lambda n: len(self.__cls._attribute_flattened_dependencies[n]),
        )
        failed = set()
        success = set()
        for name in sorted_dirty:
            try:
                self.get_value(name)
            except AttributeError:
                failed.add(name)
            else:
                success.add(name)

        new_values = self.__new_values.copy()
        old_values = self.__old_values.copy()

        return new_values, old_values

    @property
    def iobj(self):
        # type: () -> Optional[IntermediaryObject]
        """Intermediary object."""
        return self.__iobj_ref()

    @property
    def app(self):
        # type: () -> Application
        """Application."""
        return self.__app

    @property
    def cls(self):
        # type: () -> Type[Object]
        """Object class."""
        return self.__cls

    @property
    def state(self):
        # type: () -> DictState[str, Any]
        """Object state."""
        return self.__state

    @property
    def in_getter(self):
        # type: () -> Optional[ObjectAttribute]
        """Whether running in an attribute's getter delegate."""
        return self.__in_getter


@final
class IntermediaryObject(Base):
    """
    Intermediary object provided to delegates.

    :param app: Application.
    :param cls: Object class.
    :param state: Object state.
    """

    __slots__ = ("__weakref__", "__")

    def __init__(self, app, cls, state):
        # type: (Application, Type[Object], DictState[str, Any]) -> None
        self.__ = IntermediaryObjectInternals(self, app, cls, state)

    def __dir__(self):
        # type: () -> List[str]
        """
        Get attribute names.

        :return: Attribute names.
        """
        if self.__.in_getter is not None:
            attribute = self.__.in_getter
            return sorted(
                n for n, a in iteritems(self.__.cls._attributes)
                if a is attribute or a in a.dependencies
            )
        return sorted(self.__.cls._attributes)

    def __getattr__(self, name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param name: Attribute name.
        :return: Value.
        """
        if name != "__" and name in self.__.cls._attributes:
            return self[name]
        else:
            return self.__getattribute__(name)

    def __setattr__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        """
        if name in self.__.cls._attributes:
            self[name] = value
        else:
            super(IntermediaryObject, self).__setattr__(name, value)

    def __delattr__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.

        :param name: Attribute name.
        """
        if name in self.__.cls._attributes:
            del self[name]
        else:
            super(IntermediaryObject, self).__delattr__(name)

    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param name: Attribute name.
        :return: Value.
        """
        return self.__.get_value(name)

    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        """
        self.__.set_value(name, value)

    def __delitem__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.

        :param name: Attribute name.
        """
        self.__.delete_value(name)


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
        try:
            data_type = mcs.__data_type[cls]
        except KeyError:
            assert issubclass(cls, BaseAuxiliaryObject)
            if cls._relationship is abstract_member():
                error = (
                    "class '{}' did not define abstract member '_relationship'"
                ).format(cls.__fullname__)
                raise NotImplementedError(error)
            data_relationship = cls._relationship.data_relationship
            if data_relationship is None:
                data_type = mcs.__data_type[cls] = cls._base_auxiliary_data_type
            else:
                data_type = mcs.__data_type[cls] = make_auxiliary_cls(
                    cls._base_auxiliary_data_type,
                    data_relationship,
                    qual_name="{}.{}".format(cls.__fullname__, "Data"),
                    module=cls.__module__,
                    unique_descriptor_name=cls._unique_descriptor_name,
                    dct=cls.__functions__.make_data_cls_dct(cls),
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

    _relationship = ObjectRelationship()
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


@final
class DictObjectFunctions(BaseAuxiliaryObjectFunctions):
    """Static functions for :class:`DictObject`."""
    __slots__ = ()

    @staticmethod
    def make_data_cls_dct(auxiliary_cls):
        # type: (Type[DictObject]) -> Dict[str, Any]
        """
        Make data class member dictionary.

        :param auxiliary_cls: Base auxiliary object class.
        :return: Data class member dictionary.
        """
        dct = super(DictObjectFunctions, DictObjectFunctions).make_data_cls_dct(
            auxiliary_cls
        )
        dct.update({"_key_relationship": auxiliary_cls._key_relationship})
        return dct

    @staticmethod
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
        data = store.data._set(data_location, new_child_data)
        if data is store.data:
            return store
        return store.set("data", data)

    @staticmethod
    def update(
        obj,  # type: DictObject
        input_values,  # type: Mapping
        factory=True,  # type: bool
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship
        key_relationship = cls._key_relationship
        with obj.app.__.write_context(obj) as (read, write):
            if not input_values:
                return

            # Get state, data, and locations cache.
            store = read()
            state = old_state = store.state  # type: DictState
            data = store.data  # type: DictData
            metadata = store.metadata  # type: InteractiveDictData
            locations = metadata.get("locations", DictState())  # type: DictState

            # Prepare change information.
            child_counter = collections_abc.Counter()  # type: Counter[BaseObject]
            old_children = set()
            new_children = set()
            history_adopters = set()
            new_values = {}
            old_values = {}

            # Fabricate keys first.
            if factory and cls._key_relationship.factory is not None:
                input_values = dict(
                    (key_relationship.fabricate_key(k, factory=True), v)
                    for k, v in iteritems(input_values)
                )

            # For every input value.
            for key, value in iteritems(input_values):

                # Are we deleting it?
                delete_item = value is DELETED

                # Fabricate new value if not deleting.
                if not delete_item:
                    if factory:
                        value = relationship.fabricate_value(
                            value,
                            factory=factory,
                            **{"app": obj.app}
                        )
                new_values[key] = value

                # Get old value.
                try:
                    old_value = store.state[key]
                except KeyError:
                    if delete_item:
                        error = "can't delete non-existing key '{}'".format(key)
                        raise KeyError(error)
                    old_value = DELETED
                else:
                    if value is old_value:
                        continue
                old_values[key] = old_value

                # Child relationship.
                if relationship.child:
                    same_app = not delete_item and obj.__.in_same_application(value)

                    # Update children counter, old/new children sets, and locations.
                    if old_value is not DELETED:
                        if obj.__.in_same_application(old_value):
                            child_counter[old_value] -= 1
                            old_children.add(old_value)
                            locations = locations.delete(old_value)
                    if same_app:
                        child_counter[value] += 1
                        new_children.add(value)
                        locations = locations.set(value, key)

                    # Add history adopter.
                    if relationship.history and same_app:
                        history_adopters.add(value)

                    # Update data.
                    if relationship.data:
                        if delete_item:
                            data = data._delete(key)
                        else:
                            data_relationship = relationship.data_relationship
                            if same_app:
                                with value.app.__.write_context(value) as (v_read, _):
                                    data = data._set(
                                        key,
                                        data_relationship.fabricate_value(
                                            v_read().data
                                        ),
                                    )
                            else:
                                data = data._set(
                                    key,
                                    data_relationship.fabricate_value(value),
                                )

                # Update state.
                if not delete_item:
                    state = state.set(key, value)
                else:
                    state = state.delete(key)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = DictUpdate(
                __redo__=DictObjectFunctions.redo_update,
                __undo__=DictObjectFunctions.undo_update,
                obj=obj,
                old_children=old_children,
                new_children=new_children,
                old_values=old_values,
                new_values=new_values,
                old_state=old_state,
                new_state=state,
                history_adopters=history_adopters,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_update(change):
        # type: (DictUpdate) -> None
        DictObjectFunctions.update(
            cast("DictObject", change.obj),
            change.new_values,
            factory=False,
        )

    @staticmethod
    def undo_update(change):
        # type: (DictUpdate) -> None
        DictObjectFunctions.update(
            cast("DictObject", change.obj),
            change.old_values,
            factory=False,
        )


type.__setattr__(cast(type, DictObjectFunctions), FINAL_METHOD_TAG, True)


class DictObjectMeta(BaseAuxiliaryObjectMeta, BaseDictStructureMeta):
    """Metaclass for :class:`DictObject`."""

    @property
    @final
    def _state_factory(cls):
        # type: () -> Callable[..., DictState]
        """State factory."""
        return DictState

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[DictObject]
        """Base auxiliary object type."""
        return DictObject

    @property
    @final
    def _base_auxiliary_data_type(cls):
        # type: () -> Type[DictData]
        """Base auxiliary data type."""
        return DictData


# noinspection PyTypeChecker
_DO = TypeVar("_DO", bound="DictObject")


class DictObject(
    with_metaclass(
        DictObjectMeta,
        BaseAuxiliaryObject[KT],
        BaseDictStructure[KT, VT],
    )
):
    """
    Dictionary object.

    :param app: Application.
    :param initial: Initial values.
    """
    __slots__ = ()
    __functions__ = DictObjectFunctions

    def __init__(
        self,
        app,  # type: Application
        initial=(),  # type: Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]]
    ):
        # type: (...) -> None
        super(DictObject, self).__init__(app=app)
        self.__functions__.update(self, dict(initial))

    @final
    def __reversed__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        """
        return self._state.__reversed__()

    @final
    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Invalid key.
        """
        return self._state[key]

    @final
    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key in self._state:
            yield key

    @final
    def __contains__(self, key):
        # type: (Any) -> bool
        """
        Get whether key is present.

        :param key: Key.
        :return: True if contains.
        """
        return key in self._state

    @final
    def _clear(self):
        # type: (_DO) -> _DO
        """
        Clear.

        :return: Transformed.
        :raises AttributeError: No deletable attributes.
        """
        with self.app.write_context():
            self._update((k, DELETED) for k in self._state)
        return self

    @overload
    def _update(self, __m, **kwargs):
        # type: (_DO, Iterable[Tuple[str, Any]], Any) -> _DO
        pass

    @overload
    def _update(self, **kwargs):
        # type: (_DO, Any) -> _DO
        pass

    @final
    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        self.__functions__.update(self, dict(*args, **kwargs))
        return self

    @final
    def _set(self, key, value):
        # type: (_DO, KT, VT) -> _DO
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        self.__functions__.update(self, {key: value})
        return self

    @final
    def _discard(self, key):
        # type: (_DO, KT) -> _DO
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        with self.app.write_context():
            if key in self._state:
                self.__functions__.update(self, {key: DELETED})
        return self

    @final
    def _remove(self, key):
        # type: (_DO, KT) -> _DO
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        self.__functions__.update(self, {key: DELETED})
        return self

    @final
    def _locate(self, child):
        # type: (BaseObject) -> KT
        """
        Locate child object.

        :param child: Child object.
        :return: Location.
        :raises ValueError: Could not locate child.
        """
        with self.app.__.read_context(self) as read:
            metadata = read().metadata
            try:
                return metadata["locations"][child]
            except KeyError:
                error = "could not locate child {} in {}".format(child, self)
                exc = ValueError(error)
                raise_from(exc, None)
                raise exc

    @final
    def _locate_data(self, child):
        # type: (BaseObject) -> KT
        """
        Locate child object's data.

        :param child: Child object.
        :return: Data location.
        :raises ValueError: Could not locate child's data.
        """
        return self._locate(child)

    @classmethod
    @final
    def deserialize(cls, serialized, app=None, **kwargs):
        # type: (Type[_O], Dict[str, Any], Application, Any) -> _O
        """
        Deserialize.

        :param serialized: Serialized.
        :param app: Application (required).
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        if app is None:
            error = (
                "missing required 'app' keyword argument for '{}.deserialize()' method"
            ).format(cls.__fullname__)
            raise ValueError(error)

        with app.write_context():
            self = cast("DictObject", cls.__new__(cls))
            with init_context(self):
                super(DictObject, self).__init__(app)
                initial = dict(
                    (n, cls.deserialize_value(v, None, **kwargs))
                    for n, v in iteritems(serialized)
                    if cls._relationship.serialized
                )
                self.__functions__.update(self, initial)
            return self

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> Dict
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to serializer functions.
        :return: Serialized.
        """
        with self.app.read_context():
            return dict(
                (k, self.serialize_value(v, None, **kwargs))
                for (k, v) in iteritems(self._state)
                if type(self)._relationship.serialized
            )

    @property
    @final
    def _state(self):
        # type: () -> DictState[KT, VT]
        """State."""
        return cast("DictState[KT, VT]", super(DictObject, self)._state)

    @property
    @final
    def data(self):
        # type: () -> DictData[KT, VT]
        """Data."""
        return cast("DictData[KT, VT]", super(DictObject, self).data)


@final
class ListObjectFunctions(BaseAuxiliaryObjectFunctions):
    """Static functions for :class:`ListObject`."""
    __slots__ = ()

    @staticmethod
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
        data = store.data._set(data_location, new_child_data)
        return store.set("data", data)

    @staticmethod
    def insert(
        obj,  # type: ListObject
        index,  # type: int
        input_values,  # type: Iterable[Any]
        factory=True,  # type: bool
    ):
        # type: (...) -> None
        if not input_values:
            error = "no values provided"
            raise ValueError(error)
        cls = type(obj)
        relationship = cls._relationship
        with obj.app.__.write_context(obj) as (read, write):
            if not input_values:
                return

            # Get resolved index.
            index = obj.resolve_index(index, clamp=True)

            # Get state, data, and a brand new locations cache.
            store = read()
            state = old_state = store.state  # type: ListState
            data = store.data  # type: ListData
            metadata = store.metadata  # type: InteractiveDictData
            locations = {}  # type: Dict[BaseObject, int]

            # Prepare change information.
            child_counter = collections_abc.Counter()  # type: Counter[BaseObject]
            new_children = set()  # type: Set[BaseObject]
            history_adopters = set()  # type: Set[BaseObject]
            new_values = []  # type: List[Any]
            new_data_values = []  # type: List[Any]

            # For every input value.
            for i, value in enumerate(input_values):

                # Fabricate new value.
                if factory:
                    value = relationship.fabricate_value(
                        value,
                        factory=factory,
                        **{"app": obj.app}
                    )
                new_values.append(value)

                # Child relationship.
                if relationship.child:
                    same_app = obj.__.in_same_application(value)

                    # Update children counter and new children set.
                    if same_app:
                        child_counter[value] += 1
                        new_children.add(value)
                        locations[value] = index + i

                    # Add history adopter.
                    if relationship.history and same_app:
                        history_adopters.add(value)

                    # Update data.
                    if relationship.data:
                        data_relationship = relationship.data_relationship
                        if same_app:
                            with value.app.__.write_context(value) as (v_read, _):
                                data_value = data_relationship.fabricate_value(
                                    v_read().data,
                                )
                        else:
                            data_value = data_relationship.fabricate_value(value)
                        new_data_values.append(data_value)

            # Update state and data.
            state = state.insert(index, *new_values)
            if relationship.data:
                data = data._insert(index, *new_data_values)

            # Get last index and stop.
            stop = index + len(new_values)
            last_index = stop - 1

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = ListInsert(
                __redo__=ListObjectFunctions.redo_insert,
                __undo__=ListObjectFunctions.undo_insert,
                obj=obj,
                old_children=(),
                new_children=new_children,
                index=index,
                last_index=last_index,
                stop=stop,
                new_values=new_values,
                old_state=old_state,
                new_state=state,
                history_adopters=history_adopters,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_insert(change):
        # type: (ListInsert) -> None
        ListObjectFunctions.insert(
            cast("ListObject", change.obj),
            change.index,
            change.new_values,
            factory=False,
        )

    @staticmethod
    def undo_insert(change):
        # type: (ListInsert) -> None
        ListObjectFunctions.delete(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
        )

    @staticmethod
    def delete(
        obj,  # type: ListObject
        item,  # type: Union[int, slice]
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship
        with obj.app.__.write_context(obj) as (read, write):

            # Get resolved indexes and stop.
            if isinstance(item, slice):
                index, stop = obj.resolve_slice(item)
                if stop == index:
                    return
            else:
                index = obj.resolve_index(item)
                stop = index + 1
            last_index = stop - 1
            slc = slice(index, stop)

            # Get state, data, and a brand new locations cache.
            store = read()
            state = old_state = store.state  # type: ListState
            data = store.data  # type: ListData
            metadata = store.metadata  # type: InteractiveDictData
            locations = {}  # type: Dict[BaseObject, int]

            # Prepare change information.
            child_counter = collections_abc.Counter()  # type: Counter[BaseObject]
            old_children = set()  # type: Set[BaseObject]
            old_values = state[index : last_index + 1]  # type: ListState

            # For every value being removed.
            for value in old_values:

                # Child relationship.
                if relationship.child:
                    same_app = obj.__.in_same_application(value)

                    # Update children counter and new children set.
                    if same_app:
                        child_counter[value] -= 1
                        old_children.add(value)

            # Update state and data.
            state = state.delete_slice(slc)
            if relationship.data:
                data = data._delete_slice(slc)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = ListDelete(
                __redo__=ListObjectFunctions.redo_delete,
                __undo__=ListObjectFunctions.undo_delete,
                obj=obj,
                old_children=old_children,
                new_children=(),
                index=index,
                last_index=last_index,
                stop=stop,
                old_values=old_values,
                old_state=old_state,
                new_state=state,
                history_adopters=(),
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_delete(change):
        # type: (ListDelete) -> None
        ListObjectFunctions.delete(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
        )

    @staticmethod
    def undo_delete(change):
        # type: (ListDelete) -> None
        ListObjectFunctions.insert(
            cast("ListObject", change.obj),
            change.index,
            change.old_values,
            factory=False,
        )

    @staticmethod
    def update(
        obj,  # type: ListObject
        item,  # type: Union[int, slice]
        input_values,  # type: Iterable[Any]
        factory=True,  # type: bool
    ):
        # type: (...) -> None
        if not input_values:
            error = "no values provided"
            raise ValueError(error)
        cls = type(obj)
        relationship = cls._relationship
        with obj.app.__.write_context(obj) as (read, write):

            # Get state, data, and a brand new locations cache.
            store = read()
            state = old_state = store.state  # type: ListState
            data = store.data  # type: ListData
            metadata = store.metadata  # type: InteractiveDictData
            locations = {}  # type: Dict[BaseObject, int]

            # Get old values and check length.
            if isinstance(item, slice):
                index, stop = obj.resolve_slice(item)
            else:
                index = obj.resolve_index(item)
                stop = index + 1
            slc = slice(index, stop)
            last_index = stop - 1
            input_values = list(input_values)
            old_values = state[slc]
            if len(old_values) != len(input_values):
                error = "length of slice and values mismatch"
                raise IndexError(error)
            if len(old_values) == 0:
                return

            # Prepare change information.
            child_counter = collections_abc.Counter()  # type: Counter[BaseObject]
            history_adopters = set()
            old_children = set()
            new_children = set()
            new_values = []
            new_data_values = []

            # For every value being removed.
            for value, old_value in zip(input_values, old_values):

                # Fabricate new value.
                if factory:
                    value = relationship.fabricate_value(
                        value,
                        factory=factory,
                        **{"app": obj.app}
                    )
                new_values.append(value)

                # No change.
                if value is old_value:
                    continue

                # Child relationship.
                if relationship.child:
                    same_app = obj.__.in_same_application(value)

                    # Update children counter, old/new children sets.
                    if obj.__.in_same_application(old_value):
                        child_counter[old_value] -= 1
                        old_children.add(old_value)
                    if same_app:
                        child_counter[value] += 1
                        new_children.add(value)

                    # Add history adopter.
                    if relationship.history and same_app:
                        history_adopters.add(value)

                    # Update data.
                    if relationship.data:
                        data_relationship = relationship.data_relationship
                        if same_app:
                            with value.app.__.write_context(value) as (v_read, _):
                                data_value = data_relationship.fabricate_value(
                                    v_read().data,
                                )
                        else:
                            data_value = data_relationship.fabricate_value(value)
                        new_data_values.append(data_value)

            # Update state and data.
            state = state.set_slice(slc, new_values)
            if relationship.data:
                data = data._set_slice(slc, new_data_values)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = ListUpdate(
                __redo__=ListObjectFunctions.redo_update,
                __undo__=ListObjectFunctions.undo_update,
                obj=obj,
                old_children=old_children,
                new_children=new_children,
                history_adopters=history_adopters,
                index=index,
                last_index=last_index,
                stop=stop,
                old_values=old_values,
                new_values=new_values,
                old_state=old_state,
                new_state=state,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_update(change):
        # type: (ListUpdate) -> None
        ListObjectFunctions.update(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
            change.new_values,
            factory=False,
        )

    @staticmethod
    def undo_update(change):
        # type: (ListUpdate) -> None
        ListObjectFunctions.update(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
            change.old_values,
            factory=False,
        )

    @staticmethod
    def move(
        obj,  # type: ListObject
        item,  # type: Union[int, slice]
        target_index,  # type: int
    ):
        # type: (...) -> None
        with obj.app.__.write_context(obj) as (read, write):

            # Get state, data, and a brand new locations cache.
            store = read()
            state = old_state = store.state  # type: ListState
            data = store.data  # type: ListData
            metadata = store.metadata  # type: InteractiveDictData
            locations = {}  # type: Dict[BaseObject, int]

            # Get resolved indexes and stop.
            pre_move_result = pre_move(len(state), item, target_index)
            if pre_move_result is None:
                return
            index, stop, target_index, post_index = pre_move_result
            post_stop = post_index + (stop - index)
            last_index = stop - 1
            post_last_index = post_stop - 1

            # Prepare change information.
            values = state[index : last_index + 1]

            # Update state and data.
            state = state.move(item, target_index)
            data = data._move(item, target_index)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = ListMove(
                __redo__=ListObjectFunctions.redo_move,
                __undo__=ListObjectFunctions.undo_move,
                obj=obj,
                old_children=(),
                new_children=(),
                history_adopters=(),
                index=index,
                last_index=last_index,
                stop=stop,
                target_index=target_index,
                post_index=post_index,
                post_last_index=post_last_index,
                post_stop=post_stop,
                values=values,
                old_state=old_state,
                new_state=state,
            )
            write(state, data, metadata, collections_abc.Counter(), change)

    @staticmethod
    def redo_move(change):
        # type: (ListMove) -> None
        ListObjectFunctions.move(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
            change.target_index,
        )

    @staticmethod
    def undo_move(change):
        # type: (ListMove) -> None
        ListObjectFunctions.move(
            cast("ListObject", change.obj),
            slice(change.post_index, change.post_stop),
            change.index,
        )


type.__setattr__(cast(type, ListObjectFunctions), FINAL_METHOD_TAG, True)


class ListObjectMeta(BaseAuxiliaryObjectMeta, BaseListStructureMeta):
    """Metaclass for :class:`ListObject`."""

    @property
    @final
    def _state_factory(cls):
        # type: () -> Callable[..., ListState]
        """State factory."""
        return ListState

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[ListObject]
        """Base auxiliary object type."""
        return ListObject

    @property
    @final
    def _base_auxiliary_data_type(cls):
        # type: () -> Type[ListData]
        """Base auxiliary data type."""
        return ListData


# noinspection PyTypeChecker
_LO = TypeVar("_LO", bound="ListObject")


class ListObject(
    with_metaclass(
        ListObjectMeta,
        BaseAuxiliaryObject[T],
        BaseListStructure[T],
    )
):
    """
    List object.

    :param app: Application.
    :param initial: Initial values.
    """
    __slots__ = ()
    __functions__ = ListObjectFunctions

    def __init__(self, app, initial=()):
        # type: (Application, Iterable[T]) -> None
        super(ListObject, self).__init__(app=app)
        self.__functions__.insert(self, 0, initial)

    @final
    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return self._state.__reversed__()

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> ListState[T]
        pass

    @final
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        return self._state[index]

    @final
    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in self._state:
            yield value

    @final
    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :return: True if contains.
        """
        return value in self._state

    @final
    def _clear(self):
        # type: (_LO) -> _LO
        """
        Clear all values.

        :return: Transformed.
        """
        with self.app.write_context():
            state_length = len(self._state)
            if state_length:
                self._delete(slice(0, state_length))
        return self

    @final
    def _insert(self, index, *values):
        # type: (_LO, int, T) -> _LO
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        self.__functions__.insert(self, index, values)
        return self

    @final
    def _append(self, value):
        # type: (_LO, T) -> _LO
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        self.__functions__.insert(self, len(self._state), (value,))
        return self

    @final
    def _extend(self, iterable):
        # type: (_LO, Iterable[T]) -> _LO
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        self.__functions__.insert(self, len(self._state), iterable)
        return self

    @final
    def _remove(self, value):
        # type: (_LO, T) -> _LO
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        with self.app.write_context():
            index = self.index(value)
            self.__functions__.delete(self, index)
            return self

    @final
    def _reverse(self):
        # type: (_LO) -> _LO
        """
        Reverse values.

        :return: Transformed.
        """
        with self.app.write_context():
            if self._state:
                reversed_values = self._state.reverse()
                self.__functions__.update(
                    self, slice(0, len(self._state)), reversed_values
                )
        return self

    @final
    def _move(self, item, target_index):
        # type: (_LO, Union[slice, int], int) -> _LO
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        self.__functions__.move(self, item, target_index)
        return self

    @final
    def _delete(self, item):
        # type: (_LO, Union[slice, int]) -> _LO
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        self.__functions__.delete(self, item)
        return self

    @final
    def _update(self, index, *values):
        # type: (_LO, int, T) -> _LO
        """
        Update value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        self.__functions__.update(self, index, values)
        return self

    @final
    def _locate(self, child):
        # type: (BaseObject) -> int
        """
        Locate child object.

        :param child: Child object.
        :return: Location.
        :raises ValueError: Could not locate child.
        """
        with self.app.__.read_context(self) as read:
            metadata = read().metadata
            try:
                return metadata["locations"][child]
            except KeyError:
                if child in self._children:
                    location = metadata["locations"][child] = self.index(child)
                    return location
                error = "could not locate child {} in {}".format(child, self)
                exc = ValueError(error)
                raise_from(exc, None)
                raise exc

    @final
    def _locate_data(self, child):
        # type: (BaseObject) -> int
        """
        Locate child object's data.

        :param child: Child object.
        :return: Data location.
        :raises ValueError: Could not locate child's data.
        """
        return self._locate(child)

    @classmethod
    @final
    def deserialize(cls, serialized, app=None, **kwargs):
        # type: (Type[_LO], Dict[str, Any], Application, Any) -> _LO
        """
        Deserialize.

        :param serialized: Serialized.
        :param app: Application (required).
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        app = kwargs.get("app")  # type: Optional[Application]
        if app is None:
            error = (
                "missing required 'app' keyword argument for '{}.deserialize()' method"
            ).format(cls.__name__)
            raise ValueError(error)

        with app.write_context():
            self = cast("ListObject", cls.__new__(cls))
            with init_context(self):
                super(ListObject, self).__init__(app)
                initial = (
                    cls.deserialize_value(v, None, **kwargs)
                    for v in serialized
                    if cls._relationship.serialized
                )
                self.__functions__.insert(self, 0, initial)
            return self

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> List
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized.
        """
        with self.app.read_context():
            return list(
                self.serialize_value(v, None, **kwargs)
                for v in self._state
                if type(self)._relationship.serialized
            )

    @property
    @final
    def _state(self):
        # type: () -> ListState[T]
        """State."""
        return cast("ListState[T]", super(ListObject, self)._state)

    @property
    @final
    def data(self):
        # type: () -> ListData[T]
        """Data."""
        return cast("ListData[T]", super(ListObject, self).data)
