# -*- coding: utf-8 -*-
"""Abstract collection interfaces."""

from abc import abstractmethod

from slotted import (
    SlottedABC,
    SlottedContainer,
    SlottedIterable,
    SlottedSized,
    SlottedMapping,
    SlottedMutableMapping,
    SlottedSequence,
    SlottedMutableSequence,
    SlottedSet,
    SlottedMutableSet,
)
from typing import TYPE_CHECKING, TypeVar, Generic, cast, overload

if TYPE_CHECKING:
    pass

__all__ = [
    "Interface",
    "SemiInteractiveInterface",
    "InteractiveInterface",
    "MutableInterface",
    "DictInterface",
    "SemiInteractiveDictInterface",
    "InteractiveDictInterface",
    "MutableDictInterface",
    "ListInterface",
    "SemiInteractiveListInterface",
    "InteractiveListInterface",
    "MutableListInterface",
    "SetInterface",
    "SemiInteractiveSetInterface",
    "InteractiveSetInterface",
    "MutableSetInterface",
]

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_T = TypeVar("_T")


class Interface(SlottedSized, SlottedIterable, SlottedContainer, SlottedABC):
    """Abstract collection interface."""


class SemiInteractiveInterface(Interface):
    """Abstract semi-interactive collection interface."""


class InteractiveInterface(SemiInteractiveInterface):
    """Abstract interactive collection interface."""


class MutableInterface(InteractiveInterface):
    """Abstract mutable interface."""


class DictInterface(Interface, SlottedMapping, Generic[_KT, _VT]):
    """Abstract dictionary-like interface."""


class SemiInteractiveDictInterface(DictInterface, SemiInteractiveInterface):
    """Abstract semi-interactive dictionary-like interface."""


class InteractiveDictInterface(SemiInteractiveDictInterface, InteractiveInterface):
    """Abstract interactive dictionary-like interface."""


class MutableDictInterface(
    InteractiveDictInterface, MutableInterface, SlottedMutableMapping
):
    """Abstract mutable dictionary-like interface."""


class ListInterface(Interface, SlottedSequence, Generic[_T]):
    """Abstract list-like interface."""


class SemiInteractiveListInterface(ListInterface, SemiInteractiveInterface):
    """Abstract semi-interactive list-like interface."""


class InteractiveListInterface(
    SemiInteractiveListInterface, InteractiveInterface
):
    """Abstract interactive list-like interface."""


class MutableListInterface(
    InteractiveListInterface, MutableInterface, SlottedMutableSequence
):
    """Abstract mutable list-like interface."""


class SetInterface(Interface, SlottedSet, Generic[_T]):
    """Abstract set-like interface."""


class SemiInteractiveSetInterface(SetInterface, SemiInteractiveInterface):
    """Abstract semi-interactive set-like interface."""


class InteractiveSetInterface(SemiInteractiveSetInterface, InteractiveInterface):
    """Abstract interactive set-like interface."""


class MutableSetInterface(InteractiveSetInterface, MutableInterface, SlottedMutableSet):
    """Abstract mutable set-like interface."""
