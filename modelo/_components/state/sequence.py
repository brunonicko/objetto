# -*- coding: utf-8 -*-
"""Sequence state component."""

from collections import namedtuple
from typing import Any, Callable, Union, Iterable, Optional, Tuple, Iterator
from six import raise_from

from ...utils.type_checking import UnresolvedType as UType
from ...utils.type_checking import assert_is_unresolved_type, assert_is_instance
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

    def __init__(
        self,
        obj,  # type: CompositeMixin
        value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        value_factory=None,  # type: Optional[Callable]
        exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        default_module=None,  # type: Optional[str]
        accepts_none=None,  # type: Optional[bool]
    ):
        # type: (...) -> None
        """Initialize."""
        super(SequenceState, self).__init__(obj)

        # Internal list state
        self.__state = []

        # Default module
        if default_module is None:
            self.__default_module = None
        else:
            self.__default_module = str(default_module)

        # Check, and store 'value_type', 'exact_value_type', and 'accepts_none'
        if value_type is not None and exact_value_type is not None:
            raise ValueError(
                "cannot specify bot 'value_type' and 'exact_value_type' arguments"
            )
        if value_type is not None:
            assert_is_unresolved_type(value_type)
            self.__value_type = value_type
            self.__exact_value_type = None
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else False
            )
        elif exact_value_type is not None:
            assert_is_unresolved_type(exact_value_type)
            self.__value_type = None
            self.__exact_value_type = exact_value_type
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else False
            )
        else:
            self.__value_type = None
            self.__exact_value_type = None
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else True
            )

        # Check and store 'value_factory'
        if value_factory is not None and not callable(value_factory):
            raise TypeError(
                "expected a callable for 'value_factory', got '{}'".format(
                    type(value_factory).__name__
                )
            )
        self.__value_factory = value_factory

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

    def __getitem__(self, item):
        # type: (Union[int, slice]) -> Any
        """Get value at index/slice."""
        return self.__state[item]

    def __len__(self):
        # type: () -> int
        """Get value count."""
        return len(self.__state)

    def __iter__(self):
        # type: () -> Iterator[Any, ...]
        """Iterate over values."""
        for value in self.__state:
            yield value

    def __factory(self, value):
        # type: (Any) -> Any
        """Fabricate value by running it through type checks and factory."""
        if self.__value_factory is not None:
            value = self.__value_factory(value)
        if self.__value_type is not None:
            assert_is_instance(
                value,
                self.__value_type,
                optional=self.__accepts_none,
                exact=False,
                default_module_name=self.__default_module,
            )
        elif self.__exact_value_type is not None:
            assert_is_instance(
                value,
                self.__exact_value_type,
                optional=self.__accepts_none,
                exact=True,
                default_module_name=self.__default_module,
            )
        elif not self.__accepts_none and value is None:
            error = "sequence does not accept None as a value"
            raise TypeError(error)
        return value

    def normalize_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """Normalize index."""
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
        new_values = tuple(self.__factory(value) for value in new_values)
        index = self.normalize_index(index, clamp=True)
        last_index = index + len(new_values) - 1
        return SequenceInsert(index=index, last_index=last_index, new_values=new_values)

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
        new_values = tuple(self.__factory(value) for value in new_values)
        last_index = self.normalize_index(index + len(new_values) - 1)
        old_values = tuple(self.__state[index : last_index + 1])
        return SequenceChange(
            index=index,
            last_index=last_index,
            new_values=new_values,
            old_values=old_values
        )

    def change(self, change):
        # type: (SequenceChange) -> None
        """Change a range of values."""
        self.__state[change.index : change.last_index + 1] = change.new_values

    @property
    def value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Value type."""
        return self.__value_type

    @property
    def value_factory(self):
        # type: () -> Optional[Callable]
        """Value factory."""
        return self.__value_factory

    @property
    def exact_value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Exact value type."""
        return self.__exact_value_type

    @property
    def default_module(self):
        # type: () -> Optional[str]
        """Default module name for type checking."""
        return self.__default_module

    @property
    def accepts_none(self):
        # type: () -> bool
        """Whether None can be accepted as a value."""
        return self.__accepts_none


SequenceInsert = namedtuple("SequenceInsert", "index last_index new_values")
SequencePop = namedtuple("SequencePop", "index last_index old_values")
SequenceMove = namedtuple("SequenceMove", "index target_index values last_index")
SequenceChange = namedtuple("SequenceChange", "index last_index new_values old_values")


class SequenceStateException(StateException):
    """Sequence state exception."""


class SequenceStateError(StateError, SequenceStateException):
    """Sequence state error."""
