# -*- coding: utf-8 -*-
"""List container."""

from abc import abstractmethod
from typing import Generic, TypeVar

from six import with_metaclass
from slotted import SlottedSequence, SlottedMutableSequence

from .base import BaseAuxiliaryContainerMeta, BaseAuxiliaryContainer
from ..utils.immutable import ImmutableList

__all__ = ["ListContainerMeta", "ListContainer", "MutableListContainer"]

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


class MutableListContainer(ListContainer, SlottedMutableSequence):
    """Mutable list container."""
