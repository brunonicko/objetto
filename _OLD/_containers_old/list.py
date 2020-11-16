# -*- coding: utf-8 -*-
"""List container."""

from abc import abstractmethod
from typing import Generic, TypeVar

from six import with_metaclass
from slotted import SlottedMutableSequence, SlottedSequence

from ..utils.immutable import ImmutableList
from .bases import (
    BaseAuxiliaryContainer,
    BaseAuxiliaryContainerMeta,
    BaseInteractiveAuxiliaryContainer,
    BaseMutableAuxiliaryContainer,
    BaseSemiInteractiveAuxiliaryContainer,
)

__all__ = [
    "ListContainerMeta",
    "ListContainer",
    "SemiInteractiveListContainer",
    "InteractiveListContainer",
    "MutableListContainer",
]

_T = TypeVar("_T")


class ListContainerMeta(BaseAuxiliaryContainerMeta):
    """Metaclass for :class:`ListContainer`."""


class ListContainer(
    with_metaclass(
        ListContainerMeta,
        BaseAuxiliaryContainer,
        SlottedSequence,
        Generic[_T],
    )
):
    """List container."""

    __slots__ = ()

    @property
    @abstractmethod
    def _state(self):
        # type: () -> ImmutableList[_T]
        """Internal state."""
        raise NotImplementedError()


class SemiInteractiveListContainer(
    ListContainer, BaseSemiInteractiveAuxiliaryContainer
):
    """Semi-interactive list container."""

    __slots__ = ()


class InteractiveListContainer(
    SemiInteractiveListContainer, BaseInteractiveAuxiliaryContainer
):
    """Interactive list container."""

    __slots__ = ()


class MutableListContainer(
    InteractiveListContainer, BaseMutableAuxiliaryContainer, SlottedMutableSequence
):
    """Mutable list container."""

    __slots__ = ()
