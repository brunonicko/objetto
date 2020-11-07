# -*- coding: utf-8 -*-
"""Base container classes and metaclasses."""

from inspect import getmro
from abc import abstractmethod
from re import sub as re_sub
from weakref import WeakKeyDictionary
from typing import TYPE_CHECKING

from six import with_metaclass, iteritems
from slotted import SlottedHashable, SlottedContainer, SlottedSized, SlottedIterable

from .._bases import (
    FINAL_METHOD_TAG,
    BaseMeta,
    Base,
    ProtectedBase,
    final,
    make_base_cls,
    abstract_member,
)
from ..utils.type_checking import (
    get_type_names, format_types, import_types, assert_is_instance
)
from ..utils.lazy_import import import_path, get_path
from ..utils.factoring import format_factory, run_factory, import_factory
from ..utils.custom_repr import custom_mapping_repr

if TYPE_CHECKING:
    from typing import (
        Any, Tuple, Type, Optional, Union, Dict, List, Hashable, Mapping, MutableMapping
    )

    from .._bases import AbstractType
    from ..utils.type_checking import LazyTypes
    from ..utils.factoring import LazyFactory
    from ..utils.immutable import Immutable

__all__ = [
    "make_auxiliary_cls",
    "BaseRelationship",
    "UniqueDescriptor",
    "BaseContainerMeta",
    "BaseContainer",
    "BaseSemiInteractiveContainer",
    "BaseInteractiveContainer",
    "BaseMutableContainer",
    "BaseAuxiliaryContainerMeta",
    "BaseAuxiliaryContainer",
    "BaseSemiInteractiveAuxiliaryContainer",
    "BaseInteractiveAuxiliaryContainer",
    "BaseMutableAuxiliaryContainer",
]


_SERIALIZED_CLASS_KEY = "__class__"
_ESCAPED_SERIALIZED_CLASS_KEY = "\\__class__"
_SERIALIZED_VALUE_KEY = "value"


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


def make_auxiliary_cls(
    base,  # type: Optional[Type[BaseAuxiliaryContainer]]
    relationship=None,  # type: Optional[BaseRelationship]
    qual_name=None,  # type: Optional[str]
    module=None,  # type: Optional[str]
    dct=None,  # type: Optional[Mapping[str, Any]]
):
    # type: (...) -> Type[BaseAuxiliaryContainer]
    """
    Make an auxiliary container subclass on the fly.

    :param base: Base auxiliary container class.
    :param relationship: Relationship.
    :param qual_name: Qualified name.
    :param module: Module.
    :param dct: Members dictionary.
    :return: Generated auxiliary container subclass.
    """

    # Generate default name based on relationship types.
    if qual_name is None:
        type_names = get_type_names(
            tuple(t for t in relationship.types if type(None) is not t)
        )
        if not type_names:
            qual_name = base.__name__
        else:
            base_name = base.__name__
            prefix = "".join(
                _capitalize_first(re_sub(r"[^A-Za-z]+", "", tn)) for tn in type_names
            )
            qual_name = "{}{}".format(
                prefix if prefix != base_name else "",
                base_name,
            )

    # Copy dct and add relationship to it.
    dct_copy = dict(dct or {})
    dct_copy["_relationship"] = relationship

    return make_base_cls(
        base=base,
        qual_name=qual_name,
        module=module,
        dct=dct,
    )


class BaseRelationship(ProtectedBase):
    """
    Relationship between a container and its values.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param type_checked: Whether to perform runtime type check.
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
        "type_checked",
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
        type_checked=True,  # type: bool
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
        serialized=True,  # type: bool
        serializer=None,  # type: LazyFactory
        deserializer=None,  # type: LazyFactory
        represented=True,  # type: bool
    ):
        # type: (...) -> None
        self.types = format_types(types, module=module)
        self.subtypes = bool(subtypes)
        self.type_checked = bool(type_checked)
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
        try:
            return self.__hash  # type: ignore
        except AttributeError:
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

    @final
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
            "types": frozenset(import_types(self.types)),
            "subtypes": self.subtypes,
            "type_checked": self.type_checked,
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
            typ for typ in import_types(self.types)
            if issubclass(typ, import_types(types))
        )
        if len(filtered_types) == 1:
            return next(iter(filtered_types))
        else:
            return None

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
        if self.types and self.type_checked:
            assert_is_instance(value, self.types, subtypes=self.subtypes)
        return value

    @property
    def passthrough(self):
        # type: () -> bool
        """Whether does not perform type checks and has no factory."""
        return (not self.types or not self.type_checked) and self.factory is None


@final
class UniqueDescriptor(Base):
    """
    Descriptor to be used on :class:`BaseContainer` classes.
    When used, the object ID will be the hash, and the equality method will compare by
    identity instead of by values.
    If accessed through an instance, the descriptor will return the object ID.
    """
    __slots__ = (FINAL_METHOD_TAG,)

    def __init__(self):
        setattr(self, FINAL_METHOD_TAG, True)

    def __get__(
        self,
        instance,  # type: Optional[BaseContainer]
        owner,  # type: Optional[Type[BaseContainer]]
    ):
        # type: (...) -> Union[int, UniqueDescriptor]
        """
        Get object ID when accessing from instance or this descriptor otherwise.
        
        :param instance: Instance.
        :param owner: Owner class.
        :return: Object ID or this descriptor.
        """
        if instance is not None:
            cls = type(instance)
            if getattr(cls, "_unique_descriptor", None) is self:
                return id(instance)
        return self


class BaseContainerMeta(BaseMeta):
    """Metaclass for :class:`BaseContainer`."""

    __unique_descriptor_name = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseContainerMeta, Optional[str]]
    __unique_descriptor = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseContainerMeta, Optional[UniqueDescriptor]]

    def __init__(cls, name, bases, dct):
        # type: (str, Tuple[Type, ...], Dict[str, Any]) -> None
        super(BaseContainerMeta, cls).__init__(name, bases, dct)

        # Find unique descriptors.
        unique_descriptors = {}
        for base in reversed(getmro(cls)):
            base_is_base_container = isinstance(base, BaseContainerMeta)
            for member_name, member in iteritems(base.__dict__):

                # Found unique descriptor.
                if type(member) is UniqueDescriptor:

                    # Valid declaration.
                    if base_is_base_container:
                        unique_descriptors[member_name] = member

                    # Invalid.
                    else:
                        error = (
                            "unique descriptor '{}' can't be declared in base '{}', "
                            "which is not a subclass of '{}'"
                        ).format(member_name, base.__name__, BaseContainer.__name__)
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
    def _serializable_container_types(cls):
        # type: () -> Tuple[Type[BaseContainer], ...]
        """Serializable container types."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """Relationship type."""
        raise NotImplementedError()


class BaseContainer(
    with_metaclass(
        BaseContainerMeta,
        Base,
        SlottedHashable,
        SlottedSized,
        SlottedIterable,
        SlottedContainer,
    )
):
    """Base container class."""
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
            return id(self)
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
        cls = type(self)
        if cls._unique_descriptor:
            return False
        elif isinstance(other, BaseContainer) and type(other)._unique_descriptor:
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
        # type: (Optional[Hashable]) -> BaseRelationship
        """
        Get relationship at location.

        :param location: Location.
        :return: Relationship.
        """
        raise NotImplementedError()

    @abstractmethod
    def get(self, location, fallback=None):
        # type: (Optional[Hashable], Any) -> Any
        """
        Get value at location, return fallback value if not found.

        :param location: Location.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        raise NotImplementedError()

    @classmethod
    @final
    def deserialize_value(cls, serialized, location=None, **kwargs):
        # type: (Any, Optional[Hashable], Any) -> Any
        """
        Deserialize value for location.

        :param serialized: Serialized value.
        :param location: Location.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized value.
        :raises ValueError: Can't deserialize value.
        """

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

        # Possible serialized container.
        if type(serialized) in (dict, list):

            # Serialized in a dictionary.
            if type(serialized) is dict:

                # Serialized container with path to its class.
                if _SERIALIZED_CLASS_KEY in serialized:
                    serialized_class = import_path(
                        serialized[_SERIALIZED_CLASS_KEY]
                    )  # type: Type[BaseContainer]
                    serialized_value = serialized[_SERIALIZED_VALUE_KEY]
                    if type(serialized_value) is dict:
                        serialized_value = _unescape_serialized_class(serialized_value)
                    return serialized_class.deserialize(serialized_value, **kwargs)

                # Unescape keys.
                serialized = _unescape_serialized_class(serialized)

            # Single, non-ambiguous container type.
            single_container_type = relationship.get_single_exact_type(
                cls._serializable_container_types
            )  # type: Optional[Type[BaseContainer]]
            if single_container_type is not None:
                return single_container_type.deserialize(serialized, **kwargs)

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
        # type: (Any, Optional[Hashable], Any) -> Any
        """
        Serialize value for location.

        :param value: Value.
        :param location: Location.
        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized value.
        :raises ValueError: Can't serialize value.
        """

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

        # Container type.
        if isinstance(value, cls._serializable_container_types):
            serialized_value = value.serialize(**kwargs)

            # Escape keys.
            if type(serialized_value) is dict:
                serialized_value = _escape_serialized_class(serialized_value)

            # Ambiguous type, serialize with class path.
            single_container_type = relationship.get_single_exact_type(
                cls._serializable_container_types
            )  # type: Optional[Type[BaseContainer]]
            if single_container_type is None:
                return {
                    _SERIALIZED_CLASS_KEY: get_path(type(value)),
                    _SERIALIZED_VALUE_KEY: serialized_value
                }

            return serialized_value

        # Escape keys.
        if type(value) is dict:
            value = _escape_serialized_class(value)

        return value

    @classmethod
    @abstractmethod
    def deserialize(cls, serialized, **kwargs):
        # type: (Any, Any) -> BaseContainer
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
        # type: () -> Immutable
        """State."""
        raise NotImplementedError()


class BaseSemiInteractiveContainer(BaseContainer):
    """Base semi-interactive container."""

    __slots__ = ()

    @abstractmethod
    def _set(self, location, value):
        # type: (Optional[Hashable], Any) -> Any
        raise NotImplementedError()


class BaseInteractiveContainer(BaseSemiInteractiveContainer):
    """Base interactive container."""

    __slots__ = ()

    @abstractmethod
    def set(self, location, value):
        # type: (Optional[Hashable], Any) -> Any
        raise NotImplementedError()


class BaseMutableContainer(BaseInteractiveContainer):
    """Base mutable container."""

    __slots__ = ()


class BaseAuxiliaryContainerMeta(BaseContainerMeta):
    """Metaclass for :class:`BaseAuxiliaryContainer`."""

    def __init__(cls, name, bases, dct):
        super(BaseAuxiliaryContainerMeta, cls).__init__(name, bases, dct)

        # Check relationship type.
        relationship = getattr(cls, "_relationship")
        if type(relationship) is not type(abstract_member()):
            relationship_type = cls._relationship_type
            assert_is_instance(relationship, relationship_type, subtypes=False)

    @property
    @abstractmethod
    def _base_auxiliary_type(cls):
        # type: () -> Type[BaseAuxiliaryContainer]
        """Base auxiliary container type."""
        raise NotImplementedError()


class BaseAuxiliaryContainer(with_metaclass(BaseAuxiliaryContainerMeta, BaseContainer)):
    """Container with a single relationship."""
    __slots__ = ()

    _relationship = abstract_member()  # type: Union[AbstractType, BaseRelationship]
    """Relationship for all locations."""

    @classmethod
    @final
    def _get_relationship(cls, location=None):
        # type: (Optional[Hashable]) -> BaseRelationship
        """
        Get relationship.
        
        :param location: Location.
        :return: Relationship.
        """
        return cls._relationship


class BaseSemiInteractiveAuxiliaryContainer(
    BaseAuxiliaryContainer, BaseSemiInteractiveContainer
):
    """Base semi-interactive auxiliary container."""

    __slots__ = ()


class BaseInteractiveAuxiliaryContainer(
    BaseSemiInteractiveAuxiliaryContainer, BaseInteractiveContainer
):
    """Base interactive auxiliary container."""

    __slots__ = ()


class BaseMutableAuxiliaryContainer(
    BaseInteractiveAuxiliaryContainer, BaseMutableContainer
):
    """Base mutable auxiliary container."""

    __slots__ = ()
