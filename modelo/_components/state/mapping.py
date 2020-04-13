# -*- coding: utf-8 -*-
"""Mapping state component."""

from componente import CompositeMixin
from slotted import Slotted
from typing import Callable, Union, Mapping, Optional, Iterable

from ...utils.type_checking import UnresolvedType
from .base import State, StateException, StateError

__all__ = ["MappingState", "MappingStateException", "MappingStateError"]


class MappingState(State):
    """Holds values mapped by hashable keys."""

    __slots__ = ("__attributes",)

    def __init__(self, obj):
        # type: (CompositeMixin) -> None
        """Initialize."""
        super(MappingState, self).__init__(obj)


class MappingStateException(StateException):
    """Mapping state exception."""


class MappingStateError(StateError, MappingStateException):
    """Mapping state error."""
