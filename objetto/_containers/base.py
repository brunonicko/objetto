# -*- coding: utf-8 -*-
"""Base container class and metaclass."""

from abc import abstractmethod
from re import sub as re_sub
from typing import TYPE_CHECKING

from six import with_metaclass

from .._bases import BaseMeta, Base, ProtectedBase, final, make_base_cls
from ..utils.type_checking import (
    get_type_names, format_types, import_types, assert_is_instance
)
from ..utils.lazy_import import import_path, get_path
from ..utils.factoring import format_factory, run_factory
from ..utils.immutable import ImmutableDict

if TYPE_CHECKING:
    from typing import Any, Tuple, Type, Optional, Union, Dict, List, Iterable, Mapping

    from ..utils.type_checking import LazyTypes
    from ..utils.factoring import LazyFactory

__all__ = [
    "make_auxiliary_cls",
    "BaseRelationship",
    "BaseContainerMeta",
    "BaseContainer",
    "BaseAuxiliaryContainerMeta",
    "BaseAuxiliaryContainer",
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

    # Generate default qualified name based on relationship types.
    if qual_name is None:
        type_names = get_type_names(set(relationship.types).difference((type(None),)))
        if not type_names:
            qual_name = base.__fullname__
        else:
            base_qual_name = base.__fullname__
            root_name = (
                ".".join(base_qual_name.split(".")[:-1]) + "."
                if "." in base_qual_name else ""
            )
            base_name = base_qual_name.split(".")[-1]
            prefix = "".join(
                _capitalize_first(re_sub(r"[^A-Za-z]+", "", tn)) for tn in type_names
            )
            qual_name = "{}{}{}".format(
                root_name,
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
    """Relationship between a container and its values."""

    __slots__ = (
        "types",
        "subtypes",
        "type_checked",
        "module",
        "factory",
        "serialized",
        "serializer",
        "deserializer",
        "represented",
        "passthrough",
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
        self.types = format_types(types, module=module)
        self.subtypes = bool(subtypes)
        self.type_checked = bool(type_checked)
        self.module = module
        self.factory = format_factory(factory, module=module)
        self.serialized = bool(serialized)
        self.serializer = format_factory(serializer, module=module)
        self.deserializer = format_factory(deserializer, module=module)
        self.represented = bool(represented)
        self.passthrough = bool(
            (not self.type_checked or not self.types) and self.factory is None
        )

    @final
    def get_single_exact_type(self, types=(type,)):
        # type: (LazyTypes) -> Optional[Type]
        """Get single exact type from available types if possible."""
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

    def fabricate_value(
        self,
        value,  # type: Any
        factory=True,  # type: bool
        args=(),  # type: Iterable[Any]
        kwargs=ImmutableDict(),  # type: Mapping[str, Any]
    ):
        # type: (...) -> Any
        """Fabricate value."""
        if self.passthrough:
            return value
        if factory and self.factory is not None:
            value = run_factory(self.factory, (value,) + tuple(args), kwargs)
        if self.type_checked and self.types:
            assert_is_instance(value, self.types, subtypes=self.subtypes)
        return value


class BaseContainerMeta(BaseMeta):
    """Metaclass for :class:`BaseContainer`."""

    @property
    @abstractmethod
    def _serializable_container_types(cls):
        # type: () -> Tuple[Type[BaseContainer], ...]
        """Serializable container types."""
        raise NotImplementedError()


class BaseContainer(with_metaclass(BaseContainerMeta, Base)):
    """Base container class."""
    __slots__ = ()

    @classmethod
    @abstractmethod
    def _get_relationship(cls, location=None):
        # type: (Any) -> BaseRelationship
        """Get relationship at location."""
        raise NotImplementedError()

    @classmethod
    @final
    def deserialize_value(cls, serialized, location, **kwargs):
        """Deserialize value at location."""

        # Get relationship.
        relationship = cls._get_relationship(location)
        if not relationship.serialized:
            error = (
                "can't deserialize '{}' object as a value of '{}' since the "
                "relationship{} does not allow for serialization/deserialization"
            ).format(
                type(serialized).__name__,
                cls.__name__,
                " at location {}".format(location) if location is not None else "",
            )
            raise ValueError(error)

        # Custom deserializer.
        if relationship.deserializer is not None:

            # Unescape keys.
            if type(serialized) is dict:
                serialized = _unescape_serialized_class(serialized)

            # Run deserializer.
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
                    return serialized_class.deserialize(
                        serialized[_SERIALIZED_VALUE_KEY], **kwargs
                    )

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
                    cls.__name__,
                    " at location {}".format(location) if location is not None else "",
                )
                raise TypeError(error)

        return relationship.fabricate_value(serialized, factory=False)

    @final
    def serialize_value(self, value, location, **kwargs):
        """Serialize value at location."""

        # Get relationship.
        cls = type(self)
        relationship = cls._get_relationship(location)
        if not relationship.serialized:
            error = (
                "can't serialize '{}' value contained in a '{}' object since the "
                "relationship{} does not allow for serialization/deserialization"
            ).format(
                type(value).__name__,
                cls.__name__,
                " at location {}".format(location) if location is not None else "",
            )
            raise ValueError(error)

        # Custom serializer.
        if relationship.serializer is not None:
            serialized_value = run_factory(relationship.serializer, (value,), kwargs)

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
        """Deserialize."""
        raise NotImplementedError()

    @abstractmethod
    def serialize(self, **kwargs):
        """Serialize."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def _state(self):
        raise NotImplementedError()


class BaseAuxiliaryContainerMeta(BaseContainerMeta):
    """Metaclass for :class:`BaseAuxiliaryContainer`."""

    def __init__(cls, name, bases, dct):
        super(BaseAuxiliaryContainerMeta, cls).__init__(name, bases, dct)
        assert_is_instance(
            getattr(cls, "_relationship"),
            cls._relationship_type,
            subtypes=False
        )

    @property
    @abstractmethod
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """Relationship type."""
        return BaseRelationship


class BaseAuxiliaryContainer(BaseContainer):
    """Container with a single relationship."""
    __slots__ = ()

    _relationship = BaseRelationship()
    """Relationship for all locations."""

    @classmethod
    @final
    def _get_relationship(cls, location=None):
        # type: (Any) -> BaseRelationship
        """Get relationship."""
        return cls._relationship
