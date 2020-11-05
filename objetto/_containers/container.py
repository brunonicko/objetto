# -*- coding: utf-8 -*-
"""Attribute container."""

from abc import abstractmethod
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary
from inspect import getmro

from six import iteritems

from .._bases import ABSTRACT_TAG, FINAL_METHOD_TAG, ProtectedBase, final
from .base import BaseRelationship, BaseContainerMeta, BaseContainer
from ..utils.factoring import format_factory, run_factory
from ..utils.immutable import ImmutableDict

if TYPE_CHECKING:
    from typing import Any, Optional, Type, Union, Iterable, Mapping, MutableMapping

    from ..utils.factoring import LazyFactory

__all__ = ["NOTHING", "BaseAttribute", "ContainerMeta", "Container"]

NOTHING = object()


class BaseAttribute(ProtectedBase):
    __slots__ = (
        "relationship",
        "default",
        "default_factory",
        "module",
        "required",
        "final",
        "abstract",
        ABSTRACT_TAG,
        FINAL_METHOD_TAG,
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
        self.relationship = relationship
        self.default = default
        self.default_factory = format_factory(default_factory, module=module)
        self.module = module or relationship.module
        self.required = bool(required)
        self.final = bool(final)
        self.abstract = bool(abstract)

        if self.final and self.abstract:
            error = "can't be final and abstract at the same time"
            raise ValueError(error)
        elif self.final:
            setattr(self, FINAL_METHOD_TAG, True)
        elif self.abstract:
            setattr(self, ABSTRACT_TAG, True)

    def __get__(
        self,
        instance,  # type: Optional[Container]
        owner,  # type: Optional[Type[Container]]
    ):
        # type: (...) -> Union[Any, BaseAttribute]
        """Get value when accessing from instance or this descriptor otherwise."""
        if instance is not None:
            attribute_type = getattr(type(instance), "_attribute_type", None)
            if attribute_type is not None and type(self) is attribute_type:
                return self.get_value(instance)
        return self

    def get_name(self, instance):
        # type: (Container) -> str
        """Get attribute name."""
        cls = type(instance)
        return cls._attribute_names[self]

    def get_value(self, instance):
        # type: (Container) -> Any
        """Get attribute value."""
        return instance[self.get_name(instance)]

    def fabricate_default_value(
        self,
        factory=True,  # type: bool
        args=(),  # type: Iterable[Any]
        kwargs=None,  # type: Optional[Mapping[str, Any]]
    ):
        # type: (...) -> Any
        """Fabricate default value."""
        default = self.default
        if self.default_factory is not None:
            default = run_factory(self.default_factory, args, kwargs)
        if default is NOTHING:
            error = "attribute has no 'default' or valid 'default_factory'"
            raise ValueError(error)
        return self.relationship.fabricate_value(
            default,
            factory=factory,
            args=args,
            kwargs=kwargs,
        )

    @property
    def has_default(self):
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

        attributes = {}
        for base in reversed(getmro(cls)):
            for member_name, member in iteritems(base.__dict__):
                if isinstance(member, cls._attribute_type):
                    attributes[member_name] = member
                elif member_name in attributes:
                    del attributes[member_name]
        type(cls).__attributes[cls] = ImmutableDict(attributes)

        attribute_names = {}
        for attribute_name, attribute in iteritems(attributes):
            attribute_names[attribute] = attribute_name
        type(cls).__attribute_names[cls] = ImmutableDict(attribute_names)

    @property
    @abstractmethod
    def _attribute_type(cls):
        # type: () -> Type[BaseAttribute]
        """Attribute type."""
        raise NotImplementedError()

    @property
    @final
    def _attributes(cls):
        # type: () -> ImmutableDict[str, BaseAttribute]
        """Attributes mapped by name."""
        return type(cls).__attributes[cls]

    @property
    @final
    def _attribute_names(cls):
        # type: () -> ImmutableDict[BaseAttribute, str]
        """Names mapped by attribute."""
        return type(cls).__attribute_names[cls]


class Container(BaseContainer):
    """Attribute container."""
    __slots__ = ()
