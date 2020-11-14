# -*- coding: utf-8 -*-
"""State-carrying structures."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar
from weakref import WeakKeyDictionary
from inspect import getmro

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, with_metaclass

from ._bases import FINAL_METHOD_TAG, BaseMeta, Base, ProtectedBase, BaseHashable, BaseCollection, BaseProtectedCollection, BaseInteractiveCollection, BaseMutableCollection, final
from ._states import BaseState
from .utils.type_checking import format_types, import_types, assert_is_instance
from .utils.factoring import format_factory, import_factory, run_factory
from .utils.custom_repr import custom_mapping_repr
from .utils.lazy_import import import_path, get_path

if TYPE_CHECKING:
    from typing import Any, Union, Optional, Type, MutableMapping, Tuple, Dict, List

    from .utils.type_checking import LazyTypes
    from .utils.factoring import LazyFactory

__all__ = ["BaseRelationship", "UniqueDescriptor", "BaseStructureMeta", "BaseStructure"]


_SERIALIZED_CLASS_KEY = "__class__"
_ESCAPED_SERIALIZED_CLASS_KEY = "\\__class__"
_SERIALIZED_VALUE_KEY = "value"


_T = TypeVar("_T")  # Any type.


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


class BaseRelationship(ProtectedBase):
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
        "types",
        "subtypes",
        "checked",
        "module",
        "factory",
        "serialized",
        "serializer",
        "deserializer",
        "represented",
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
        self.types = format_types(types, module=module)
        self.subtypes = bool(subtypes)
        self.checked = bool(checked)
        self.module = module
        self.factory = format_factory(factory, module=module)
        self.serialized = bool(serialized)
        self.serializer = format_factory(serializer, module=module)
        self.deserializer = format_factory(deserializer, module=module)
        self.represented = bool(represented)

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


class BaseStructure(with_metaclass(BaseStructureMeta, BaseHashable, BaseCollection[_T], Base)):
    """
    Base structure.

      - Is hashable.
      - Is a collection.
      - Has state.
      - Will have unique hash if unique descriptor is defined.
      - Holds values at locations.
      - Has a relationship for each location.
    """
    __slots__= ()

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


# TODO: protected, interactive, and mutable structures
