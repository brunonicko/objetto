# -*- coding: utf-8 -*-
"""Dictionary container."""

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from six import with_metaclass
from slotted import SlottedMapping, SlottedMutableMapping

from .._bases import ProtectedBase, final, abstract_member
from .bases import (
    BaseAuxiliaryContainerMeta,
    BaseAuxiliaryContainer,
    BaseSemiInteractiveAuxiliaryContainer,
    BaseInteractiveAuxiliaryContainer,
    BaseMutableAuxiliaryContainer,
)
from ..utils.type_checking import assert_is_instance, format_types
from ..utils.factoring import format_factory, run_factory
from ..utils.immutable import ImmutableDict

if TYPE_CHECKING:
    from typing import Any, Type, Optional, Hashable, Union

    from .._bases import AbstractType
    from ..utils.type_checking import LazyTypes
    from ..utils.factoring import LazyFactory

__all__ = [
    "KeyRelationship",
    "DictContainerMeta",
    "DictContainer",
    "SemiInteractiveDictContainer",
    "InteractiveDictContainer",
    "MutableDictContainer",
]

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


@final
class KeyRelationship(ProtectedBase):
    """
    Relationship between a dict container and their keys.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Key factory.
    """

    __slots__ = (
        "types",
        "subtypes",
        "checked",
        "module",
        "factory",
    )

    def __init__(
        self,
        types=(),  # type: LazyTypes
        subtypes=False,  # type: bool
        checked=True,  # type: bool
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
    ):
        self.types = format_types(types, module=module)
        self.subtypes = bool(subtypes)
        self.checked = bool(checked)
        self.module = module
        self.factory = format_factory(factory, module=module)

    def fabricate_key(self, key, factory=True, **kwargs):
        # type: (Optional[Hashable], bool, Any) -> Optional[Hashable]
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
    def passthrough(self):
        # type: () -> bool
        """Whether does not perform type checks and has no factory."""
        return (not self.types or not self.checked) and self.factory is None


class DictContainerMeta(BaseAuxiliaryContainerMeta):
    """Metaclass for :class:`DictContainer`."""

    def __init__(cls, name, bases, dct):
        super(DictContainerMeta, cls).__init__(name, bases, dct)

        # Check key relationship type.
        assert_is_instance(
            getattr(cls, "_key_relationship"),
            (cls._key_relationship_type, type(abstract_member())),
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

    _key_relationship = abstract_member()  # type: Union[AbstractType, KeyRelationship]
    """Relationship for keys."""

    @property
    @abstractmethod
    def _state(self):
        # type: () -> ImmutableDict[_KT, _VT]
        """Internal state."""
        raise NotImplementedError()


class SemiInteractiveDictContainer(
    DictContainer, BaseSemiInteractiveAuxiliaryContainer
):
    """Semi-interactive dictionary container."""
    __slots__ = ()


class InteractiveDictContainer(
    SemiInteractiveDictContainer, BaseInteractiveAuxiliaryContainer
):
    """Interactive dictionary container."""
    __slots__ = ()


class MutableDictContainer(
    InteractiveDictContainer, BaseMutableAuxiliaryContainer, SlottedMutableMapping
):
    """Mutable dictionary container."""
    __slots__ = ()
