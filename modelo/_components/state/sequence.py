# -*- coding: utf-8 -*-
"""Sequence state component."""

from componente import CompositeMixin
from slotted import Slotted
from typing import Callable, Union, Mapping, Optional, Iterable

from ...utils.type_checking import UnresolvedType
from .base import State, StateException, StateError

__all__ = ["SequenceState", "SequenceStateException", "SequenceStateError"]


class SequenceState(State):
    """Holds values in a sequence."""

    __slots__ = ("__state",)

    def __init__(self, obj):
        # type: (CompositeMixin) -> None
        """Initialize."""
        super(SequenceState, self).__init__(obj)
        self.__state = []


class SequenceStateException(StateException):
    """Sequence state exception."""


class SequenceStateError(StateError, SequenceStateException):
    """Sequence state error."""
