# -*- coding: utf-8 -*-
"""Structure with state curated by attribute descriptors."""

from abc import abstractmethod
from inspect import getmro
from typing import TYPE_CHECKING, Generic, TypeVar, overload
from weakref import WeakKeyDictionary

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, raise_from, string_types, with_metaclass

from .._bases import ABSTRACT_TAG, FINAL_METHOD_TAG, MISSING, Base, BaseMeta, final
from .._states import DictState, SetState
from ..utils.custom_repr import custom_mapping_repr
from ..utils.factoring import format_factory, import_factory, run_factory
from ..utils.reraise_context import ReraiseContext
from ..utils.type_checking import assert_is_instance
from .bases import (
    BaseInteractiveStructure,
    BaseMutableStructure,
    BaseRelationship,
    BaseStructure,
    BaseStructureMeta,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        Iterable,
        Iterator,
        Mapping,
        MutableMapping,
        Optional,
        Tuple,
        Type,
    )

    from ..utils.factoring import LazyFactory

__all__ = [
    "BaseAttributeMeta",
    "BaseAttribute",
    "BaseAttributeStructureMeta",
    "BaseAttributeStructure",
    "BaseInteractiveAttributeStructure",
    "BaseMutableAttributeStructure",
]


T = TypeVar("T")  # Any type.


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
            if instance._initializing:
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
        # type: (Any) -> Any
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