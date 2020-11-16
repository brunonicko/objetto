# -*- coding: utf-8 -*-
"""State-carrying structures."""

from abc import abstractmethod
from inspect import getmro
from typing import TYPE_CHECKING, TypeVar, cast
from weakref import WeakKeyDictionary

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, with_metaclass

from ._bases import (
    FINAL_METHOD_TAG,
    Base,
    BaseCollection,
    BaseDict,
    BaseHashable,
    BaseInteractiveCollection,
    BaseInteractiveDict,
    BaseInteractiveList,
    BaseInteractiveSet,
    BaseList,
    BaseMeta,
    BaseMutableCollection,
    BaseMutableDict,
    BaseMutableList,
    BaseMutableSet,
    BaseProtectedCollection,
    BaseProtectedDict,
    BaseProtectedList,
    BaseProtectedSet,
    BaseSet,
    abstract_member,
    final,
)
from ._states import BaseState, DictState, ListState, SetState
from .utils.custom_repr import custom_mapping_repr
from .utils.factoring import format_factory, import_factory, run_factory
from .utils.lazy_import import get_path, import_path
from .utils.type_checking import assert_is_instance, format_types, import_types

if TYPE_CHECKING:
    from typing import Any, Dict, List, MutableMapping, Optional, Tuple, Type, Union

    from ._bases import AbstractType
    from .utils.factoring import LazyFactory
    from .utils.type_checking import LazyTypes

__all__ = [
    "BaseRelationship",
    "UniqueDescriptor",
    "BaseStructureMeta",
    "BaseStructure",
    "BaseProtectedStructure",
    "BaseInteractiveStructure",
    "BaseMutableStructure",
    "BaseAuxiliaryStructureMeta",
    "BaseAuxiliaryStructure",
    "BaseProtectedAuxiliaryStructure",
    "BaseInteractiveAuxiliaryStructure",
    "BaseMutableAuxiliaryStructure",
    "KeyRelationship",
    "BaseDictStructureMeta",
    "BaseDictStructure",
    "BaseProtectedDictStructure",
    "BaseInteractiveDictStructure",
    "BaseMutableDictStructure",
    "BaseListStructureMeta",
    "BaseListStructure",
    "BaseProtectedListStructure",
    "BaseInteractiveListStructure",
    "BaseMutableListStructure",
    "BaseSetStructureMeta",
    "BaseSetStructure",
    "BaseProtectedSetStructure",
    "BaseInteractiveSetStructure",
    "BaseMutableSetStructure",
]


_SERIALIZED_CLASS_KEY = "__class__"
_ESCAPED_SERIALIZED_CLASS_KEY = "\\__class__"
_SERIALIZED_VALUE_KEY = "value"


_T = TypeVar("_T")  # Any type.
_KT = TypeVar("_KT")  # Key type.
_VT = TypeVar("_VT")  # Value type.


def _escape_serialized_class(dct):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Escape serialized '__class__' key.

    :param dct: Serialized dictionary.
    :return: Escaped serialized dictionary.
    """
    if _SERIALIZED_CLASS_KEY in dct:
        dct = dct.copy()
        dct[_ESCAPED_SERIALIZED_CLASS_KEY] = dct.pop(_SERIALIZED_CLASS_KEY)
    return dct


def _unescape_serialized_class(dct):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Unescape serialized '__class__' key.

    :param dct: Serialized dictionary.
    :return: Unescaped serialized dictionary.
    """
    if _ESCAPED_SERIALIZED_CLASS_KEY in dct:
        dct = dct.copy()
        dct[_SERIALIZED_CLASS_KEY] = dct.pop(_ESCAPED_SERIALIZED_CLASS_KEY)
    return dct


def _capitalize_first(string):
    # type: (str) -> str
    """
    Capitalize first letter of string, without touching the rest of it.

    :param string: String.
    :return: Capitalized string.
    """
    return string[:1].upper() + string[1:]


class BaseRelationship(Base):
    """
    Relationship between a structure and its values.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Value factory.
    :param serialized: Whether should be serialized.
    :param serializer: Custom serializer.
    :param deserializer: Custom deserializer.
    :param represented: Whether should be represented.
    """

    __slots__ = (
        "__hash",
        "__types",
        "__subtypes",
        "__checked",
        "__module",
        "__factory",
        "__serialized",
        "__serializer",
        "__deserializer",
        "__represented",
    )

    def __init__(
        self,
        types=(),  # type: LazyTypes
        subtypes=False,  # type: bool
        checked=True,  # type: bool
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
        serialized=True,  # type: bool
        serializer=None,  # type: LazyFactory
        deserializer=None,  # type: LazyFactory
        represented=True,  # type: bool
    ):
        # type: (...) -> None
        self.__hash = None  # type: Optional[int]
        self.__types = format_types(types, module=module)
        self.__subtypes = bool(subtypes)
        self.__checked = bool(checked)
        self.__module = module
        self.__factory = format_factory(factory, module=module)
        self.__serialized = bool(serialized)
        self.__serializer = format_factory(serializer, module=module)
        self.__deserializer = format_factory(deserializer, module=module)
        self.__represented = bool(represented)

    @final
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        if self.__hash is None:
            self.__hash = hash(frozenset(iteritems(self.to_dict())))
        return self.__hash

    @final
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare with another object for equality.

        :param other: Another object.
        :return: True if considered equal.
        """
        if type(self) is not type(other):
            return False
        assert isinstance(other, BaseRelationship)
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
            sorting=True,
            key_repr=str,
        )

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        """
        return {
            "types": frozenset(import_types(self.types)),
            "subtypes": self.subtypes,
            "checked": self.checked,
            "module": self.module,
            "factory": import_factory(self.factory),
            "serialized": self.serialized,
            "serializer": import_factory(self.serializer),
            "deserializer": import_factory(self.deserializer),
            "represented": self.represented,
        }

    @final
    def get_single_exact_type(self, types=(type,)):
        # type: (LazyTypes) -> Optional[Type]
        """
        Get single exact type from available types if possible.

        :param types: Base types.
        :return: Single exact type that is a subclass of one of provided base types.
        """
        if not types or self.subtypes:
            return None
        filtered_types = set(
            typ
            for typ in import_types(self.types)
            if issubclass(typ, import_types(types))
        )
        if len(filtered_types) == 1:
            return next(iter(filtered_types))
        else:
            return None

    @final
    def fabricate_value(self, value, factory=True, **kwargs):
        # type: (Any, bool, Any) -> Any
        """
        Perform type check and run value through factory.

        :param value: Value.
        :param factory: Whether to run value through factory.
        :param kwargs: Keyword arguments to be passed to the factory.
        :return: Fabricated value.
        """
        if factory and self.factory is not None:
            value = run_factory(self.factory, args=(value,), kwargs=kwargs)
        if self.types and self.checked:
            assert_is_instance(value, self.types, subtypes=self.subtypes)
        return value

    @property
    def types(self):
        # type: () -> LazyTypes
        """Types."""
        return self.__types

    @property
    def subtypes(self):
        # type: () -> bool
        """Whether to accept subtypes."""
        return self.__subtypes

    @property
    def checked(self):
        # type: () -> bool
        """Whether to perform runtime type check."""
        return self.__checked

    @property
    def module(self):
        # type: () -> Optional[str]
        """Module path for lazy types/factories."""
        return self.__module

    @property
    def factory(self):
        # type: () -> LazyFactory
        """Value factory."""
        return self.__factory

    @property
    def serialized(self):
        # type: () -> bool
        """Whether should be serialized."""
        return self.__serialized

    @property
    def serializer(self):
        # type: () -> LazyFactory
        """Custom serializer."""
        return self.__serializer

    @property
    def deserializer(self):
        # type: () -> LazyFactory
        """Custom deserializer."""
        return self.__deserializer

    @property
    def represented(self):
        # type: () -> bool
        """Whether should be represented."""
        return self.__represented

    @property
    def passthrough(self):
        # type: () -> bool
        """Whether does not perform type checks and has no factory."""
        return (not self.types or not self.checked) and self.factory is None


@final
class UniqueDescriptor(Base):
    """
    Descriptor to be used on :class:`BaseStructure` classes.
    When used, the object ID will be the hash, and the equality method will compare by
    identity instead of by values.
    If accessed through an instance, the descriptor will return the object ID.
    """

    __slots__ = (FINAL_METHOD_TAG,)

    def __init__(self):
        setattr(self, FINAL_METHOD_TAG, True)

    def __get__(
        self,
        instance,  # type: Optional[BaseStructure]
        owner,  # type: Optional[Type[BaseStructure]]
    ):
        # type: (...) -> Union[int, UniqueDescriptor]
        """
        Get object hash when accessing from instance or this descriptor otherwise.

        :param instance: Instance.
        :param owner: Owner class.
        :return: Object hash or this descriptor.
        """
        if instance is not None:
            cls = type(instance)
            if getattr(cls, "_unique_descriptor", None) is self:
                return hash(id(instance))
        return self


class BaseStructureMeta(BaseMeta):
    """Metaclass for :class:`BaseStructure`."""

    __unique_descriptor_name = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseStructureMeta, Optional[str]]
    __unique_descriptor = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseStructureMeta, Optional[UniqueDescriptor]]

    def __init__(cls, name, bases, dct):
        # type: (str, Tuple[Type, ...], Dict[str, Any]) -> None
        super(BaseStructureMeta, cls).__init__(name, bases, dct)

        # Find unique descriptors.
        unique_descriptors = {}
        for base in reversed(getmro(cls)):
            base_is_base_structure = isinstance(base, BaseStructureMeta)
            for member_name, member in iteritems(base.__dict__):

                # Found unique descriptor.
                if type(member) is UniqueDescriptor:

                    # Valid declaration.
                    if base_is_base_structure:
                        unique_descriptors[member_name] = member

                    # Invalid.
                    else:
                        error = (
                            "unique descriptor '{}' can't be declared in base '{}', "
                            "which is not a subclass of '{}'"
                        ).format(member_name, base.__name__, BaseStructure.__name__)
                        raise TypeError(error)

                # Was overridden.
                elif member_name in unique_descriptors:
                    del unique_descriptors[member_name]

        # Multiple unique descriptors.
        if len(unique_descriptors) > 1:
            error = "class '{}' has multiple unique descriptors at {}".format(
                cls.__name__, ", ".join("'{}'".format(n) for n in unique_descriptors)
            )
            raise TypeError(error)

        # Store unique descriptor.
        unique_descriptor_name = None  # type: Optional[str]
        unique_descriptor = None  # type: Optional[UniqueDescriptor]
        if unique_descriptors:
            unique_descriptor_name, unique_descriptor = next(
                iteritems(unique_descriptors)
            )
        type(cls).__unique_descriptor_name[cls] = unique_descriptor_name
        type(cls).__unique_descriptor[cls] = unique_descriptor

    @property
    @final
    def _unique_descriptor_name(cls):
        # type: () -> Optional[str]
        """Unique descriptor name or None."""
        return type(cls).__unique_descriptor_name[cls]

    @property
    @final
    def _unique_descriptor(cls):
        # type: () -> Optional[UniqueDescriptor]
        """Unique descriptor or None."""
        return type(cls).__unique_descriptor[cls]

    @property
    @abstractmethod
    def _serializable_structure_types(cls):
        # type: () -> Tuple[Type[BaseStructure], ...]
        """Serializable structure types."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """Relationship type."""
        raise NotImplementedError()


class BaseStructure(
    with_metaclass(BaseStructureMeta, BaseHashable, BaseCollection[_T], Base)
):
    """
    Base structure.

      - Is hashable.
      - Is a collection.
      - Has state.
      - Unique hash based on ID if unique descriptor is defined.
      - Holds values at locations.
      - Has a relationship for each location.
      - Serializes/deserializes values and itself.
    """

    __slots__ = ()

    @final
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        cls = type(self)
        if cls._unique_descriptor:
            return hash(id(self))
        else:
            return self._hash()

    @final
    def __eq__(self, other):
        # type: (Any) -> bool
        """
        Compare with another object for equality/identity.

        :param other: Another object.
        :return: True if equal or the exact same object.
        """
        if self is other:
            return True
        if not isinstance(other, collections_abc.Hashable):
            return self._eq(other)
        cls = type(self)
        if cls._unique_descriptor:
            return False
        elif isinstance(other, BaseStructure) and type(other)._unique_descriptor:
            return False
        else:
            return self._eq(other)

    @abstractmethod
    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    @abstractmethod
    def _eq(self, other):
        # type: (Any) -> bool
        """
        Compare with another object for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _get_relationship(cls, location):
        # type: (Any) -> BaseRelationship
        """
        Get relationship at location.

        :param location: Location.
        :return: Relationship.
        """
        raise NotImplementedError()

    @classmethod
    @final
    def deserialize_value(cls, serialized, location=None, **kwargs):
        # type: (Any, Any, Any) -> Any
        """
        Deserialize value for location.

        :param serialized: Serialized value.
        :param location: Location.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized value.
        :raises ValueError: Can't deserialize value.
        """

        # TODO: add "super" to kwargs so custom deserializers can call it.

        # Get relationship.
        relationship = cls._get_relationship(location)
        if not relationship.serialized:
            error = (
                "can't deserialize '{}' object as a value of '{}' since the "
                "relationship{} does not allow for serialization/deserialization"
            ).format(
                type(serialized).__name__,
                cls.__fullname__,
                " at location {}".format(location) if location is not None else "",
            )
            raise ValueError(error)

        # Custom deserializer.
        if relationship.deserializer is not None:

            # Unescape keys.
            if type(serialized) is dict:
                serialized = _unescape_serialized_class(serialized)

            # Run deserializer and return type-check deserialized value.
            value = run_factory(
                relationship.deserializer, args=(serialized,), kwargs=kwargs
            )
            return relationship.fabricate_value(value, factory=False)

        # Possible serialized structure.
        if type(serialized) in (dict, list):

            # Serialized in a dictionary.
            if type(serialized) is dict:

                # Serialized structure with path to its class.
                if _SERIALIZED_CLASS_KEY in serialized:
                    serialized_class = import_path(
                        serialized[_SERIALIZED_CLASS_KEY]
                    )  # type: Type[BaseStructure]
                    serialized_value = serialized[_SERIALIZED_VALUE_KEY]
                    if type(serialized_value) is dict:
                        serialized_value = _unescape_serialized_class(serialized_value)
                    return serialized_class.deserialize(serialized_value, **kwargs)

                # Unescape keys.
                serialized = _unescape_serialized_class(serialized)

            # Single, non-ambiguous structure type.
            single_structure_type = relationship.get_single_exact_type(
                cls._serializable_structure_types
            )  # type: Optional[Type[BaseStructure]]
            if single_structure_type is not None:
                return single_structure_type.deserialize(serialized, **kwargs)

            # Complex type (dict or list).
            single_complex_type = relationship.get_single_exact_type(
                (dict, list)
            )  # type: Optional[Union[Type[Dict], Type[List]]]
            if single_complex_type is None:
                error = (
                    "can't deserialize '{}' object as a value of '{}' without a custom "
                    "deserializer, since relationship{} defines none or ambiguous types"
                ).format(
                    type(serialized).__name__,
                    cls.__fullname__,
                    " at location {}".format(location) if location is not None else "",
                )
                raise TypeError(error)

        # Return type-check deserialized value.
        return relationship.fabricate_value(serialized, factory=False)

    @final
    def serialize_value(self, value, location=None, **kwargs):
        # type: (Any, Any, Any) -> Any
        """
        Serialize value for location.

        :param value: Value.
        :param location: Location.
        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized value.
        :raises ValueError: Can't serialize value.
        """

        # TODO: add "super" to kwargs so custom serializers can call it.

        # Get relationship.
        cls = type(self)
        relationship = cls._get_relationship(location)
        if not relationship.serialized:
            error = (
                "can't serialize '{}' value contained in a '{}' object since the "
                "relationship{} does not allow for serialization/deserialization"
            ).format(
                type(value).__name__,
                cls.__fullname__,
                " at location {}".format(location) if location is not None else "",
            )
            raise ValueError(error)

        # Custom serializer.
        if relationship.serializer is not None:
            serialized_value = run_factory(
                relationship.serializer, args=(value,), kwargs=kwargs
            )

            # Escape keys.
            if type(serialized_value) is dict:
                serialized_value = _escape_serialized_class(serialized_value)

            return serialized_value

        # Structure type.
        if isinstance(value, cls._serializable_structure_types):
            serialized_value = value.serialize(**kwargs)

            # Escape keys.
            if type(serialized_value) is dict:
                serialized_value = _escape_serialized_class(serialized_value)

            # Ambiguous type, serialize with class path.
            single_structure_type = relationship.get_single_exact_type(
                cls._serializable_structure_types
            )  # type: Optional[Type[BaseStructure]]
            if single_structure_type is None:
                return {
                    _SERIALIZED_CLASS_KEY: get_path(type(value)),
                    _SERIALIZED_VALUE_KEY: serialized_value,
                }

            return serialized_value

        # Escape keys.
        if type(value) is dict:
            value = _escape_serialized_class(value)

        return value

    @classmethod
    @abstractmethod
    def deserialize(cls, serialized, **kwargs):
        # type: (Any, Any) -> BaseStructure
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        raise NotImplementedError()

    @abstractmethod
    def serialize(self, **kwargs):
        # type: (Any) -> Any
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def _state(self):
        # type: () -> BaseState
        """State."""
        raise NotImplementedError()


class BaseProtectedStructure(BaseStructure[_T], BaseProtectedCollection[_T]):
    """Base protected structure."""

    __slots__ = ()


class BaseInteractiveStructure(
    BaseProtectedStructure[_T], BaseInteractiveCollection[_T]
):
    """Base interactive structure."""

    __slots__ = ()


class BaseMutableStructure(BaseProtectedStructure[_T], BaseMutableCollection[_T]):
    """Base mutable structure."""

    __slots__ = ()


class BaseAuxiliaryStructureMeta(BaseStructureMeta):
    """Metaclass for :class:`BaseAuxiliaryStructure`."""

    def __init__(cls, name, bases, dct):
        super(BaseAuxiliaryStructureMeta, cls).__init__(name, bases, dct)

        # Check relationship type.
        relationship = getattr(cls, "_relationship")
        if type(relationship) is not type(abstract_member()):
            relationship_type = cls._relationship_type
            assert_is_instance(relationship, relationship_type, subtypes=False)

    @property
    @abstractmethod
    def _base_auxiliary_type(cls):
        # type: () -> Type[BaseAuxiliaryStructure]
        """Base auxiliary structure type."""
        raise NotImplementedError()


class BaseAuxiliaryStructure(
    with_metaclass(BaseAuxiliaryStructureMeta, BaseStructure[_T])
):
    """Structure with a single relationship for all locations."""

    __slots__ = ()

    _relationship = abstract_member()  # type: Union[AbstractType, BaseRelationship]
    """Relationship for all locations."""

    @classmethod
    @final
    def _get_relationship(cls, location=None):
        # type: (Any) -> BaseRelationship
        """
        Get relationship.

        :param location: Location.
        :return: Relationship.
        """
        return cast("BaseRelationship", cls._relationship)


class BaseProtectedAuxiliaryStructure(
    BaseAuxiliaryStructure[_T], BaseProtectedStructure[_T], BaseProtectedCollection[_T]
):
    """Base protected auxiliary structure."""

    __slots__ = ()


class BaseInteractiveAuxiliaryStructure(
    BaseProtectedAuxiliaryStructure[_T],
    BaseInteractiveStructure[_T],
    BaseInteractiveCollection[_T],
):
    """Base interactive auxiliary structure."""

    __slots__ = ()


class BaseMutableAuxiliaryStructure(
    BaseProtectedAuxiliaryStructure[_T],
    BaseMutableStructure[_T],
    BaseMutableCollection[_T],
):
    """Base mutable auxiliary structure."""

    __slots__ = ()


@final
class KeyRelationship(Base):
    """
    Relationship between a dictionary auxiliary structure and their keys.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Key factory.
    """

    __slots__ = (
        "__hash",
        "__types",
        "__subtypes",
        "__checked",
        "__module",
        "__factory",
    )

    def __init__(
        self,
        types=(),  # type: LazyTypes
        subtypes=False,  # type: bool
        checked=True,  # type: bool
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
    ):
        self.__hash = None  # type: Optional[int]
        self.__types = format_types(types, module=module)
        self.__subtypes = bool(subtypes)
        self.__checked = bool(checked)
        self.__module = module
        self.__factory = format_factory(factory, module=module)

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        if self.__hash is None:
            self.__hash = hash(frozenset(iteritems(self.to_dict())))
        return self.__hash

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare with another object for equality.

        :param other: Another object.
        :return: True if considered equal.
        """
        if type(self) is not type(other):
            return False
        assert isinstance(other, KeyRelationship)
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
            sorting=True,
            key_repr=str,
        )

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        """
        return {
            "types": frozenset(import_types(self.types)),
            "subtypes": self.subtypes,
            "checked": self.checked,
            "module": self.module,
            "factory": import_factory(self.factory),
        }

    def fabricate_key(self, key, factory=True, **kwargs):
        # type: (Any, bool, Any) -> Any
        """
        Perform type check and run key through factory.

        :param key: Key.
        :param factory: Whether to run value through factory.
        :param kwargs: Keyword arguments to be passed to the factory.
        :return: Fabricated value.
        """
        if factory and self.factory is not None:
            key = run_factory(self.factory, args=(key,), kwargs=kwargs)
        if self.types and self.checked:
            assert_is_instance(key, self.types, subtypes=self.subtypes)
        return key

    @property
    def types(self):
        # type: () -> LazyTypes
        """Types."""
        return self.__types

    @property
    def subtypes(self):
        # type: () -> bool
        """Whether to accept subtypes."""
        return self.__subtypes

    @property
    def checked(self):
        # type: () -> bool
        """Whether to perform runtime type check."""
        return self.__checked

    @property
    def module(self):
        # type: () -> Optional[str]
        """Module path for lazy types/factories."""
        return self.__module

    @property
    def factory(self):
        # type: () -> LazyFactory
        """Key factory."""
        return self.__factory

    @property
    def passthrough(self):
        # type: () -> bool
        """Whether does not perform type checks and has no factory."""
        return (not self.types or not self.checked) and self.factory is None


class BaseDictStructureMeta(BaseAuxiliaryStructureMeta):
    """Metaclass for :class:`DictStructure`."""

    def __init__(cls, name, bases, dct):
        super(BaseDictStructureMeta, cls).__init__(name, bases, dct)

        # Check key relationship type.
        assert_is_instance(
            getattr(cls, "_key_relationship"),
            (cls._key_relationship_type, type(abstract_member())),
            subtypes=False,
        )

    @property
    @final
    def _key_relationship_type(cls):
        # type: () -> Type[KeyRelationship]
        """Relationship type."""
        return KeyRelationship


class BaseDictStructure(
    with_metaclass(
        BaseDictStructureMeta,
        BaseAuxiliaryStructure,
        BaseDict[_KT, _VT],
    )
):
    """Base dictionary structure."""

    __slots__ = ()

    _key_relationship = abstract_member()  # type: Union[AbstractType, KeyRelationship]
    """Relationship for the keys."""

    @property
    @abstractmethod
    def _state(self):
        # type: () -> DictState[_KT, _VT]
        """Internal state."""
        raise NotImplementedError()


class BaseProtectedDictStructure(
    BaseDictStructure[_KT, _VT],
    BaseProtectedAuxiliaryStructure[_KT],
    BaseProtectedDict[_KT, _VT],
):
    """Base protected dictionary structure."""

    __slots__ = ()


class BaseInteractiveDictStructure(
    BaseProtectedDictStructure[_KT, _VT],
    BaseInteractiveAuxiliaryStructure[_KT],
    BaseInteractiveDict[_KT, _VT],
):
    """Base interactive dictionary structure."""

    __slots__ = ()


class BaseMutableDictStructure(
    BaseProtectedDictStructure[_KT, _VT],
    BaseMutableAuxiliaryStructure[_KT],
    BaseMutableDict[_KT, _VT],
):
    """Base mutable dictionary structure."""

    __slots__ = ()


class BaseListStructureMeta(BaseAuxiliaryStructureMeta):
    """Metaclass for :class:`ListStructure`."""


class BaseListStructure(
    with_metaclass(
        BaseListStructureMeta,
        BaseAuxiliaryStructure,
        BaseList[_T],
    )
):
    """Base list structure."""

    __slots__ = ()

    @property
    @abstractmethod
    def _state(self):
        # type: () -> ListState[_T]
        """Internal state."""
        raise NotImplementedError()


class BaseProtectedListStructure(
    BaseListStructure[_T], BaseProtectedAuxiliaryStructure[_T], BaseProtectedList[_T]
):
    """Base protected list structure."""

    __slots__ = ()


class BaseInteractiveListStructure(
    BaseProtectedListStructure[_T],
    BaseInteractiveAuxiliaryStructure[_T],
    BaseInteractiveList[_T],
):
    """Base interactive list structure."""

    __slots__ = ()


class BaseMutableListStructure(
    BaseProtectedListStructure[_T],
    BaseMutableAuxiliaryStructure[_T],
    BaseMutableList[_T],
):
    """Base mutable list structure."""

    __slots__ = ()


class BaseSetStructureMeta(BaseAuxiliaryStructureMeta):
    """Metaclass for :class:`SetStructure`."""


class BaseSetStructure(
    with_metaclass(
        BaseSetStructureMeta,
        BaseAuxiliaryStructure,
        BaseSet[_T],
    )
):
    """Base set structure."""

    __slots__ = ()

    @property
    @abstractmethod
    def _state(self):
        # type: () -> SetState[_T]
        """Internal state."""
        raise NotImplementedError()


class BaseProtectedSetStructure(
    BaseSetStructure[_T], BaseProtectedAuxiliaryStructure[_T], BaseProtectedSet[_T]
):
    """Base protected set structure."""

    __slots__ = ()


class BaseInteractiveSetStructure(
    BaseProtectedSetStructure[_T],
    BaseInteractiveAuxiliaryStructure[_T],
    BaseInteractiveSet[_T],
):
    """Base interactive set structure."""

    __slots__ = ()


class BaseMutableSetStructure(
    BaseProtectedSetStructure[_T], BaseMutableAuxiliaryStructure[_T], BaseMutableSet[_T]
):
    """Base mutable set structure."""

    __slots__ = ()