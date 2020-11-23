# -*- coding: utf-8 -*-
"""State-carrying structures."""

from abc import abstractmethod
from inspect import getmro
from re import sub as re_sub
from typing import TYPE_CHECKING, Generic, TypeVar, cast, overload
from weakref import WeakKeyDictionary

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import (
    iteritems,
    iterkeys,
    itervalues,
    raise_from,
    string_types,
    with_metaclass,
)

from ._bases import (
    ABSTRACT_TAG,
    FINAL_METHOD_TAG,
    INITIALIZING_TAG,
    MISSING,
    AbstractMember,
    Base,
    BaseHashable,
    BaseInteractiveCollection,
    BaseInteractiveDict,
    BaseInteractiveList,
    BaseInteractiveSet,
    BaseMeta,
    BaseMutableCollection,
    BaseMutableDict,
    BaseMutableList,
    BaseMutableSet,
    BaseProtectedCollection,
    BaseProtectedDict,
    BaseProtectedList,
    BaseProtectedSet,
    abstract_member,
    final,
    make_base_cls,
)
from ._states import BaseState, DictState, SetState
from .utils.custom_repr import custom_mapping_repr, custom_iterable_repr
from .utils.factoring import format_factory, import_factory, run_factory
from .utils.lazy_import import get_path, import_path
from .utils.reraise_context import ReraiseContext
from .utils.type_checking import (
    assert_is_instance,
    format_types,
    get_type_names,
    import_types,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        Iterable,
        Iterator,
        List,
        Mapping,
        MutableMapping,
        Optional,
        Tuple,
        Type,
        Union,
    )

    from ._states import ListState
    from .utils.factoring import LazyFactory
    from .utils.type_checking import LazyTypes

__all__ = [
    "make_auxiliary_cls",
    "BaseRelationship",
    "UniqueDescriptor",
    "BaseStructureMeta",
    "BaseStructure",
    "BaseInteractiveStructure",
    "BaseMutableStructure",
    "BaseAttributeMeta",
    "BaseAttribute",
    "BaseAttributeStructureMeta",
    "BaseAttributeStructure",
    "BaseInteractiveAttributeStructure",
    "BaseMutableAttributeStructure",
    "BaseAuxiliaryStructureMeta",
    "BaseAuxiliaryStructure",
    "BaseInteractiveAuxiliaryStructure",
    "BaseMutableAuxiliaryStructure",
    "KeyRelationship",
    "BaseDictStructureMeta",
    "BaseDictStructure",
    "BaseInteractiveDictStructure",
    "BaseMutableDictStructure",
    "BaseListStructureMeta",
    "BaseListStructure",
    "BaseInteractiveListStructure",
    "BaseMutableListStructure",
    "BaseSetStructureMeta",
    "BaseSetStructure",
    "BaseInteractiveSetStructure",
    "BaseMutableSetStructure",
]


_SERIALIZED_CLASS_KEY = "__class__"
_ESCAPED_SERIALIZED_CLASS_KEY = "\\__class__"
_SERIALIZED_VALUE_KEY = "value"


T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.


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


# noinspection PyTypeChecker
_A = TypeVar("_A", bound="Type[BaseAuxiliaryStructure]")


def make_auxiliary_cls(
    base,  # type: _A
    relationship,  # type: BaseRelationship
    qual_name=None,  # type: Optional[str]
    module=None,  # type: Optional[str]
    unique_descriptor_name=None,  # type: Optional[str]
    dct=None,  # type: Optional[Mapping[str, Any]]
):
    # type: (...) -> _A
    """
    Make an auxiliary container subclass on the fly.
    :param base: Base auxiliary container class.
    :param relationship: Relationship.
    :param qual_name: Qualified name.
    :param module: Module.
    :param unique_descriptor_name: Attribute name for unique descriptor.
    :param dct: Members dictionary.
    :return: Generated auxiliary container subclass.
    :raises TypeError: Invalid 'qual_name' parameter type.
    :raises TypeError: Invalid 'module' parameter type.
    """

    # 'qual_name'
    with ReraiseContext(TypeError, "'qual_name' parameter"):
        assert_is_instance(qual_name, string_types + (type(None),))

    # 'module'
    with ReraiseContext(TypeError, "'module' parameter"):
        assert_is_instance(module, string_types + (type(None),))
    module = module or None

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

    # Add unique descriptor.
    if unique_descriptor_name:
        dct_copy[unique_descriptor_name] = UniqueDescriptor()

    return cast(
        "_A",
        make_base_cls(
            base=base,
            qual_name=qual_name,
            module=module,
            dct=dct_copy,
        ),
    )


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
    :raises TypeError: Invalid 'module' parameter type.
    :raises ValueError: Invalid 'types' parameter value.
    :raises TypeError: Invalid 'types' parameter type.
    :raises ValueError: Did not provide any 'types' but 'checked' is True.
    :raises ValueError: Invalid 'factory' parameter value.
    :raises TypeError: Invalid 'factory' parameter type.
    :raises ValueError: Provided 'serializer' but 'serialized' is False.
    :raises ValueError: Provided 'deserializer' but 'serialized' is False.
    :raises ValueError: Invalid 'serializer' parameter value.
    :raises TypeError: Invalid 'serializer' parameter type.
    :raises ValueError: Invalid 'deserializer' parameter value.
    :raises TypeError: Invalid 'deserializer' parameter type.
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
        checked=None,  # type: Optional[bool]
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
        serialized=True,  # type: bool
        serializer=None,  # type: LazyFactory
        deserializer=None,  # type: LazyFactory
        represented=True,  # type: bool
    ):
        # type: (...) -> None

        # 'module'
        with ReraiseContext(TypeError, "'module' parameter"):
            assert_is_instance(module, string_types + (type(None),))
        module = module or None

        # 'types' and 'checked'
        with ReraiseContext((ValueError, TypeError), "'types' parameter"):
            types = format_types(types, module=module)
        if not types:
            if checked:
                error = "did not provide any 'types' but 'checked' is True"
                raise ValueError(error)
            if checked is None:
                checked = False
        else:
            if checked is None:
                checked = True
        checked = bool(checked)

        # 'factory'
        with ReraiseContext((ValueError, TypeError), "'factory' parameter"):
            factory = format_factory(factory, module=module)

        # 'serialized', 'serializer', and 'deserializer'
        if not serialized:
            if serializer is not None:
                error = "provided 'serializer' but 'serialized' is False"
                raise ValueError(error)
            if deserializer is not None:
                error = "provided 'deserializer' but 'serialized' is False"
                raise ValueError(error)
        else:
            if serializer is not None:
                with ReraiseContext((ValueError, TypeError), "'serializer' parameter"):
                    serializer = format_factory(serializer, module=module)
            if deserializer is not None:
                with ReraiseContext(
                    (ValueError, TypeError), "'deserializer' parameter"
                ):
                    deserializer = format_factory(deserializer, module=module)

        self.__hash = None  # type: Optional[int]
        self.__types = types
        self.__subtypes = bool(subtypes)
        self.__checked = bool(checked)
        self.__module = module
        self.__factory = factory
        self.__serialized = bool(serialized)
        self.__serializer = serializer
        self.__deserializer = deserializer
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

    @overload
    def __get__(self, instance, owner):
        # type: (None, Type[BaseStructure]) -> UniqueDescriptor
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (BaseStructure, Type[BaseStructure]) -> int
        pass

    def __get__(self, instance, owner):
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


# noinspection PyTypeChecker
_BS = TypeVar("_BS", bound="BaseStructure")


class BaseStructure(
    with_metaclass(BaseStructureMeta, BaseHashable, BaseProtectedCollection[T])
):
    """
    Base structure.

      - Is hashable.
      - Is a protected collection.
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

    @staticmethod
    @final
    def __deserialize_value(
        serialized,  # type: Any
        location,  # type: Any
        relationship,  # type: BaseRelationship
        serializable_structure_types,  # type: Tuple[Type[BaseStructure], ...]
        class_name,  # type: str
        **kwargs  # type: Any
    ):
        # type: (...) -> Any
        """
        Deserialize value for location with built-in serializer.

        :param serialized: Serialized value.
        :param location: Location.
        :param relationship: Relationship.
        :param serializable_structure_types: Serializable structure types.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized value.
        :raises TypeError: Can't deserialize value due to ambiguous types.
        """

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
                serializable_structure_types
            )  # type: Optional[Type[BaseStructure]]
            if single_structure_type is not None:
                return single_structure_type.deserialize(serialized, **kwargs)

            # Complex type (dict or list).
            single_complex_type = relationship.get_single_exact_type(
                (dict, list)
            )  # type: Optional[Union[Type[Dict], Type[List]]]
            if single_complex_type is None:
                error = (
                    "can't deserialize '{}' object as a value of '{}' since "
                    "relationship{} defines none or ambiguous types"
                ).format(
                    type(serialized).__name__,
                    class_name,
                    " at location {}".format(location) if location is not None else "",
                )
                raise TypeError(error)

        # Return type-check deserialized value.
        return relationship.fabricate_value(serialized, factory=False)

    @staticmethod
    @final
    def __serialize_value(
        value,  # type: Any
        relationship,  # type: BaseRelationship
        serializable_structure_types,  # type: Tuple[Type[BaseStructure], ...]
        **kwargs  # type: Any
    ):
        # type: (...) -> Any
        """
        Serialize value for location with built-in serializer.

        :param value: Value.
        :param relationship: Relationship.
        :param serializable_structure_types: Serializable structure types.
        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized value.
        """

        # Structure type.
        if isinstance(value, serializable_structure_types):
            serialized_value = value.serialize(**kwargs)

            # Escape keys.
            if type(serialized_value) is dict:
                serialized_value = _escape_serialized_class(serialized_value)

            # Ambiguous type, serialize with class path.
            single_structure_type = relationship.get_single_exact_type(
                serializable_structure_types
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
        :raises KeyError: Invalid location.
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
        :raises ValueError: Keyword arguments contain reserved keys.
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

        # Built-in deserializer.
        deserializer = lambda: cls.__deserialize_value(
            serialized,
            location,
            relationship,
            cls._serializable_structure_types,
            cls.__fullname__,
        )
        if relationship.deserializer is None:
            return deserializer()

        # Check kwargs for reserved keys.
        if "super" in kwargs:
            error = "can't pass reserved keyword argument 'super' to deserializers"
            raise ValueError(error)

        # Custom deserializer.
        kwargs = dict(kwargs)
        kwargs["super"] = deserializer
        if type(serialized) is dict:
            serialized = _unescape_serialized_class(serialized)
        value = run_factory(
            relationship.deserializer, args=(serialized,), kwargs=kwargs
        )
        return relationship.fabricate_value(value, factory=False)

    @final
    def serialize_value(self, value, location=None, **kwargs):
        # type: (Any, Any, Any) -> Any
        """
        Serialize value for location.

        :param value: Value.
        :param location: Location.
        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized value.
        :raises ValueError: Keyword arguments contain reserved keys.
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

        # Built-in serializer
        serializer = lambda: self.__serialize_value(
            value, relationship, cls._serializable_structure_types, **kwargs
        )
        if relationship.serializer is None:
            return serializer()

        # Check kwargs for reserved keys.
        if "super" in kwargs:
            error = "can't pass reserved keyword argument 'super' to serializers"
            raise ValueError(error)

        # Custom serializer.
        kwargs = dict(kwargs)
        kwargs["super"] = serializer
        serialized_value = run_factory(
            relationship.serializer, args=(value,), kwargs=kwargs
        )
        if type(serialized_value) is dict:
            serialized_value = _escape_serialized_class(serialized_value)
        return serialized_value

    @classmethod
    @abstractmethod
    def deserialize(cls, serialized, **kwargs):
        # type: (Type[_BS], Any, Any) -> _BS
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


# noinspection PyAbstractClass
class BaseInteractiveStructure(BaseStructure[T], BaseInteractiveCollection[T]):
    """Base interactive structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableStructure(BaseStructure[T], BaseMutableCollection[T]):
    """Base mutable structure."""

    __slots__ = ()


class BaseAttributeMeta(BaseMeta):
    """Metaclass for :class:`BaseAttribute`."""

    @property
    @abstractmethod
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """Relationship type."""
        return BaseRelationship


class BaseAttribute(with_metaclass(BaseAttributeMeta, Base, Generic[T])):
    """
    Base attribute descriptor.

    :param relationship: Relationship.
    :param default: Default value.
    :param default_factory: Default value factory.
    :param module: Optional module path to use in case partial paths are provided.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :raises TypeError: Invalid 'relationship' parameter type.
    :raises TypeError: Invalid 'module' parameter type.
    :raises ValueError: Can't specify both 'default' and 'default_factory' arguments.
    :raises TypeError: Invalid 'default_factory' parameter type.
    :raises TypeError: Invalid 'default_factory' parameter value.
    :raises ValueError: Can't be 'required' and 'deletable' at the same time.
    :raises ValueError: Can't be 'finalized' and 'abstracted' at the same time.
    """

    __slots__ = (
        "__relationship",
        "__default",
        "__default_factory",
        "__module",
        "__required",
        "_changeable",
        "_deletable",
        "__finalized",
        "__abstracted",
        ABSTRACT_TAG,
        FINAL_METHOD_TAG,
    )

    def __init__(
        self,
        relationship=BaseRelationship(),  # type: BaseRelationship
        default=MISSING,  # type: Any
        default_factory=None,  # type: LazyFactory
        module=None,  # type: Optional[str]
        required=True,  # type: bool
        changeable=True,  # type: bool
        deletable=False,  # type: bool
        finalized=False,  # type: bool
        abstracted=False,  # type: bool
    ):
        # type: (...) -> None
        cls = type(self)

        # 'relationship'
        with ReraiseContext(TypeError, "'relationship' parameter"):
            assert_is_instance(relationship, cls._relationship_type, subtypes=False)

        # 'module'
        if module is None:
            module = relationship.module
        else:
            with ReraiseContext(TypeError, "'module' parameter"):
                assert_is_instance(module, string_types + (type(None),))
            module = module or None

        # 'default' and 'default_factory'
        if default is not MISSING and default_factory is not None:
            error = "can't specify both 'default' and 'default_factory' arguments"
            raise ValueError(error)
        with ReraiseContext((ValueError, TypeError), "'default_factory' parameter"):
            default_factory = format_factory(default_factory, module=module)

        # 'deletable' and 'required'
        if deletable and required:
            error = "can't be 'required' and 'deletable' at the same time"
            raise ValueError(error)

        # 'finalized' and 'abstracted'
        if finalized and abstracted:
            error = "can't be 'finalized' and 'abstracted' at the same time"
            raise ValueError(error)

        self.__relationship = relationship
        self.__default = default
        self.__default_factory = default_factory
        self.__module = module
        self.__required = bool(required)
        self._changeable = bool(changeable)
        self._deletable = bool(deletable)
        self.__finalized = bool(finalized)
        self.__abstracted = bool(abstracted)

        if finalized:
            setattr(self, FINAL_METHOD_TAG, True)
        if abstracted:
            setattr(self, ABSTRACT_TAG, True)

    @overload
    def __get__(self, instance, owner):
        # type: (None, Type[BaseAttributeStructure]) -> BaseAttribute[T]
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (BaseAttributeStructure, Type[BaseAttributeStructure]) -> T
        pass

    def __get__(self, instance, owner):
        """
        Get attribute value when accessing from valid instance or this descriptor
        otherwise.

        :param instance: Instance.
        :param owner: Owner class.
        :return: Value or this descriptor.
        """
        if instance is not None:
            attribute_type = getattr(type(instance), "_attribute_type", None)
            if attribute_type is not None and isinstance(self, attribute_type):
                return self.get_value(instance)
        return self

    @final
    def __hash__(self):
        # type: () -> int
        """
        Get hash based on object id.

        :return: Hash based on object id.
        """
        return hash(id(self))

    @final
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare with another object for identity.

        :param other: Another object.
        :return: True if the same object.
        """
        return other is self

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
            "relationship": self.relationship,
            "default": self.default,
            "default_factory": import_factory(self.default_factory),
            "module": self.module,
            "required": self.required,
            "changeable": self.changeable,
            "deletable": self.deletable,
            "finalized": self.finalized,
            "abstracted": self.abstracted,
        }

    def get_name(self, instance):
        # type: (BaseAttributeStructure) -> str
        """
        Get attribute name.

        :param instance: Instance.
        :return: Attribute Name.
        """
        cls = type(instance)
        return cls._attribute_names[self]

    def get_value(self, instance):
        # type: (BaseAttributeStructure) -> T
        """
        Get attribute value.

        :param instance: Instance.
        :return: Attribute Value.
        :raises AttributeError: Could not get value.
        """
        name = self.get_name(instance)
        try:
            value = instance[name]
        except KeyError:
            error = "attribute '{}' of '{}' has no value set".format(
                name, type(instance).__fullname__
            )
            if getattr(instance, INITIALIZING_TAG, False):
                error += " (instance hasn't finished initializing)"
            exc = AttributeError(error)
            raise_from(exc, None)
            raise exc
        else:
            return value

    @final
    def fabricate_default_value(self, **kwargs):
        # type: (Any, Any) -> Any
        """
        Fabricate default value.

        :param kwargs: Keyword arguments to be passed to the factories.
        :return: Fabricated value.
        :raises ValueError: No default or default factory.
        """
        default = self.__default
        if self.__default_factory is not None:
            default = run_factory(self.__default_factory, kwargs=kwargs)
        if default is MISSING:
            error = "attribute has no valid 'default' or 'default factory'"
            raise ValueError(error)
        return self.__relationship.fabricate_value(default, **kwargs)

    @property
    def relationship(self):
        # type: () -> BaseRelationship
        """Relationship."""
        return self.__relationship

    @property
    def default(self):
        # type: () -> Any
        """Default value."""
        return self.__default

    @property
    def default_factory(self):
        # type: () -> LazyFactory
        """Default value factory."""
        return self.__default_factory

    @property
    def module(self):
        # type: () -> Optional[str]
        """Optional module path to use in case partial paths are provided."""
        return self.__module

    @property
    def required(self):
        # type: () -> bool
        """Whether attribute is required to have a value or not."""
        return self.__required

    @property
    def changeable(self):
        # type: () -> bool
        """Whether attribute value can be changed."""
        return self._changeable

    @property
    def deletable(self):
        # type: () -> bool
        """Whether attribute value can be deleted."""
        return self._deletable

    @property
    def finalized(self):
        # type: () -> bool
        """If True, attribute can't be overridden by subclasses."""
        return self.__finalized

    @property
    def abstracted(self):
        # type: () -> bool
        """If True, attribute needs to be overridden by subclasses."""
        return self.__abstracted

    @property
    def has_default(self):
        # type: () -> bool
        """Whether attribute has a default value or a default factory."""
        return self.default is not MISSING or self.default_factory is not None


class BaseAttributeStructureMeta(BaseStructureMeta):
    """Metaclass for :class:`BaseAttributeStructure`."""

    __attributes = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseAttributeStructureMeta, Mapping[str, BaseAttribute]]
    __attribute_names = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseAttributeStructureMeta, Mapping[BaseAttribute, str]]

    def __init__(cls, name, bases, dct):
        # type: (str, Tuple[Type, ...], Dict[str, Any]) -> None
        super(BaseAttributeStructureMeta, cls).__init__(name, bases, dct)

        # Get attribute type.
        try:
            attribute_type = cls._attribute_type  # type: Optional[Type[BaseAttribute]]
        except NotImplementedError:
            attribute_type = None

        # Store attributes.
        attributes = {}
        if attribute_type is not None:
            for base in reversed(getmro(cls)):
                for member_name, member in iteritems(base.__dict__):
                    if isinstance(member, attribute_type):
                        attributes[member_name] = member
                    elif member_name in attributes:
                        del attributes[member_name]

        # Store attribute names.
        attribute_names = {}
        if attribute_type is not None:
            for attribute_name, attribute in iteritems(attributes):
                attribute_names[attribute] = attribute_name

        type(cls).__attributes[cls] = DictState(attributes)
        type(cls).__attribute_names[cls] = DictState(attribute_names)

    @property
    @abstractmethod
    def _attribute_type(cls):
        # type: () -> Type[BaseAttribute]
        """Attribute type."""
        raise NotImplementedError()

    @property
    def _attributes(cls):
        # type: () -> Mapping[str, BaseAttribute]
        """Attributes mapped by name."""
        return type(cls).__attributes[cls]

    @property
    def _attribute_names(cls):
        # type: () -> Mapping[Any, str]
        """Names mapped by attribute."""
        return type(cls).__attribute_names[cls]


# noinspection PyTypeChecker
_BAS = TypeVar("_BAS", bound="BaseAttributeStructure")


class BaseAttributeStructure(
    with_metaclass(BaseAttributeStructureMeta, BaseStructure[str])
):
    """
    Base attribute structure.

      - Holds values in attributes defined by descriptors.
      - Can be cast into a dictionary.
    """

    __slots__ = ()

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_mapping_repr(
            dict(
                (n, v)
                for n, v in iteritems(self._state)
                if type(self)._get_relationship(n).represented
            ),
            prefix="{}(".format(type(self).__fullname__),
            template="{key}={value}",
            suffix=")",
            key_repr=str,
        )

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
    def _get_relationship(cls, location):
        # type: (str) -> BaseRelationship
        """
        Get relationship at location (attribute name).

        :param location: Location (attribute name).
        :return: Relationship.
        :raises KeyError: Attribute does not exist.
        """
        return cls._get_attribute(location).relationship

    @classmethod
    def _get_attribute(cls, name):
        # type: (str) -> BaseAttribute
        """
        Get attribute by name.

        :param name: Attribute name.
        :return: Attribute.
        :raises KeyError: Attribute does not exist.
        """
        return cls._attributes[name]

    @abstractmethod
    def _set(self, name, value):
        # type: (_BAS, str, Any) -> _BAS
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        raise NotImplementedError()

    @abstractmethod
    def _delete(self, name):
        # type: (_BAS, str) -> _BAS
        """
        Delete attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises KeyError: Attribute does not exist or has no value.
        :raises AttributeError: Attribute is not deletable.
        """
        raise NotImplementedError()

    @overload
    @abstractmethod
    def _update(self, __m, **kwargs):
        # type: (_BAS, Mapping[str, Any], Any) -> _BAS
        pass

    @overload
    @abstractmethod
    def _update(self, __m, **kwargs):
        # type: (_BAS, Iterable[Tuple[str, Any]], Any) -> _BAS
        pass

    @overload
    @abstractmethod
    def _update(self, **kwargs):
        # type: (_BAS, Any) -> _BAS
        pass

    @abstractmethod
    def _update(self, *args, **kwargs):
        """
        Update multiple attribute values.
        Same parameters as :meth:`dict.update`.

        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        raise NotImplementedError()

    @final
    def keys(self):
        # type: () -> SetState[str]
        """
        Get names of the attributes with values.

        :return: Attribute names.
        """
        return SetState(self._state.keys())

    @final
    def find_with_attributes(self, **attributes):
        # type: (Any) -> VT
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        return self._state.find_with_attributes(**attributes)

    @property
    @abstractmethod
    def _state(self):
        # type: () -> DictState[str, Any]
        """Internal state."""
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseInteractiveAttributeStructure(
    BaseAttributeStructure, BaseInteractiveStructure[str]
):
    """Base interactive attribute structure."""

    __slots__ = ()

    @final
    def set(self, name, value):
        # type: (_BAS, str, Any) -> _BAS
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        return self._set(name, value)

    @final
    def delete(self, name):
        # type: (_BAS, str) -> _BAS
        """
        Delete attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises KeyError: Attribute does not exist or has no value.
        :raises AttributeError: Attribute is not deletable.
        """
        return self._delete(name)

    @overload
    def update(self, __m, **kwargs):
        # type: (_BAS, Mapping[str, Any], Any) -> _BAS
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (_BAS, Iterable[Tuple[str, Any]], Any) -> _BAS
        pass

    @overload
    def update(self, **kwargs):
        # type: (_BAS, Any) -> _BAS
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update multiple attribute values.
        Same parameters as :meth:`dict.update`.

        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        return self._update(*args, **kwargs)


# noinspection PyAbstractClass
class BaseMutableAttributeStructure(BaseAttributeStructure, BaseMutableStructure[str]):
    """Base mutable attribute structure."""

    __slots__ = ()

    @final
    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :return: Value.
        :raises KeyError: Attribute does not exist.
        """
        self._set(name, value)

    @final
    def __delitem__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.

        :param name: Attribute name.
        :raises KeyError: Attribute does not exist or has no value.
        """
        self._delete(name)

    @final
    def delete(self, name):
        # type: (str) -> None
        """
        Delete attribute value.

        :param name: Attribute name.
        :raises KeyError: Attribute does not exist or has no value.
        """
        self._delete(name)

    @final
    def set(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :raises KeyError: Attribute does not exist.
        """
        self._set(name, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (Mapping[str, Any], Any) -> None
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (Iterable[Tuple[str, Any]], Any) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (Any) -> None
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update multiple attribute values.
        Same parameters as :meth:`dict.update`.

        :raises KeyError: Attribute does not exist.
        """
        self._update(*args, **kwargs)


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


# noinspection PyAbstractClass
class BaseAuxiliaryStructure(
    with_metaclass(BaseAuxiliaryStructureMeta, BaseStructure[T])
):
    """Structure with a single relationship for all locations."""

    __slots__ = ()

    _relationship = (
        abstract_member()
    )  # type: Union[Type[AbstractMember], BaseRelationship]
    """Relationship for all locations."""

    def find_with_attributes(self, **attributes):
        # type: (Any) -> VT
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        return self._state.find_with_attributes(**attributes)

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


# noinspection PyAbstractClass
class BaseInteractiveAuxiliaryStructure(
    BaseAuxiliaryStructure[T],
    BaseInteractiveStructure[T],
):
    """Base interactive auxiliary structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableAuxiliaryStructure(
    BaseAuxiliaryStructure[T],
    BaseMutableStructure[T],
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


# noinspection PyAbstractClass
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
        BaseAuxiliaryStructure[KT],
        BaseProtectedDict[KT, VT],
    )
):
    """Base dictionary structure."""

    __slots__ = ()

    _key_relationship = (
        abstract_member()
    )  # type: Union[Type[AbstractMember], KeyRelationship]
    """Relationship for the keys."""

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        if type(self)._relationship.represented:
            return custom_mapping_repr(
                self._state,
                prefix="{}({{".format(type(self).__fullname__),
                suffix="})",
            )
        else:
            return "<{}>".format(type(self).__fullname__)

    @final
    def __reversed__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        """
        return reversed(self._state)

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
    def get(self, key, fallback=None):
        # type: (KT, Any) -> Union[VT, Any]
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._state.get(key, fallback)

    @final
    def iteritems(self):
        # type: () -> Iterator[Tuple[KT, VT]]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key, value in iteritems(self._state):
            yield key, value

    @final
    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in iterkeys(self._state):
            yield key

    @final
    def itervalues(self):
        # type: () -> Iterator[VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in itervalues(self._state):
            yield value

    @property
    @abstractmethod
    def _state(self):
        # type: () -> DictState[KT, VT]
        """Internal state."""
        raise NotImplementedError()


class BaseInteractiveDictStructure(
    BaseDictStructure[KT, VT],
    BaseInteractiveAuxiliaryStructure[KT],
    BaseInteractiveDict[KT, VT],
):
    """Base interactive dictionary structure."""

    __slots__ = ()


class BaseMutableDictStructure(
    BaseDictStructure[KT, VT],
    BaseMutableAuxiliaryStructure[KT],
    BaseMutableDict[KT, VT],
):
    """Base mutable dictionary structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseListStructureMeta(BaseAuxiliaryStructureMeta):
    """Metaclass for :class:`ListStructure`."""


class BaseListStructure(
    with_metaclass(
        BaseListStructureMeta,
        BaseAuxiliaryStructure[T],
        BaseProtectedList[T],
    )
):
    """Base list structure."""

    __slots__ = ()

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        if type(self)._relationship.represented:
            return custom_iterable_repr(
                self._state,
                prefix="{}([".format(type(self).__fullname__),
                suffix="])",
            )
        else:
            return "<{}>".format(type(self).__fullname__)

    @final
    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._state)

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
    def count(self, value):
        # type: (Any) -> int
        """
        Count number of occurrences of a value.

        :return: Number of occurrences.
        """
        return self._state.count(value)

    @final
    def index(self, value, start=None, stop=None):
        # type: (Any, Optional[int], Optional[int]) -> int
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :return: Index of value.
        :raises ValueError: Provided stop but did not provide start.
        """
        return self._state.index(value, start=start, stop=stop)

    @final
    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return self._state.resolve_index(index, clamp=clamp)

    @final
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return self._state.resolve_continuous_slice(slc)

    @property
    @abstractmethod
    def _state(self):
        # type: () -> ListState[T]
        """Internal state."""
        raise NotImplementedError()


class BaseInteractiveListStructure(
    BaseListStructure[T],
    BaseInteractiveAuxiliaryStructure[T],
    BaseInteractiveList[T],
):
    """Base interactive list structure."""

    __slots__ = ()


class BaseMutableListStructure(
    BaseListStructure[T],
    BaseMutableAuxiliaryStructure[T],
    BaseMutableList[T],
):
    """Base mutable list structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseSetStructureMeta(BaseAuxiliaryStructureMeta):
    """Metaclass for :class:`SetStructure`."""


class BaseSetStructure(
    with_metaclass(
        BaseSetStructureMeta,
        BaseAuxiliaryStructure[T],
        BaseProtectedSet[T],
    )
):
    """Base set structure."""

    __slots__ = ()

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        if type(self)._relationship.represented:
            return custom_iterable_repr(
                self._state,
                prefix="{}([".format(type(self).__fullname__),
                suffix="])",
                sorting=True,
                sort_key=lambda v: hash(v),
            )
        else:
            return "<{}>".format(type(self).__fullname__)

    @final
    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._state)

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

    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return self._state.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._state.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._state.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return self._state.intersection(iterable)

    def difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return self._state.difference(iterable)

    def inverse_difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        return self._state.inverse_difference(iterable)

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return self._state.symmetric_difference(iterable)

    def union(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return self._state.union(iterable)

    @property
    @abstractmethod
    def _state(self):
        # type: () -> SetState[T]
        """Internal state."""
        raise NotImplementedError()


class BaseInteractiveSetStructure(
    BaseSetStructure[T],
    BaseInteractiveAuxiliaryStructure[T],
    BaseInteractiveSet[T],
):
    """Base interactive set structure."""

    __slots__ = ()


class BaseMutableSetStructure(
    BaseSetStructure[T],
    BaseMutableAuxiliaryStructure[T],
    BaseMutableSet[T],
):
    """Base mutable set structure."""

    __slots__ = ()
