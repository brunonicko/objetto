# -*- coding: utf-8 -*-
"""Sequence state component."""

from componente import CompositeMixin
from collections import namedtuple
from slotted import Slotted
from typing import Any, Callable, Union, Mapping, Optional, Tuple, Iterator

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

    def __getitem__(self, item):
        # type: (Union[int, slice]) -> Any
        """Get value at index/slice."""
        return self.__state[item]

    def __len__(self):
        # type: () -> int
        """Get value count."""
        return len(self.__state)

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """Get representation."""
        return "<{}.{} object at {}{}>".format(
            type(self).__module__,
            type(self).__name__,
            hex(id(self)),
            " | " if self.__state else "",
            repr(self.__state) if self.__state else "",
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

    def __iter__(self):
        # type: () -> Iterator[Any, ...]
        """Iterate over values."""
        for value in self.__state:
            yield value

    def normalize_index(self, index, clamp=False):
        state_len = len(self.__state)
        if index < 0:
            index += state_len
        if clamp:
            if index < 0:
                index = 0
            elif index > state_len:
                index = state_len
        elif index < 0 or index >= state_len:
            raise IndexError("index out of range")
        return index

    def prepare_insert(self, index, *new_values):
        # type: (int, Tuple) -> SequenceInsert
        """Prepare insert operation."""
        index = self.normalize_index(index, clamp=True)
        return SequenceInsert(index=index, new_values=new_values)

    def insert(self, insert):
        # type: (SequenceInsert) -> None
        """Insert values at an index."""
        self.__state[insert.index : insert.index] = insert.new_values

    def prepare_pop(self, index=-1, last_index=None):
        # type: (int, Optional[int]) -> SequencePop
        """Prepare pop operation."""
        index = self.normalize_index(index)
        if last_index is None:
            last_index = index
        else:
            last_index = self.normalize_index(last_index)
        old_values = tuple(self.__state[index : last_index + 1])
        return SequencePop(index=index, last_index=last_index, old_values=old_values)

    def pop(self, pop):
        # type: (SequencePop) -> Tuple
        """Pop a range of values out."""
        del self.__state[pop.index : pop.last_index + 1]
        return pop.old_values

    def prepare_move(self, index, target_index, last_index=None):
        # type: (int, int, Optional[int]) -> SequenceMove
        """Prepare move operation."""
        index = self.normalize_index(index)
        target_index = self.normalize_index(target_index, clamp=True)
        if last_index is None:
            last_index = index
        else:
            last_index = self.normalize_index(last_index)
        values = tuple(self.__state[index : last_index + 1])
        return SequenceMove(
            index=index, target_index=target_index, values=values, last_index=last_index
        )

    def move(self, move):
        # type: (SequenceMove) -> None
        """Move a range of values to a different index."""
        if move.target_index < move.index:
            del self.__state[move.index : move.last_index + 1]
            self.__state[move.target_index : move.target_index] = move.values
        elif move.target_index > move.last_index:
            self.__state[move.target_index : move.target_index] = move.values
            del self.__state[move.index : move.last_index + 1]

    def prepare_change(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> SequenceChange
        """Prepare change operation."""
        index = self.normalize_index(index)
        last_index = self.normalize_index(index + len(new_values) - 1)
        old_values = tuple(self.__state[index : last_index + 1])
        return SequenceChange(
            index=index,
            new_values=new_values,
            old_values=old_values,
            last_index=last_index,
        )

    def change(self, change):
        # type: (SequenceChange) -> None
        """Change a range of values."""
        self.__state[change.index : change.last_index + 1] = change.new_values


SequenceInsert = namedtuple("SequenceInsert", "index new_values")
SequencePop = namedtuple("SequencePop", "index last_index old_values")
SequenceMove = namedtuple("SequenceMove", "index target_index values last_index")
SequenceChange = namedtuple("SequenceChange", "index new_values old_values last_index")


class SequenceStateException(StateException):
    """Sequence state exception."""


class SequenceStateError(StateError, SequenceStateException):
    """Sequence state error."""
