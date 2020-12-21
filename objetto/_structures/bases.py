# -*- coding: utf-8 -*-
"""State-carrying structures."""

from abc import abstractmethod
from inspect import getmro
from re import sub as re_sub
from typing import TYPE_CHECKING, TypeVar, cast, overload
from weakref import WeakKeyDictionary

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, string_types, with_metaclass

from .._bases import (
    FINAL_METHOD_TAG,
    Base,
    BaseHashable,
    BaseInteractiveCollection,
    BaseMeta,
    BaseMutableCollection,
    BaseProtectedCollection,
    final,
    make_base_cls,
)
from .._exceptions import BaseObjettoException
from .._states import BaseState
from ..utils.custom_repr import custom_mapping_repr
from ..utils.factoring import format_factory, import_factory, run_factory
from ..utils.lazy_import import get_path, import_path
from ..utils.recursive_repr import recursive_repr
from ..utils.reraise_context import ReraiseContext
from ..utils.type_checking import (
    assert_is_instance,
    format_types,
    get_type_names,
    import_types,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        List,
        Mapping,
        MutableMapping,
        Optional,
        Tuple,
        Type,
        Union,
    )

    from ..utils.factoring import LazyFactory
    from ..utils.type_checking import LazyTypes, LazyTypesTuple

__all__ = [
    "make_auxiliary_cls",
    "SerializationError",
    "BaseRelationship",
    "UniqueDescriptor",
    "unique_descriptor",
    "BaseStructureMeta",
    "BaseStructure",
    "BaseInteractiveStructure",
    "BaseMutableStructure",
    "BaseAuxiliaryStructureMeta",
    "BaseAuxiliaryStructure",
    "BaseInteractiveAuxiliaryStructure",
    "BaseMutableAuxiliaryStructure",
]


_SERIALIZED_CLASS_KEY = "__class__"
_ESCAPED_SERIALIZED_CLASS_KEY = "\\__class__"
_SERIALIZED_VALUE_KEY = "__state__"


T = TypeVar("T")  # Any type.


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
        assert_is_instance(qual_name, string_types + (None,))

    # 'module'
    with ReraiseContext(TypeError, "'module' parameter"):
        assert_is_instance(module, string_types + (None,))
    module = module or None

    # Generate default name based on relationship types.
    if qual_name is None:
        type_names = get_type_names(
            tuple(t for t in relationship.types if t not in (type(None), None))
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


class SerializationError(BaseObjettoException):
    """
    Failed to serialize/deserialize structure.

    Inherits from:
      - :class:`objetto.bases.BaseObjettoException`
    """


class BaseRelationship(BaseHashable):
    """
    Relationship between a structure and its values.

    Inherits from:
      - :class:`objetto.bases.BaseHashable`

    Inherited by:
      - :class:`objetto.data.DataRelationship`
      - :class:`objetto.objects.Relationship`

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
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
            assert_is_instance(module, string_types + (None,))
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
        self.__checked = checked
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
        :rtype: int
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
        :rtype: bool
        """
        if self is other:
            return True
        if type(self) is not type(other):
            return False
        assert isinstance(other, BaseRelationship)
        return self.to_dict() == other.to_dict()

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
            sorting=True,
            key_repr=str,
        )

    def __str__(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        :rtype: str
        """
        return self.__repr__()

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[str, Any]
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
        :type types: str or type or None or tuple[str or type or None]

        :return: Single exact type that is a subclass of one of provided base types.
        :rtype: type or None
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
        :type factory: bool

        :param kwargs: Keyword arguments to be passed to the factory.

        :return: Fabricated value.
        """
        if factory and self.factory is not None:
            value = run_factory(self.factory, args=(value,), kwargs=kwargs)
        if self.types and self.checked:
            assert_is_instance(value, self.types, subtypes=self.subtypes)
        return value

    @property
    @final
    def types(self):
        # type: () -> LazyTypesTuple
        """
        Types.

        :rtype: tuple[str or type]
        """
        return self.__types

    @property
    @final
    def subtypes(self):
        # type: () -> bool
        """
        Whether to accept subtypes.

        :rtype: bool
        """
        return self.__subtypes

    @property
    @final
    def checked(self):
        # type: () -> bool
        """
        Whether to perform runtime type check.

        :rtype: bool
        """
        return self.__checked

    @property
    @final
    def module(self):
        # type: () -> Optional[str]
        """
        Module path for lazy types/factories.

        :rtype: str or None
        """
        return self.__module

    @property
    @final
    def factory(self):
        # type: () -> LazyFactory
        """
        Value factory.

        :rtype: str or collections.abc.Callable or None
        """
        return self.__factory

    @property
    @final
    def serialized(self):
        # type: () -> bool
        """
        Whether should be serialized.

        :rtype: bool
        """
        return self.__serialized

    @property
    @final
    def serializer(self):
        # type: () -> LazyFactory
        """
        Custom serializer.

        :rtype: str or collections.abc.Callable or None
        """
        return self.__serializer

    @property
    @final
    def deserializer(self):
        # type: () -> LazyFactory
        """
        Custom deserializer.

        :rtype: str or collections.abc.Callable or None
        """
        return self.__deserializer

    @property
    @final
    def represented(self):
        # type: () -> bool
        """
        Whether should be represented.

        :rtype: bool
        """
        return self.__represented

    @property
    @final
    def passthrough(self):
        # type: () -> bool
        """
        Whether does not perform type checks and has no factory.

        :rtype: bool
        """
        return (not self.types or not self.checked) and self.factory is None


# noinspection PyTypeChecker
_UD = TypeVar("_UD", bound="UniqueDescriptor")


@final
class UniqueDescriptor(Base):
    """
    Descriptor to be used on :class:`objetto.bases.BaseStructure` classes.
    When used, the object ID will be the hash, and the equality method will compare by
    identity instead of by values.
    If accessed through an instance, the descriptor will return the object ID.

    Inherits from:
      - :class:`objetto.bases.Base`
    """

    __slots__ = (FINAL_METHOD_TAG,)

    def __init__(self):
        setattr(self, FINAL_METHOD_TAG, True)

    @overload
    def __get__(self, instance, owner):
        # type: (_UD, None, Type[BaseStructure]) -> _UD
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (BaseStructure, Type[BaseStructure]) -> int
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (_UD, object, type) -> _UD
        pass

    def __get__(self, instance, owner):
        """
        Get object hash when accessing from instance or this descriptor otherwise.

        :param instance: Instance.
        :type instance: objetto.bases.BaseStructure or None

        :param owner: Owner class.
        :type owner: type[objetto.bases.BaseStructure] or None

        :return: Object hash based on object ID or this descriptor.
        :rtype: int or objetto.objects.UniqueDescriptor or objetto.data.UniqueDescriptor
        """
        if instance is not None:
            cls = type(instance)
            if getattr(cls, "_unique_descriptor", None) is self:
                return hash(id(instance))
        return self


# noinspection PyAbstractClass
def unique_descriptor():
    # type: () -> UniqueDescriptor
    """
    Descriptor to be used when declaring an :class:`objetto.objects.Object` or an
    :class:`objetto.data.InteractiveData` container class.
    When used, the hash for the container will be the object ID, and the equality method
    will compare by identity instead of values.
    If accessed through an instance, the descriptor will return the unique hash based
    on the object's ID.

    .. code:: python

        >>> from objetto import Application, Object, unique_descriptor

        >>> class UniqueObject(Object):
        ...     unique_hash = unique_descriptor()
        ...
        >>> app = Application()
        >>> obj = UniqueObject(app)
        >>> obj.unique_hash == hash(id(obj))
        True

    :return: Unique descriptor.
    :rtype: objetto.objects.UniqueDescriptor or objetto.data.UniqueDescriptor
    """
    return UniqueDescriptor()


class BaseStructureMeta(BaseMeta):
    """
    Metaclass for :class:`objetto.bases.BaseStructure`.

    Inherits from:
      - :class:`objetto.bases.BaseMeta`

    Inherited by:
      - :class:`objetto.bases.BaseAuxiliaryStructureMeta`
      - :class:`objetto.bases.BaseAttributeStructureMeta`
      - :class:`objetto.bases.BaseDataMeta`
      - :class:`objetto.bases.BaseObjectMeta`

    Features:
      - Support for `unique descriptors <objetto.objects.unique_descriptor>`_.
      - Defines serializable structure type.
    """

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
        unique_descriptor_ = None  # type: Optional[UniqueDescriptor]
        if unique_descriptors:
            unique_descriptor_name, unique_descriptor_ = next(
                iteritems(unique_descriptors)
            )
        type(cls).__unique_descriptor_name[cls] = unique_descriptor_name
        type(cls).__unique_descriptor[cls] = unique_descriptor_

    @property
    @final
    def _unique_descriptor_name(cls):
        # type: () -> Optional[str]
        """
        Unique descriptor name or `None`.

        :rtype: str or None
        """
        return type(cls).__unique_descriptor_name[cls]

    @property
    @final
    def _unique_descriptor(cls):
        # type: () -> Optional[UniqueDescriptor]
        """
        Unique descriptor or `None`.

        :rtype: objetto.objects.UniqueDescriptor or objetto.data.UniqueDescriptor or \
None
        """
        return type(cls).__unique_descriptor[cls]

    @property
    @abstractmethod
    def _serializable_structure_types(cls):
        # type: () -> Tuple[Type[BaseStructure], ...]
        """
        Serializable structure types.

        :rtype: tuple[type[objetto.bases.BaseStructure]]
        """
        raise NotImplementedError()

    @property
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """
        Relationship type.

        :rtype: type[objetto.bases.BaseRelationship]
        """
        return BaseRelationship


# noinspection PyTypeChecker
_BS = TypeVar("_BS", bound="BaseStructure")


class BaseStructure(
    with_metaclass(BaseStructureMeta, BaseHashable, BaseProtectedCollection[T])
):
    """
    Base structure.

    Metaclass:
      - :class:`objetto.bases.BaseStructureMeta`

    Inherits from:
      - :class:`objetto.bases.BaseHashable`
      - :class:`objetto.bases.BaseProtectedCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveStructure`
      - :class:`objetto.bases.BaseMutableStructure`
      - :class:`objetto.bases.BaseAuxiliaryStructure`
      - :class:`objetto.bases.BaseData`
      - :class:`objetto.bases.BaseObject`

    Features:
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
        :rtype: int
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
        :rtype: bool
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

    # @abstractmethod (commented out due to a PyCharm bug)
    def _hash(self):
        # type: () -> int
        """
        **Abstract**

        Get hash.

        :return: Hash.
        :rtype: int

        :raises RuntimeError: Abstract method not implemented by subclasses.
        """
        # raise NotImplementedError
        raise RuntimeError()

    # @abstractmethod (commented out due to a PyCharm bug)
    def _eq(self, other):
        # type: (Any) -> bool
        """
        **Abstract**

        Compare with another object for equality.

        :param other: Another object.

        :return: True if equal.
        :rtype: bool

        :raises RuntimeError: Abstract method not implemented by subclasses.
        """
        # raise NotImplementedError
        raise RuntimeError()

    @classmethod
    @abstractmethod
    def _get_relationship(cls, location):
        # type: (Any) -> BaseRelationship
        """
        Get relationship at location.

        :param location: Location.
        :type location: collections.abc.Hashable

        :return: Relationship.
        :rtype: objetto.bases.BaseRelationship

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
        :type location: collections.abc.Hashable

        :param kwargs: Keyword arguments to be passed to the deserializers.

        :return: Deserialized value.

        :raises objetto.exceptions.SerializationError: Can't deserialize value.
        :raises ValueError: Keyword arguments contain reserved keys.
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
            raise SerializationError(error)

        # Built-in deserializer.
        deserializer = lambda: cls.__deserialize_value(
            serialized,
            location,
            relationship,
            cls._serializable_structure_types,
            cls.__fullname__,
            **kwargs
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
        :type location: collections.abc.Hashable

        :param kwargs: Keyword arguments to be passed to the serializers.

        :return: Serialized value.

        :raises objetto.exceptions.SerializationError: Can't serialize value.
        :raises ValueError: Keyword arguments contain reserved keys.
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
            raise SerializationError(error)

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
        :rtype: objetto.bases.BaseStructure

        :raises objetto.exceptions.SerializationError: Can't deserialize.
        """
        raise NotImplementedError()

    @abstractmethod
    def serialize(self, **kwargs):
        # type: (Any) -> Any
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.

        :return: Serialized.

        :raises objetto.exceptions.SerializationError: Can't serialize.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def _state(self):
        # type: () -> BaseState
        """
        State.

        :rtype: objetto.bases.BaseState
        """
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseInteractiveStructure(BaseStructure[T], BaseInteractiveCollection[T]):
    """
    Base interactive structure.

    Inherits from:
      - :class:`objetto.bases.BaseStructure`
      - :class:`objetto.bases.BaseInteractiveCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveAuxiliaryStructure`
      - :class:`objetto.bases.BaseInteractiveData`

    Features:
      - Is an interactive collection/structure.
    """

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableStructure(BaseStructure[T], BaseMutableCollection[T]):
    """
    Base mutable structure.

    Inherits from:
      - :class:`objetto.bases.BaseStructure`
      - :class:`objetto.bases.BaseMutableCollection`

    Inherited By:
      - :class:`objetto.bases.BaseMutableAuxiliaryStructure`
      - :class:`objetto.bases.BaseMutableObject`

    Features:
      - Is a mutable collection/structure.
    """

    __slots__ = ()


class BaseAuxiliaryStructureMeta(BaseStructureMeta):
    """
    Metaclass for :class:`objetto.bases.BaseAuxiliaryStructure`.

    Inherits from:
      - :class:`objetto.bases.BaseStructureMeta`

    Inherited by:
      - :class:`objetto.bases.BaseAuxiliaryDataMeta`
      - :class:`objetto.bases.BaseAuxiliaryObjectMeta`
      - :class:`objetto.bases.BaseDictStructureMeta`
      - :class:`objetto.bases.BaseListStructureMeta`
      - :class:`objetto.bases.BaseSetStructureMeta`

    Features:
      - Defines a base auxiliary type.
      - Enforces correct type for :attr:`objetto.bases.BaseAuxiliaryStructure.\
_relationship`.
    """

    def __init__(cls, name, bases, dct):
        super(BaseAuxiliaryStructureMeta, cls).__init__(name, bases, dct)

        # Check relationship type.
        relationship = getattr(cls, "_relationship")
        relationship_type = cls._relationship_type
        assert_is_instance(relationship, relationship_type, subtypes=False)

    @property
    @abstractmethod
    def _base_auxiliary_type(cls):
        # type: () -> Type[BaseAuxiliaryStructure]
        """
        Base auxiliary structure type.

        :rtype: type[objetto.bases.BaseAuxiliaryStructure]
        """
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseAuxiliaryStructure(
    with_metaclass(BaseAuxiliaryStructureMeta, BaseStructure[T])
):
    """
    Structure with a single relationship for all locations.

    Inherits from:
      - :class:`objetto.bases.BaseStructure`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveAuxiliaryStructure`
      - :class:`objetto.bases.BaseMutableAuxiliaryStructure`
      - :class:`objetto.bases.BaseDictStructure`
      - :class:`objetto.bases.BaseListStructure`
      - :class:`objetto.bases.BaseSetStructure`
      - :class:`objetto.bases.BaseAuxiliaryData`
      - :class:`objetto.bases.BaseAuxiliaryObject`
    """

    __slots__ = ()

    _relationship = BaseRelationship()
    """
    **Class Attribute**

    Relationship for all locations.

    :type: objetto.bases.BaseRelationship
    """

    def find_with_attributes(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.

        :return: Value that has matching attributes.

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
        :type location: collections.abc.Hashable

        :return: Relationship.
        :rtype: objetto.bases.BaseRelationship
        """
        return cast("BaseRelationship", cls._relationship)


# noinspection PyAbstractClass
class BaseInteractiveAuxiliaryStructure(
    BaseAuxiliaryStructure[T],
    BaseInteractiveStructure[T],
):
    """
    Base interactive auxiliary structure.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructure`
      - :class:`objetto.bases.BaseInteractiveStructure`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveAuxiliaryData`
      - :class:`objetto.bases.BaseInteractiveDictStructure`
      - :class:`objetto.bases.BaseInteractiveListStructure`
      - :class:`objetto.bases.BaseInteractiveSetStructure`
    """

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableAuxiliaryStructure(
    BaseAuxiliaryStructure[T],
    BaseMutableStructure[T],
):
    """
    Base mutable auxiliary structure.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructure`
      - :class:`objetto.bases.BaseMutableStructure`

    Inherited By:
      - :class:`objetto.bases.BaseMutableAuxiliaryObject`
      - :class:`objetto.bases.BaseMutableDictStructure`
      - :class:`objetto.bases.BaseMutableListStructure`
      - :class:`objetto.bases.BaseMutableSetStructure`
    """

    __slots__ = ()
