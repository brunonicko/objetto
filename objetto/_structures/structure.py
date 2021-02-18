# -*- coding: utf-8 -*-
"""Structure with state curated by attribute descriptors."""

from abc import abstractmethod
from inspect import getmro
from typing import TYPE_CHECKING, TypeVar, overload
from weakref import WeakKeyDictionary

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, raise_from, with_metaclass

from .._bases import (
    ABSTRACT_TAG,
    FINAL_METHOD_TAG,
    MISSING,
    BaseDict,
    BaseHashable,
    BaseList,
    BaseMeta,
    BaseSet,
    Generic,
    final,
)
from .._constants import BASE_STRING_TYPES
from .._states import DictState, SetState
from ..utils.custom_repr import custom_iterable_repr, custom_mapping_repr
from ..utils.factoring import format_factory, import_factory, run_factory
from ..utils.recursive_repr import recursive_repr
from ..utils.reraise_context import ReraiseContext
from ..utils.type_checking import assert_is_instance, get_type_names
from .bases import (
    BaseAuxiliaryStructure,
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
        Union,
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
    """
    Metaclass for :class:`objetto.bases.BaseAttribute`.

    Inherits from:
      - :class:`objetto.bases.BaseMeta`

    Inherited by:
      - :class:`objetto.data.DataAttributeMeta`
      - :class:`objetto.objects.AttributeMeta`

    Features:
      - Defines relationship type.
    """

    @property
    @abstractmethod
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """
        Relationship type.

        :rtype: type[objetto.bases.BaseRelationship]
        """
        return BaseRelationship


# noinspection PyTypeChecker
_BA = TypeVar("_BA", bound="BaseAttribute")


class BaseAttribute(with_metaclass(BaseAttributeMeta, BaseHashable, Generic[T])):
    """
    Base attribute descriptor for :class:`objetto.bases.BaseAttributeStructure` classes.

    Metaclass:
      - :class:`objetto.bases.BaseAttributeMeta`

    Inherits from:
      - :class:`objetto.bases.BaseHashable`
      - :class:`typing.Generic`

    Inherited by:
      - :class:`objetto.data.DataAttribute`
      - :class:`objetto.objects.Attribute`

    :param relationship: Relationship.
    :type relationship: objetto.bases.BaseRelationship

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param module: Optional module path to use in case partial paths are provided.
    :type module: str or None

    :param required: Whether attribute is required to have a value or not.
    :type required: bool

    :param changeable: Whether attribute value can be changed.
    :type changeable: bool

    :param deletable: Whether attribute value can be deleted.
    :type deletable: bool

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    :raises ValueError: Can't specify both 'default' and 'default_factory' arguments.
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
        "__metadata",
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
        metadata=None,  # type: Any
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
                assert_is_instance(module, BASE_STRING_TYPES + (None,))
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
        self.__metadata = metadata

        if finalized:
            setattr(self, FINAL_METHOD_TAG, True)
        if abstracted:
            setattr(self, ABSTRACT_TAG, True)

    @overload
    def __get__(self, instance, owner):
        # type: (_BA, None, Type[BaseAttributeStructure]) -> Union[_BA, T]
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (BaseAttributeStructure, Type[BaseAttributeStructure]) -> T
        pass

    @overload
    def __get__(self, instance, owner):
        # type: (_BA, object, type) -> _BA
        pass

    def __get__(self, instance, owner):
        """
        Get attribute value when accessing from valid instance or when attribute is
        constant. Get this descriptor otherwise.

        :param instance: Instance.
        :type instance: objetto.bases.BaseAttributeStructure or None

        :param owner: Owner class.
        :type owner: type[objetto.bases.BaseAttributeStructure]

        :return: Value or this descriptor.
        :rtype: Any or objetto.bases.BaseAttribute
        """
        if instance is not None:
            attribute_type = getattr(type(instance), "_attribute_type", None)
            if attribute_type is not None and isinstance(self, attribute_type):
                return self.get_value(instance)
        elif self.constant:
            return self.default
        else:
            return self

    @final
    def __hash__(self):
        # type: () -> int
        """
        Get hash based on object id.

        :return: Hash based on object id.
        :rtype: int
        """
        return hash(id(self))

    @final
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare with another object for identity.

        :param other: Another object.

        :return: True if the same object.
        :rtype: bool
        """
        return other is self

    @final
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
            key_repr=str,
        )

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[str, Any]
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
            "metadata": self.metadata,
        }

    def copy(self, **kwargs):
        # type: (_BA, Any) -> _BA
        """
        Make a copy of this attribute and optionally change some of its parameters.

        :param kwargs: New parameters.

        :return: New attribute.
        :rtype: objetto.bases.BaseAttribute
        """
        return type(self)(
            relationship=kwargs.get("relationship", self.relationship),
            default=kwargs.get("default", self.default),
            default_factory=kwargs.get("default_factory", self.default_factory),
            module=kwargs.get("module", self.module),
            required=kwargs.get("required", self.required),
            changeable=kwargs.get("changeable", self.changeable),
            deletable=kwargs.get("deletable", self.deletable),
            finalized=kwargs.get("finalized", self.finalized),
            abstracted=kwargs.get("abstracted", self.abstracted),
            metadata=kwargs.get("metadata", self.metadata),
        )

    def get_name(self, instance):
        # type: (BaseAttributeStructure) -> str
        """
        Get attribute name.

        :param instance: Instance.
        :type instance: objetto.bases.BaseAttributeStructure

        :return: Attribute Name.
        :rtype: str
        """
        cls = type(instance)
        return cls._attribute_names[self]

    def get_value(self, instance):
        # type: (BaseAttributeStructure) -> T
        """
        Get attribute value.

        :param instance: Instance.
        :type instance: objetto.bases.BaseAttributeStructure

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
        # type: (Any) -> Any
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
        """
        Relationship.

        :rtype: objetto.bases.BaseRelationship
        """
        return self.__relationship

    @property
    def default(self):
        # type: () -> Any
        """Default value."""
        return self.__default

    @property
    def default_factory(self):
        # type: () -> LazyFactory
        """
        Default value factory.

        :rtype: str or collections.abc.Callable or None
        """
        return self.__default_factory

    @property
    def module(self):
        # type: () -> Optional[str]
        """
        Optional module path to use in case partial paths are provided.

        :rtype: str or None
        """
        return self.__module

    @property
    def required(self):
        # type: () -> bool
        """
        Whether attribute is required to have a value or not.

        :rtype: bool
        """
        return self.__required

    @property
    def changeable(self):
        # type: () -> bool
        """
        Whether attribute value can be changed.

        :rtype: bool
        """
        return self._changeable

    @property
    def deletable(self):
        # type: () -> bool
        """
        Whether attribute value can be deleted.

        :rtype: bool
        """
        return self._deletable

    @property
    def finalized(self):
        # type: () -> bool
        """
        If True, attribute can't be overridden by subclasses.

        :rtype: bool
        """
        return self.__finalized

    @property
    def abstracted(self):
        # type: () -> bool
        """
        If True, attribute needs to be overridden by subclasses.

        :rtype: bool
        """
        return self.__abstracted

    @property
    def metadata(self):
        # type: () -> Any
        """Metadata."""
        return self.__metadata

    @property
    def has_default(self):
        # type: () -> bool
        """
        Whether attribute has a default value or a default factory.

        :rtype: bool
        """
        return self.default is not MISSING or self.default_factory is not None

    @property
    def constant(self):
        # type: () -> bool
        """
        Whether attribute is constant.

        :rtype: bool
        """
        return (
            self.default is not MISSING
            and not self.changeable
            and self.relationship.factory is None
        )


class BaseAttributeStructureMeta(BaseStructureMeta):
    """
    Metaclass for :class:`objetto.bases.BaseAttributeStructure`.

    Inherits from:
      - :class:`objetto.bases.BaseStructureMeta`

    Inherited by:
      - :class:`objetto.data.DataMeta`
      - :class:`objetto.objects.ObjectMeta`

    Features:
      - Support for :class:`objetto.bases.BaseAttribute` descriptors.
    """

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

        # Store attributes, check implementation of abstract attributes along the way.
        attributes = {}  # type: Dict[str, BaseAttribute]
        abstract_attributes = {}  # type: Dict[str, Tuple[Type, BaseAttribute]]
        if attribute_type is not None:
            for base in reversed(getmro(cls)):

                # We might need to replace something in the dict for this base, copy it.
                if base is cls:
                    base_dict = dict(base.__dict__)
                else:
                    base_dict = base.__dict__

                # Loop through base dict.
                for member_name, member in iteritems(base_dict):

                    # Implementing checked abstract attribute.
                    if (
                        member_name in abstract_attributes
                        and abstract_attributes[member_name][1].relationship.checked
                    ):
                        abstract_base, abstract_attribute = abstract_attributes[
                            member_name
                        ]

                        # Not an attribute.
                        if not isinstance(member, attribute_type):

                            # Abstract attribute is constant, wrap non-attribute value.
                            if (
                                cls is base
                                and abstract_attribute.constant
                                and not isinstance(member, BaseAttribute)
                            ):

                                # Test for constant value type.
                                try:
                                    abstract_attribute.relationship.fabricate_value(
                                        member, factory=False
                                    )
                                except TypeError:
                                    error = (
                                        "attribute '{}.{}' value type '{}' is not "
                                        "compatible with abstract '{}.{}' constant "
                                        "attribute type '{}'"
                                    ).format(
                                        name,
                                        member_name,
                                        type(member).__name__,
                                        abstract_base.__name__,
                                        member_name,
                                        type(abstract_attribute.default).__name__,
                                    )
                                    exc = TypeError(error)
                                    raise_from(exc, None)
                                    raise exc

                                # Wrap with a concrete copy of the abstract attribute.
                                member = abstract_attribute.copy(
                                    default=member,
                                    abstracted=False,
                                )
                                type.__setattr__(cls, member_name, member)

                            # Error out.
                            else:
                                error = (
                                    "can't implement abstract attribute '{}.{}' in "
                                    "'{}.{}' with unsupported member type '{}', "
                                    "expected '{}'"
                                ).format(
                                    abstract_base.__name__,
                                    member_name,
                                    name,
                                    member_name,
                                    type(member).__name__,
                                    attribute_type.__fullname__,
                                )
                                raise TypeError(error)

                        # Get abstract and concrete types.
                        abstract_member_types = abstract_attribute.relationship.types
                        member_types = member.relationship.types

                        # Both abstract and concrete are matching auxiliary structures.
                        if (
                            len(abstract_member_types) == 1
                            and isinstance(abstract_member_types[0], type)
                            and issubclass(
                                abstract_member_types[0],
                                BaseAuxiliaryStructure,
                            )
                            and len(member_types) == 1
                            and isinstance(member_types[0], type)
                            and issubclass(
                                member_types[0],
                                abstract_member_types[0]._base_auxiliary_type,
                            )
                        ):

                            # Use their auxiliary relationship types.
                            abstract_member_types = abstract_member_types[
                                0
                            ]._relationship.types
                            member_types = member_types[0]._relationship.types

                        # Check types.
                        for typ in abstract_member_types:

                            # If auxiliary structure, use base type.
                            if (
                                not isinstance(typ, BASE_STRING_TYPES)
                                and issubclass(typ, BaseAuxiliaryStructure)
                            ):
                                typ = typ._base_auxiliary_type

                            # No types declared in implementation.
                            if not member_types:

                                error = (
                                    "abstract attribute '{}.{}' declares types, but "
                                    "implementation in '{}.{}' does not"
                                ).format(
                                    abstract_base.__name__,
                                    member_name,
                                    name,
                                    member_name,
                                )
                                raise TypeError(error)

                            # Types are incompatible (skip lazy imported).
                            if not any(
                                isinstance(typ, BASE_STRING_TYPES)
                                or isinstance(t, BASE_STRING_TYPES)
                                or issubclass(t, typ)
                                for t in member_types
                            ):
                                error = (
                                    "types in attribute '{}.{}' {} are not compatible "
                                    "with abstract '{}.{}' attribute types {}"
                                ).format(
                                    name,
                                    member_name,
                                    get_type_names(member_types),
                                    abstract_base.__name__,
                                    member_name,
                                    get_type_names(abstract_member_types),
                                )
                                raise TypeError(error)

                        # Check other parameters.
                        if abstract_attribute.changeable and not member.changeable:
                            error = (
                                "abstract attribute '{}.{}' is changeable, but "
                                "implementation in '{}.{}' is not"
                            ).format(
                                abstract_base.__name__,
                                member_name,
                                name,
                                member_name,
                            )
                            raise TypeError(error)
                        if not abstract_attribute.changeable and member.changeable:
                            error = (
                                "abstract attribute '{}.{}' is not changeable, but "
                                "implementation in '{}.{}' is"
                            ).format(
                                abstract_base.__name__,
                                member_name,
                                name,
                                member_name,
                            )
                            raise TypeError(error)

                        if abstract_attribute.deletable and not member.deletable:
                            error = (
                                "abstract attribute '{}.{}' is deletable, but "
                                "implementation in '{}.{}' is not"
                            ).format(
                                abstract_base.__name__,
                                member_name,
                                name,
                                member_name,
                            )
                            raise TypeError(error)
                        if not abstract_attribute.deletable and member.deletable:
                            error = (
                                "abstract attribute '{}.{}' is not deletable, but "
                                "implementation in '{}.{}' is"
                            ).format(
                                abstract_base.__name__,
                                member_name,
                                name,
                                member_name,
                            )
                            raise TypeError(error)

                    # Store attribute.
                    if isinstance(member, attribute_type):
                        attributes[member_name] = member

                        # Abstract attribute, remember it.
                        if member.abstracted:
                            abstract_attributes[member_name] = base, member

                    # Not an attribute.
                    elif member_name in attributes:
                        del attributes[member_name]

        # Store attribute names.
        attribute_names = {}
        if attribute_type is not None:
            for attribute_name, attribute in iteritems(attributes):
                attribute_names[attribute] = attribute_name

        type(cls).__attributes[cls] = DictState(attributes)
        type(cls).__attribute_names[cls] = DictState(attribute_names)

        # Store abstract attributes.
        abstract_members = set(cls.__dict__.get("__abstractmethods__", ()))
        for attribute_name, attribute in iteritems(attributes):
            if attribute.abstracted:
                abstract_members.add(attribute_name)
        type.__setattr__(cls, "__abstractmethods__", frozenset(abstract_members))

    @property
    @abstractmethod
    def _attribute_type(cls):
        # type: () -> Type[BaseAttribute]
        """
        Attribute type.

        :rtype: type[objetto.bases.BaseAttribute]
        """
        raise NotImplementedError()

    @property
    def _attributes(cls):
        # type: () -> Mapping[str, BaseAttribute]
        """
        Attributes mapped by name.

        :rtype: dict[str, objetto.bases.BaseAttribute]
        """
        return type(cls).__attributes[cls]

    @property
    def _attribute_names(cls):
        # type: () -> Mapping[Any, str]
        """
        Names mapped by attribute.

        :rtype: dict[objetto.bases.BaseAttribute, str]
        """
        return type(cls).__attribute_names[cls]


# noinspection PyTypeChecker
_BAS = TypeVar("_BAS", bound="BaseAttributeStructure")


class BaseAttributeStructure(
    with_metaclass(BaseAttributeStructureMeta, BaseStructure[str])
):
    """
    Base attribute structure.

    Metaclass:
      - :class:`objetto.bases.BaseAttributeStructureMeta`

    Inherits from:
      - :class:`objetto.bases.BaseStructure`

    Inherited by:
      - :class:`objetto.data.Data`
      - :class:`objetto.objects.Object`

    Features:
      - Holds values in attributes defined by descriptors.
      - Can be cast into a dictionary.
    """

    __slots__ = ()

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        :rtype: str
        """

        class SimplifiedAuxiliary(object):
            __slots__ = ("auxiliary",)

            def __init__(self, auxiliary):
                self.auxiliary = auxiliary

            # noinspection PyCallingNonCallable
            def __repr__(self):
                if isinstance(self.auxiliary, BaseDict):
                    return recursive_repr(custom_mapping_repr)(self.auxiliary)
                elif isinstance(self.auxiliary, BaseList) or not self.auxiliary:
                    return recursive_repr(custom_iterable_repr)(self.auxiliary)
                else:
                    return recursive_repr(custom_iterable_repr)(
                        self.auxiliary, prefix="{", suffix="}"
                    )

        def simplify_auxiliary(value):
            if isinstance(value, (BaseDict, BaseList, BaseSet)):
                return SimplifiedAuxiliary(value)
            else:
                return value

        return custom_mapping_repr(
            dict(
                (n, simplify_auxiliary(v))
                for n, v in iteritems(self._state)
                if type(self)._get_relationship(n).represented
            ),
            prefix="{}(".format(type(self).__fullname__),
            template="{key}={value}",
            suffix=")",
            sorting=True,
            sort_key=lambda p: p[0],
            key_repr=str,
        )

    @final
    def __reversed__(self):
        # type: () -> Iterator[str]
        """
        Iterate over reversed attribute names.

        :return: Reversed attribute names iterator.
        :rtype: collections.abc.Iterator[str]
        """
        return self._state.__reversed__()

    @final
    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get value for attribute name.

        :param name: Attribute name.
        :type name: str

        :return: Value.

        :raises KeyError: Attribute does not exist or has no value.
        """
        return self._state[name]

    @final
    def __len__(self):
        # type: () -> int
        """
        Get count of attributes with value.

        :return: Count of attributes with value.
        :rtype: int
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[str]
        """
        Iterate over names of attributes with value.

        :return: Names of attributes with value.
        :rtype: collections.abc.Iterator[str]
        """
        for name in self._state:
            yield name

    @final
    def __contains__(self, name):
        # type: (Any) -> bool
        """
        Get whether attribute name is valid and has a value.

        :param name: Attribute name.
        :type name: str

        :return: True if attribute name is valid and has a value.
        :rtype: bool
        """
        return name in self._state

    @classmethod
    def _get_relationship(cls, location):
        # type: (str) -> BaseRelationship
        """
        Get relationship at location (attribute name).

        :param location: Location (attribute name).
        :type location: str

        :return: Relationship.
        :rtype: objetto.bases.BaseRelationship

        :raises KeyError: Attribute does not exist.
        """
        return cls._get_attribute(location).relationship

    @classmethod
    def _get_attribute(cls, name):
        # type: (str) -> BaseAttribute
        """
        Get attribute by name.

        :param name: Attribute name.
        :type name: str

        :return: Attribute.
        :rtype: objetto.bases.BaseAttribute

        :raises KeyError: Attribute does not exist.
        """
        return cls._attributes[name]

    @abstractmethod
    def _set(self, name, value):
        # type: (_BAS, str, Any) -> _BAS
        """
        Set attribute value.

        :param name: Attribute name.
        :type name: str

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.bases.BaseAttributeStructure

        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        raise NotImplementedError()

    @abstractmethod
    def _delete(self, name):
        # type: (_BAS, str) -> _BAS
        """
        Delete attribute value.

        :param name: Attribute name.
        :type name: str

        :return: Transformed.
        :rtype: objetto.bases.BaseAttributeStructure

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

        :return: Transformed.
        :rtype: objetto.bases.BaseAttributeStructure

        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        raise NotImplementedError()

    @final
    def keys(self):
        # type: () -> SetState[str]
        """
        Get names of the attributes with values.

        :return: Attribute names.
        :rtype: objetto.states.SetState[str]
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
        """
        Internal state.

        :rtype: objetto.states.DictState[str, Any]
        """
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseInteractiveAttributeStructure(
    BaseAttributeStructure, BaseInteractiveStructure[str]
):
    """
    Base interactive attribute structure.

    Inherits from:
      - :class:`objetto.bases.BaseAttributeStructure`
      - :class:`objetto.bases.BaseInteractiveStructure`

    Inherited by:
      - :class:`objetto.data.InteractiveData`
    """

    __slots__ = ()

    @final
    def set(self, name, value):
        # type: (_BAS, str, Any) -> _BAS
        """
        Set attribute value.

        :param name: Attribute name.
        :type name: str

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveAttributeStructure

        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        return self._set(name, value)

    @final
    def delete(self, name):
        # type: (_BAS, str) -> _BAS
        """
        Delete attribute value.

        :param name: Attribute name.
        :type name: str

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveAttributeStructure

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

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveAttributeStructure

        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        return self._update(*args, **kwargs)


# noinspection PyAbstractClass
class BaseMutableAttributeStructure(BaseAttributeStructure, BaseMutableStructure[str]):
    """
    Base mutable attribute structure.

    Inherits from:
      - :class:`objetto.bases.BaseAttributeStructure`
      - :class:`objetto.bases.BaseMutableStructure`

    Inherited by:
      - :class:`objetto.objects.Object`
    """

    __slots__ = ()

    @final
    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :type name: str

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
        :type name: str

        :raises KeyError: Attribute does not exist or has no value.
        """
        self._delete(name)

    @final
    def delete(self, name):
        # type: (str) -> None
        """
        Delete attribute value.

        :param name: Attribute name.
        :type name: str

        :raises KeyError: Attribute does not exist or has no value.
        """
        self._delete(name)

    @final
    def set(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :type name: str

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
