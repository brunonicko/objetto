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

from six import integer_types, iteritems, raise_from, string_types, with_metaclass

from ._application import Application
from ._bases import FINAL_METHOD_TAG, MISSING, Base, final, init_context, make_base_cls
from ._changes import Batch, ObjectUpdate
from ._data import BaseData, Data, DataAttribute, DataRelationship, InteractiveDictData
from ._states import BaseState, DictState, SetState
from ._structures import (
    BaseAttribute,
    BaseAttributeStructure,
    BaseAttributeStructureMeta,
    BaseMutableStructure,
    BaseRelationship,
    BaseStructure,
    BaseStructureMeta,
)
from .utils.custom_repr import custom_mapping_repr
from .utils.reraise_context import ReraiseContext
from .utils.type_checking import assert_is_callable, assert_is_instance, import_types
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

    from .utils.factoring import LazyFactory
    from .utils.type_checking import LazyTypes

__all__ = []


T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.

DELETED = object()
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
                        types.add(
                            typ.Data
                        )  # TODO: what if .Data is None (for auxiliary objs)?
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
    @final
    def _serializable_container_types(cls):
        # type: () -> Tuple[Type[BaseObject]]
        """Serializable container types."""
        return (BaseObject,)

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


# noinspection PyTypeChecker
_BO = TypeVar("_BO", bound="BaseData")


class BaseObject(with_metaclass(BaseObjectMeta, BaseStructure[T])):
    """
    Base object.

      - Is a protected structure.
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

    @abstractmethod
    def _locate(self, child):
        # type: (BaseObject) -> Any
        """
        Locate child object.

        :param child: Child object.
        :return: Location.
        """
        raise NotImplementedError()

    @abstractmethod
    def _locate_data(self, child):
        # type: (BaseObject) -> Any
        """
        Locate child object's data.

        :param child: Child object.
        :return: Data location.
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
        """Batch write context."""
        change = Batch(name=str(name), obj=self, metadata=metadata)
        with self.app.__.batch_context(self, change):
            yield change

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
        # type: () -> Optional[BaseData]
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
        data_relationship = self.relationship.data_relationship
        if data_relationship is not None:
            return DataAttribute(
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
        else:
            return None


class ObjectFunctions(BaseObjectFunctions):
    """Base static functions for :class:`Object`."""

    __slots__ = ()

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

                # Get old value.
                old_value = old_values[name]

                # Child relationship.
                if relationship.child:
                    same_app = not delete_item and obj._in_same_application(value)

                    # Update children counter, old/new children sets, and locations.
                    if old_value is not DELETED:
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
                            if same_app:
                                with value.app.__.write_context(value) as (v_read, _):
                                    data = data._set(
                                        name,
                                        relationship.fabricate_data_value(
                                            v_read().data
                                        ),
                                    )
                            else:
                                data = data._set(
                                    name,
                                    relationship.fabricate_data_value(value),
                                )

                # Update state.
                if not delete_item:
                    state = state.set(name, value)
                else:
                    state = state.delete(name)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = ObjectUpdate(
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
        # type: (ObjectUpdate) -> None
        """
        Raw update object state (REDO).

        :param change: Change.
        """
        ObjectFunctions.raw_update(
            cast("Object", change.obj),
            change.new_values,
            change.old_values,
        )

    @staticmethod
    def undo_raw_update(change):
        # type: (ObjectUpdate) -> None
        """
        Raw update object state (UNDO).

        :param change: Change.
        """
        ObjectFunctions.raw_update(
            cast("Object", change.obj),
            change.old_values,
            change.new_values,
        )


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


class Object(with_metaclass(ObjectMeta, BaseAttributeStructure, BaseObject[str])):
    """
    Object.

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

    @classmethod
    @final
    def deserialize(cls, serialized, app=None, **kwargs):
        # type: (Type[_O], Dict[str, Any], Application, Any) -> _O

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
        with self.app.read_context():
            return dict(
                (k, self.serialize_value(v, k, **kwargs))
                for k, v in self._state
                if type(self)._get_relationship(k).serialized
            )

    @property
    @final
    def _state(self):
        # type: () -> DictState[str, Any]
        """Internal state."""
        return cast("DictState", super(Object, self)._state)

    @property
    @final
    def data(self):
        # type: () -> Data
        """Data."""
        return cast("Data", super(Object, self).data)


@final
class IntermediaryObjectInternals(Base):
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

    def __init__(self, iobj, app, cls, state):
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
        if self.__in_getter is not None:
            error = "can't set attributes while running getter delegate"
            raise AttributeError(error)

        attribute = self.__get_attribute(name)
        if not attribute.settable:
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
            self.get_value(name)
            self.__set_new_value(name, DELETED)

    @contextmanager
    def __getter_context(self, attribute):
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
        try:
            return self.cls._attributes[name]
        except KeyError:
            pass
        error = "'{}' has no attribute '{}'".format(self.cls.__name__, name)
        raise AttributeError(error)

    def get_results(self):
        # type: () -> Tuple[Mapping[str, Any], Mapping[str, Any]]

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
        return self.__iobj_ref()

    @property
    def app(self):
        return self.__app

    @property
    def cls(self):
        return self.__cls

    @property
    def state(self):
        return self.__state


@final
class IntermediaryObject(Base):
    __slots__ = ("__weakref__", "__")

    def __init__(self, app, cls, state):
        object.__setattr__(
            self,
            "__",
            IntermediaryObjectInternals(self, app, cls, state),
        )

    def __dir__(self):
        # type: () -> List[str]
        return sorted(self.__.cls._attributes)

    def __getattr__(self, name):
        if name != "__" and name in self.__.cls._attributes:
            return self[name]
        else:
            return self.__getattribute__(name)

    def __setattr__(self, name, value):
        if name in self.__.cls._attributes:
            self[name] = value
        else:
            super(IntermediaryObject, self).__setattr__(name, value)

    def __delattr__(self, name):
        if name in self.__.cls._attributes:
            del self[name]
        else:
            super(IntermediaryObject, self).__delattr__(name)

    def __getitem__(self, name):
        return self.__.get_value(name)

    def __setitem__(self, name, value):
        self.__.set_value(name, value)

    def __delitem__(self, name):
        self.__.delete_value(name)

    @property
    def __objcls__(self):
        return self.__.cls


class HistoryObject(BaseObject):
    __slots__ = ()
