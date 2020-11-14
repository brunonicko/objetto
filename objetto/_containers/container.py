# -*- coding: utf-8 -*-
"""Attribute container."""

from abc import abstractmethod
from inspect import getmro
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary

from six import iteritems, with_metaclass

from .._bases import ABSTRACT_TAG, FINAL_METHOD_TAG, ProtectedBase
from .._bases import final as final_
from ..utils.custom_repr import custom_mapping_repr
from ..utils.factoring import format_factory, import_factory, run_factory
from ..utils.immutable import ImmutableDict
from ..utils.type_checking import assert_is_instance
from .bases import (
    BaseContainer,
    BaseContainerMeta,
    BaseInteractiveContainer,
    BaseMutableContainer,
    BaseRelationship,
    BaseSemiInteractiveContainer,
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
    "NOTHING",
    "BaseAttribute",
    "ContainerMeta",
    "Container",
    "SemiInteractiveContainer",
    "InteractiveContainer",
    "MutableContainer",
]

NOTHING = object()


class BaseAttribute(ProtectedBase):
    """
    Attribute descriptor for containers.

    :param relationship: Relationship.
    :param default: Default value.
    :param default_factory: Default value factory.
    :param module: Module path for lazy types/factories.
    :param required: Whether attribute is required to have a value.
    :param final: Whether attribute is final (can't be overridden).
    :param abstract: Whether attribute is abstract (needs to be overridden).
    """

    __slots__ = (
        ABSTRACT_TAG,
        FINAL_METHOD_TAG,
        "relationship",
        "default",
        "default_factory",
        "module",
        "required",
        "final",
        "abstract",
    )

    def __init__(
        self,
        relationship=BaseRelationship(),  # type: BaseRelationship
        default=NOTHING,  # type: Any
        default_factory=None,  # type: LazyFactory
        module=None,  # type: Optional[str]
        required=True,  # type: bool
        final=False,  # type: bool
        abstract=False,  # type: bool
    ):
        # type: (...) -> None
        self.relationship = relationship
        self.default = default
        self.default_factory = format_factory(
            default_factory, module=module or relationship.module
        )
        self.module = module or relationship.module
        self.required = bool(required)
        self.final = bool(final)
        self.abstract = bool(abstract)

        if self.default is not NOTHING and self.default_factory is not None:
            error = "can't provide both 'default' and 'default_factory'"
            raise ValueError(error)

        if self.final and self.abstract:
            error = "can't be final and abstract at the same time"
            raise ValueError(error)
        elif self.final:
            setattr(self, FINAL_METHOD_TAG, True)
        elif self.abstract:
            setattr(self, ABSTRACT_TAG, True)

    @final_
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return hash(id(self))

    @final_
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare with another object for identity.

        :param other: Another object.
        :return: True if the same object.
        """
        return self is other

    @final_
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
            "relationship": self.relationship.to_dict(),
            "default": self.default,
            "default_factory": import_factory(self.default_factory),
            "module": self.module,
            "required": self.required,
            "final": self.final,
            "abstract": self.abstract,
        }

    def __get__(
        self,
        instance,  # type: Optional[Container]
        owner,  # type: Optional[Type[Container]]
    ):
        # type: (...) -> Union[Any, BaseAttribute]
        """
        Get value when accessing from instance or this descriptor otherwise.

        :param instance: Instance.
        :param owner: Owner class.
        :return: Value or this descriptor.
        """
        if instance is not None:
            owner = type(instance)
            attribute_type = getattr(owner, "_attribute_type", None)
            if attribute_type is not None and type(self) is attribute_type:
                name = getattr(owner, "_attribute_names").get(self)
                if name is not None:
                    return instance[name]
        return self

    def fabricate_default_value(self, **kwargs):
        # type: (Any) -> Any
        """
        Fabricate default value.

        :param kwargs: Keyword arguments to be passed to the factories.
        :return: Fabricated value.
        :raises ValueError: Attribute has no default value or default factory.
        """
        default = self.default
        if self.default_factory is not None:
            default = run_factory(self.default_factory, kwargs=kwargs)
        if default is NOTHING:
            error = "attribute has no 'default' or valid 'default_factory'"
            raise ValueError(error)
        return self.relationship.fabricate_value(default, factory=True, **kwargs)

    @property
    def has_default(self):
        # type: () -> bool
        """Whether attribute has a default value or a default factory."""
        return self.default is not NOTHING or self.default_factory is not None


class ContainerMeta(BaseContainerMeta):
    """Metaclass for :class:`Container`."""

    __attributes = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ContainerMeta, ImmutableDict[str, BaseAttribute]]
    __attribute_names = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ContainerMeta, ImmutableDict[BaseAttribute, str]]

    def __init__(cls, name, bases, dct):
        super(ContainerMeta, cls).__init__(name, bases, dct)

        # Prevent having a member called 'keys'.
        if "keys" in dct:
            error = "can't have member of '{}' with reserved name 'keys'".format(name)
            raise TypeError(error)

        # Store attributes.
        attributes = {}  # type: Dict[str, BaseAttribute]
        for base in reversed(getmro(cls)):
            base_is_container = isinstance(base, ContainerMeta)
            for member_name, member in iteritems(base.__dict__):

                # Prevent having a member called 'keys'.
                if member_name == "keys":
                    error = (
                        "can't have base '{}' which defines member with reserved name "
                        "'keys'"
                    ).format(base.__name__)
                    raise TypeError(error)

                # Valid attribute.
                if (
                    base_is_container
                    and isinstance(member, BaseAttribute)
                    and type(member) is cls._attribute_type
                ):

                    # Check relationship type.
                    assert_is_instance(
                        member.relationship,
                        cls._relationship_type,
                        subtypes=False,
                    )

                    # Store it.
                    attributes[member_name] = member

                # Attribute was overridden.
                elif member_name in attributes:
                    del attributes[member_name]
        type(cls).__attributes[cls] = ImmutableDict(attributes)

        # Store attribute names.
        attribute_names = {}  # type: Dict[BaseAttribute, str]
        for attribute_name, attribute in iteritems(attributes):

            # Check if attribute is duplicated.
            if attribute in attribute_names:
                error = "can't use same attribute instance for '{}' and '{}'".format(
                    attribute_names[attribute], attribute_name
                )
                raise ValueError(error)

            # Store it.
            attribute_names[attribute] = attribute_name
        type(cls).__attribute_names[cls] = ImmutableDict(attribute_names)

    @property
    @abstractmethod
    def _attribute_type(cls):
        # type: () -> Type[BaseAttribute]
        """Attribute type."""
        raise NotImplementedError()

    @property
    @final_
    def _attributes(cls):
        # type: () -> ImmutableDict[str, BaseAttribute]
        """Attributes mapped by name."""
        return type(cls).__attributes[cls]

    @property
    @final_
    def _attribute_names(cls):
        # type: () -> ImmutableDict[BaseAttribute, str]
        """Names mapped by attribute."""
        return type(cls).__attribute_names[cls]


class Container(with_metaclass(ContainerMeta, BaseContainer)):
    """Attribute container."""

    __slots__ = ()

    @abstractmethod
    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param name: Name.
        :return: Value.
        """
        raise NotImplementedError()

    @abstractmethod
    def __contains__(self, pair):
        # type: (Tuple[str, Any]) -> bool
        """
        Get whether contains name-value pair.

        :param pair: Name-value pair.
        :return: True if contains.
        """
        raise NotImplementedError()

    @abstractmethod
    def __iter__(self):
        # type: () -> Iterator[Tuple[str, Any]]
        """
        Iterate over name-value pairs.

        :return: Name-value pairs iterator.
        """
        raise NotImplementedError()

    @abstractmethod
    def __len__(self):
        # type: () -> int
        """
        Get count of attributes with values.

        :return: How many attributes with values.
        """
        raise NotImplementedError()

    @classmethod
    @final_
    def _get_relationship(cls, location):
        # type: (str) -> BaseRelationship
        """
        Get relationship at location.

        :param location: Location.
        :return: Relationship.
        """
        attribute = cls._attributes[location]
        return attribute.relationship

    @property
    @abstractmethod
    def _state(self):
        # type: () -> ImmutableDict[str, Any]
        """Internal state."""
        raise NotImplementedError()


class SemiInteractiveContainer(Container, BaseSemiInteractiveContainer):
    """Semi-interactive container."""

    __slots__ = ()

    @abstractmethod
    def _update(self, updates):
        # type: (Union[Mapping, Iterable[Tuple[str, Any]]]) -> Any
        """
        Update multiple attributes.

        :param updates: Updates.
        """
        raise NotImplementedError()


class InteractiveContainer(SemiInteractiveContainer, BaseInteractiveContainer):
    """Interactive container."""

    __slots__ = ()

    @abstractmethod
    def update(self, updates):
        # type: (Union[Mapping, Iterable[Tuple[str, Any]]]) -> Any
        """
        Update multiple attributes.

        :param updates: Updates.
        """
        raise NotImplementedError()


class MutableContainer(InteractiveContainer, BaseMutableContainer):
    """Mutable container."""

    __slots__ = ()

    @abstractmethod
    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Name.
        :param value: Value.
        """
        raise NotImplementedError()

    @abstractmethod
    def __delitem__(self, name):
        # type: (str) -> None
        """
        Delete attribute.

        :param name: Name.
        """
        raise NotImplementedError()
