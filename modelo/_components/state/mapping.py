# -*- coding: utf-8 -*-
"""Mapping state component."""

from componente import CompositeMixin
from slotted import Slotted, SlottedMapping
from typing import Callable, Union, Mapping, Optional, Iterable

from ...utils.type_checking import UnresolvedType
from .base import State, StateException, StateError

__all__ = ["MappingState", "MappingStateException", "MappingStateError"]


class MappingState(State):
    """Holds values in a mapping."""

    __slots__ = ("__state",)

    def __init__(self, obj):
        # type: (CompositeMixin) -> None
        """Initialize."""
        super(MappingState, self).__init__(obj)
        self.__state = {}

    """__delitem__, __getitem__, __iter__, __len__, __setitem__"""


class MappingStateException(StateException):
    """Mapping state exception."""


class MappingStateError(StateError, MappingStateException):
    """Mapping state error."""
