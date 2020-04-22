# -*- coding: utf-8 -*-
"""Sequence model."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from collections import namedtuple
from six import with_metaclass
from typing import Tuple, Any, Optional, FrozenSet, List, Union, cast
from collections import Counter

from ..utils.partial import Partial
from .base import Model, ModelEvent
from .container import ContainerModelMeta, ContainerModel

__all__ = [
    "SequenceInsertEvent",
    "SequencePopEvent",
    "SequenceMoveEvent",
    "SequenceChangeEvent",
    "SequenceModelMeta",
    "SequenceModel",
]


class SequenceInsertEvent(ModelEvent):
    """Emitted when values are inserted into the sequence."""

    __slots__ = ("__index", "__last_index", "__new_values")

    def __init__(
        self,
        model,  # type: SequenceModel
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        index,  # type: int
        last_index,  # type: int
        new_values,  # type: Tuple[Any, ...]
    ):
        # type: (...) -> None
        """Initialize with index, last index, and new values."""
        super(SequenceInsertEvent, self).__init__(model, adoptions, releases)
        self.__index = index
        self.__last_index = last_index
        self.__new_values = new_values

    @property
    def index(self):
        # type: () -> int
        """Index."""
        return self.__index

    @property
    def last_index(self):
        # type: () -> int
        """Last index."""
        return self.__last_index

    @property
    def new_values(self):
        # type: () -> Tuple[Any, ...]
        """New values."""
        return self.__new_values


class SequencePopEvent(ModelEvent):
    """Emitted when values are popped from the sequence."""

    __slots__ = ("__index", "__last_index", "__old_values")

    def __init__(
        self,
        model,  # type: SequenceModel
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        index,  # type: int
        last_index,  # type: int
        old_values,  # type: Tuple[Any, ...]
    ):
        # type: (...) -> None
        """Initialize with index, last index, and old values."""
        super(SequencePopEvent, self).__init__(model, adoptions, releases)
        self.__index = index
        self.__last_index = last_index
        self.__old_values = old_values

    @property
    def index(self):
        # type: () -> int
        """Index."""
        return self.__index

    @property
    def last_index(self):
        # type: () -> int
        """Last index."""
        return self.__last_index

    @property
    def old_values(self):
        # type: () -> Tuple[Any, ...]
        """Old values."""
        return self.__old_values


class SequenceMoveEvent(ModelEvent):
    """Emitted when values are moved within the sequence."""

    __slots__ = ("__index", "__target_index", "__last_index", "__values")

    def __init__(
        self,
        model,  # type: SequenceModel
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        index,  # type: int
        target_index,  # type: int
        last_index,  # type: int
        values,  # type: Tuple[Any, ...]
    ):
        # type: (...) -> None
        """Initialize with index, last index, and old values."""
        super(SequenceMoveEvent, self).__init__(model, adoptions, releases)
        self.__index = index
        self.__target_index = target_index
        self.__last_index = last_index
        self.__values = values

    @property
    def index(self):
        # type: () -> int
        """Index."""
        return self.__index

    @property
    def target_index(self):
        # type: () -> int
        """Target index."""
        return self.__target_index

    @property
    def last_index(self):
        # type: () -> int
        """Last index."""
        return self.__last_index

    @property
    def values(self):
        # type: () -> Tuple[Any, ...]
        """Old values."""
        return self.__values


class SequenceChangeEvent(ModelEvent):
    """Emitted when values in the sequence change."""

    __slots__ = ("__index", "__last_index", "__new_values", "__old_values")

    def __init__(
        self,
        model,  # type: SequenceModel
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        index,  # type: int
        last_index,  # type: int
        new_values,  # type: Tuple[Any, ...]
        old_values,  # type: Tuple[Any, ...]
    ):
        # type: (...) -> None
        """Initialize with index, last index, and old values."""
        super(SequenceChangeEvent, self).__init__(model, adoptions, releases)
        self.__index = index
        self.__last_index = last_index
        self.__new_values = new_values
        self.__old_values = old_values

    @property
    def index(self):
        # type: () -> int
        """Index."""
        return self.__index

    @property
    def last_index(self):
        # type: () -> int
        """Last index."""
        return self.__last_index

    @property
    def new_values(self):
        # type: () -> Tuple[Any, ...]
        """New values."""
        return self.__new_values

    @property
    def old_values(self):
        # type: () -> Tuple[Any, ...]
        """Old values."""
        return self.__old_values


class SequenceModelMeta(ContainerModelMeta):
    """Metaclass for 'SequenceModel'."""


class SequenceModel(with_metaclass(SequenceModelMeta, ContainerModel)):
    """Model that stores values in a sequence."""

    __slots__ = ()
    __state_type__ = list

    def __getitem__(self, item):
        # type: (Union[int, slice]) -> Union[Any, List]
        """Get value/values at item/slice."""
        return self.__state[item]

    def __len__(self):
        # type: () -> int
        """Get value count."""
        return len(self.__state)

    def __iter__(self):
        """Iterate over values."""
        for value in self.__state:
            yield value

    def __normalize_index(self, index, clamp=False):
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

    def __prepare_insert(self, index, *new_values):
        # type: (int, Tuple) -> Tuple[SequenceInsert, SequencePop]
        """Prepare insert operation."""
        if not new_values:
            raise ValueError("no values provided")
        new_values = tuple(self.__factory__(value) for value in new_values)
        index = self.__normalize_index(index, clamp=True)
        last_index = index + len(new_values) - 1
        return (
            SequenceInsert(index=index, last_index=last_index, new_values=new_values),
            SequencePop(index=index, last_index=last_index, old_values=new_values),
        )

    def __prepare_pop(self, index=-1, last_index=None):
        # type: (int, Optional[int]) -> Tuple[SequencePop, SequenceInsert]
        """Prepare pop operation."""
        index = self.__normalize_index(index)
        if last_index is None:
            last_index = index
        else:
            last_index = self.__normalize_index(last_index)
        old_values = tuple(self.__state[index : last_index + 1])
        return (
            SequencePop(index=index, last_index=last_index, old_values=old_values),
            SequenceInsert(index=index, last_index=last_index, new_values=old_values),
        )

    def __prepare_move(self, index, target_index, last_index=None):
        # type: (int, int, Optional[int]) -> Tuple[SequenceMove, SequenceMove]
        """Prepare move operation."""
        index = self.__normalize_index(index)
        target_index = self.__normalize_index(target_index, clamp=True)
        if last_index is None:
            last_index = index
        else:
            last_index = self.__normalize_index(last_index)
        values = tuple(self.__state[index : last_index + 1])
        if target_index < index:
            undo_move = SequenceMove(
                index=target_index,
                target_index=last_index + index - target_index,
                values=values,
                last_index=target_index + last_index - index,
            )
        elif target_index > last_index:
            undo_move = SequenceMove(
                index=index + target_index - last_index,
                target_index=index,
                values=values,
                last_index=target_index,
            )
        else:
            raise IndexError("target index is within range of index and last index")
        return (
            SequenceMove(
                index=index,
                target_index=target_index,
                values=values,
                last_index=last_index,
            ),
            undo_move,
        )

    def __prepare_change(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> Tuple[SequenceChange, SequenceChange]
        """Prepare change operation."""
        if not new_values:
            raise ValueError("no values provided")
        index = self.__normalize_index(index)
        new_values = tuple(self.__factory__(value) for value in new_values)
        last_index = self.__normalize_index(index + len(new_values) - 1)
        old_values = tuple(self.__state[index : last_index + 1])
        return (
            SequenceChange(
                index=index,
                last_index=last_index,
                new_values=new_values,
                old_values=old_values,
            ),
            SequenceChange(
                index=index,
                last_index=last_index,
                new_values=old_values,
                old_values=new_values,
            ),
        )

    def __insert(self, insert):
        # type: (SequenceInsert) -> None
        """Insert values at an index."""
        self.__state[insert.index : insert.index] = insert.new_values

    def __pop(self, pop):
        # type: (SequencePop) -> Tuple
        """Pop a range of values out."""
        del self.__state[pop.index : pop.last_index + 1]
        return pop.old_values

    def __move(self, move):
        # type: (SequenceMove) -> None
        """Move a range of values to a different index."""
        if move.target_index < move.index:
            del self.__state[move.index : move.last_index + 1]
            self.__state[move.target_index : move.target_index] = move.values
        elif move.target_index > move.last_index:
            self.__state[move.target_index : move.target_index] = move.values
            del self.__state[move.index : move.last_index + 1]

    def __change(self, change):
        # type: (SequenceChange) -> None
        """Change a range of values."""
        self.__state[change.index : change.last_index + 1] = change.new_values

    def _insert(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> None
        """Insert values at an index."""
        if not new_values:
            return

        # Factory values
        new_values = tuple(self.__factory__(v) for v in new_values)

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Prepare insert
        redo_insert, undo_pop = self.__prepare_insert(index, *new_values)

        # Count children
        child_count = Counter()
        if self.parent:
            for value in redo_insert.new_values:
                if isinstance(value, Model):
                    child_count[value] += 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create partials
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            self.__insert, redo_insert
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            self.__pop, undo_pop
        )

        # Create events
        redo_event = SequenceInsertEvent(
            model=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            index=redo_insert.index,
            last_index=redo_insert.last_index,
            new_values=redo_insert.new_values,
        )
        undo_event = SequencePopEvent(
            model=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            index=undo_pop.index,
            last_index=undo_pop.last_index,
            old_values=undo_pop.old_values,
        )

        # Dispatch
        self.__dispatch__("Insert Values", redo, redo_event, undo, undo_event)

    def _pop(self, index=-1, last_index=None):
        # type: (int, Optional[int]) -> Tuple[Any, ...]
        """Pop a range of values out."""

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Prepare pop
        redo_pop, undo_insert = self.__prepare_pop(index=index, last_index=last_index)

        # Count children
        child_count = Counter()
        if self.parent:
            for value in redo_pop.old_values:
                if isinstance(value, Model):
                    child_count[value] -= 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create partials
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            self.__pop, redo_pop
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            self.__insert, undo_insert
        )

        # Create events
        redo_event = SequencePopEvent(
            model=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            index=redo_pop.index,
            last_index=redo_pop.last_index,
            old_values=redo_pop.old_values,
        )
        undo_event = SequenceInsertEvent(
            model=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            index=undo_insert.index,
            last_index=undo_insert.last_index,
            new_values=undo_insert.new_values,
        )

        # Dispatch
        self.__dispatch__("Pop Values", redo, redo_event, undo, undo_event)

        # Return old values
        return redo_pop.old_values

    def _move(self, index, target_index, last_index=None):
        # type: (int, int, Optional[int]) -> None
        """Move a range of values to a different index."""

        # Normalize indexes
        index = self.__normalize_index(index)
        target_index = self.__normalize_index(target_index, clamp=True)
        if last_index is None:
            last_index = index
        else:
            last_index = self.__normalize_index(last_index)
        if index <= target_index <= last_index:
            return

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Prepare move
        redo_move, undo_move = self.__prepare_move(
            index, target_index, last_index=last_index
        )

        # Create partials
        redo = Partial(self.__move, redo_move)
        undo = Partial(self.__move, undo_move)

        # No children updates
        child_count = Counter()
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create events
        redo_event = SequenceMoveEvent(
            model=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            index=redo_move.index,
            target_index=redo_move.target_index,
            last_index=redo_move.last_index,
            values=redo_move.values,
        )
        undo_event = SequenceMoveEvent(
            model=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            index=undo_move.index,
            target_index=undo_move.target_index,
            last_index=undo_move.last_index,
            values=undo_move.values,
        )

        # Dispatch
        self.__dispatch__("Move Values", redo, redo_event, undo, undo_event)

    def _change(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> None
        """Change a range of values."""
        if not new_values:
            return

        # Normalize index
        index = self.__normalize_index(index)

        # Factory values
        new_values = tuple(self.__factory__(v) for v in new_values)

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Prepare change
        redo_change, undo_change = self.__prepare_change(index, *new_values)

        # Create partials
        redo = Partial(self.__change, redo_change)
        undo = Partial(self.__change, undo_change)

        # Count children
        child_count = Counter()
        if self.parent:
            for value in redo_change.new_values:
                if isinstance(value, Model):
                    child_count[value] += 1
            for value in redo_change.old_values:
                if isinstance(value, Model):
                    child_count[value] -= 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create events
        redo_event = SequenceChangeEvent(
            model=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            index=redo_change.index,
            last_index=redo_change.last_index,
            new_values=redo_change.new_values,
            old_values=redo_change.old_values,
        )
        undo_event = SequenceChangeEvent(
            model=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            index=undo_change.index,
            last_index=undo_change.last_index,
            new_values=undo_change.new_values,
            old_values=undo_change.old_values,
        )

        # Dispatch
        self.__dispatch__("Change Values", redo, redo_event, undo, undo_event)

    @property
    def __state(self):
        # type: () -> List
        """Internal state."""
        return cast(List, super(SequenceModel, self).__get_state__())


SequenceInsert = namedtuple("SequenceInsert", "index last_index new_values")
SequencePop = namedtuple("SequencePop", "index last_index old_values")
SequenceMove = namedtuple("SequenceMove", "index target_index values last_index")
SequenceChange = namedtuple("SequenceChange", "index last_index new_values old_values")
