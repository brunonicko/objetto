# -*- coding: utf-8 -*-
"""Set container."""

from abc import abstractmethod
from typing import Generic, TypeVar

from six import with_metaclass
from slotted import SlottedMutableSet, SlottedSet

from ..utils.immutable import ImmutableSet
from .bases import (
    BaseAuxiliaryContainer,
    BaseAuxiliaryContainerMeta,
    BaseInteractiveAuxiliaryContainer,
    BaseMutableAuxiliaryContainer,
    BaseSemiInteractiveAuxiliaryContainer,
)

__all__ = [
    "SetContainerMeta",
    "SetContainer",
    "SemiInteractiveSetContainer",
    "InteractiveSetContainer",
    "MutableSetContainer",
]

_T = TypeVar("_T")


class SetContainerMeta(BaseAuxiliaryContainerMeta):
    """Metaclass for :class:`SetContainer`."""


class SetContainer(
    with_metaclass(
        SetContainerMeta,
        BaseAuxiliaryContainer,
        SlottedSet,
        Generic[_T],
    )
):
    """Set container."""

    __slots__ = ()

    @property
    @abstractmethod
    def _state(self):
        # type: () -> ImmutableSet[_T]
        """Internal state."""
        raise NotImplementedError()


class SemiInteractiveSetContainer(SetContainer, BaseSemiInteractiveAuxiliaryContainer):
    """Semi-interactive set container."""

    __slots__ = ()


class InteractiveSetContainer(
    SemiInteractiveSetContainer, BaseInteractiveAuxiliaryContainer
):
    """Interactive set container."""

    __slots__ = ()


class MutableSetContainer(
    InteractiveSetContainer, BaseMutableAuxiliaryContainer, SlottedMutableSet
):
    """Mutable set container."""

    __slots__ = ()
