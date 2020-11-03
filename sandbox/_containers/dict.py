# -*- coding: utf-8 -*-
"""Dictionary container."""

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from six import with_metaclass
from slotted import SlottedMapping, SlottedMutableMapping

from .._base import ProtectedBase, final
from .base import BaseAuxiliaryContainerMeta, BaseAuxiliaryContainer
from ..utils.type_checking import assert_is_instance, format_types
from ..utils.factoring import format_factory, run_factory
from ..utils.immutable import ImmutableDict

if TYPE_CHECKING:
    from typing import Any, Type, Mapping, Iterable, Optional

    from ..utils.type_checking import LazyTypes
    from ..utils.factoring import LazyFactory

__all__ = [
    "KeyRelationship", "DictContainerMeta", "DictContainer", "MutableDictContainer"
]

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


@final
class KeyRelationship(ProtectedBase):
    """Relationship between a dict container and their keys."""

    __slots__ = (
        "types",
        "subtypes",
        "type_checked",
        "module",
        "factory",
        "passthrough",
    )

    def __init__(
        self,
        types=(),  # type: LazyTypes
        subtypes=False,  # type: bool
        type_checked=True,  # type: bool
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
    ):
        self.types = format_types(types, module=module)
        self.subtypes = bool(subtypes)
        self.type_checked = bool(type_checked)
        self.module = module
        self.factory = format_factory(factory, module=module)
        self.passthrough = bool(
            (not self.type_checked or not self.types) and self.factory is None
        )

    def fabricate_key(
        self,
        key,  # type: Any
        factory=True,  # type: bool
        args=(),  # type: Iterable[Any]
        kwargs=ImmutableDict(),  # type: Mapping[str, Any]
    ):
        # type: (...) -> Any
        """Fabricate key."""
        if self.passthrough:
            return key
        if factory and self.factory is not None:
            key = run_factory(self.factory, (key,) + tuple(args), kwargs)
        if self.type_checked and self.types:
            assert_is_instance(key, self.types, subtypes=self.subtypes)
        return key


class DictContainerMeta(BaseAuxiliaryContainerMeta):
    """Metaclass for :class:`DictContainer`."""

    def __init__(cls, name, bases, dct):
        super(DictContainerMeta, cls).__init__(name, bases, dct)
        assert_is_instance(
            getattr(cls, "_key_relationship"),
            cls._key_relationship_type,
            subtypes=False
        )

    @property
    @final
    def _key_relationship_type(cls):
        # type: () -> Type[KeyRelationship]
        """Relationship type."""
        return KeyRelationship


class DictContainer(
    with_metaclass(
        DictContainerMeta,
        BaseAuxiliaryContainer,
        SlottedMapping,
        Generic[_KT, _VT],
    )
):
    """Dictionary container."""
    __slots__ = ()
    _key_relationship = KeyRelationship()
    """Relationship for keys."""

    @property
    @abstractmethod
    def _state(self):
        # type: () -> ImmutableDict[_KT, _VT]
        """Internal state."""
        raise NotImplementedError()


class MutableDictContainer(DictContainer, SlottedMutableMapping):
    """Mutable dictionary container."""
