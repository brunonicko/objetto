# -*- coding: utf-8 -*-
"""Sequence state component."""

from componente import CompositeMixin
from collections import namedtuple
from slotted import Slotted
from typing import Callable, Union, Mapping, Optional, Iterable

from ...utils.type_checking import UnresolvedType
from ...utils.recursive_repr import recursive_repr
from .base import State, StateException, StateError

__all__ = [
    "SequenceState",
    "SequenceStateException",
    "SequenceStateError",
    "SequenceInsert",
    "SequencePop",
    "SequenceMove",
]


class SequenceState(State):
    """Holds values in a sequence."""

    __slots__ = ("__state",)

    def __init__(self, obj):
        # type: (CompositeMixin) -> None
        """Initialize."""
        super(SequenceState, self).__init__(obj)
        self.__state = []

    """__delitem__, __getitem__, __len__, __setitem__, insert"""

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """Get representation."""
        repr_list = repr(self.__state)
        return "<{}.{} object at {}{}>".format(
            type(self).__module__,
            type(self).__name__,
            hex(id(self)),
            "values={}".format(repr_list) if repr_list else "",
        )

    @recursive_repr
    def __str__(self):
        # type: () -> str
        """Get string representation."""
        return self.__state.__str__()

    def __eq__(self, other):
        # type: (SequenceState) -> bool
        """Compare for equality."""
        if not isinstance(other, SequenceState):
            return False
        return self.__state == self.__state

    def get(self, index):
        return self.__state[index]

    def iter(self):
        for value in self.__state:
            yield value

    def len(self):
        return len(self.__state)

    def normalize_index(self, index, insert_clamp=False):
        state_len = len(self.__state)
        if index < 0:
            index += state_len
        if insert_clamp:
            if index < 0:
                index = 0
            elif index > state_len:
                index = state_len
        elif index < 0 or index >= state_len:
            raise IndexError("index out of range")
        return index

    def prepare_insert(self, index, *new_values):
        index = self.normalize_index(index, insert_clamp=True)

    def prepare_pop(self, index=-1, count=1):
        index = self.normalize_index(index)

    def prepare_move(self, index, target_index, count=1):
        index = self.normalize_index(index)
        target_index = self.normalize_index(target_index, insert_clamp=True)

    def prepare_change(self, index, *new_values):
        index = self.normalize_index(index)
        count = len(new_values)


SequenceInsert = namedtuple("SequenceInsert", "index new_values")
SequencePop = namedtuple("SequencePop", "index count old_values")
SequenceMove = namedtuple("SequenceMove", "index target_index count values")
SequenceChange = namedtuple("SequenceChange", "index count new_values old_values")


class SequenceStateException(StateException):
    """Sequence state exception."""


class SequenceStateError(StateError, SequenceStateException):
    """Sequence state error."""
