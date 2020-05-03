# -*- coding: utf-8 -*-
"""List object."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from collections import Counter, namedtuple
from itertools import chain
from six import with_metaclass, string_types
from typing import (
    Tuple,
    Callable,
    Any,
    Optional,
    List,
    Iterator,
    Union,
    cast,
)

from .._components.events import EventPhase, field

from ..utils.partial import Partial
from ..utils.type_checking import assert_is_instance

from .base import BaseObjectEvent, BaseObject
from .container import ContainerObjectEvent, ContainerObjectMeta, ContainerObject

__all__ = [
    "ListObjectEvent",
    "ListInsertEvent",
    "ListPopEvent",
    "ListMoveEvent",
    "ListChangeEvent",
    "ListObjectMeta",
    "ListObject",
    "MutableListObject",
    "ListProxyObject",
]


class ListObjectEvent(ContainerObjectEvent):
    """List object event."""


class ListInsertEvent(ListObjectEvent):
    """Emitted when values are inserted into the list."""

    index = field()
    last_index = field()
    new_values = field()


class ListPopEvent(ListObjectEvent):
    """Emitted when values are popped from the list."""

    index = field()
    last_index = field()
    old_values = field()


class ListMoveEvent(ListObjectEvent):
    """Emitted when values are moved within the list."""

    index = field()
    target_index = field()
    last_index = field()
    values = field()


class ListChangeEvent(ListObjectEvent):
    """Emitted when values in the list change."""

    index = field()
    last_index = field()
    new_values = field()
    old_values = field()


class ListObjectMeta(ContainerObjectMeta):
    """Metaclass for 'ListObject'."""


class ListObject(with_metaclass(ListObjectMeta, ContainerObject)):
    """Object that stores values in a list."""

    __slots__ = ()
    __state_type__ = list
    default_type_name_prefix = "List"

    def __getitem__(self, item):
        # type: (Union[int, slice]) -> Union[Any, List]
        """Get value/values at item/slice."""
        return self.__state[item]

    def __len__(self):
        # type: () -> int
        """Get value count."""
        return len(self.__state)

    def __iter__(self):
        # type: () -> Iterator[Any]
        """Iterate over values."""
        for value in self.__state:
            yield value

    def __contains__(self, value):
        # type: (Any) -> bool
        """Whether contains a value."""
        return value in self.__state

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
            error = "index out of range"
            raise IndexError(error)
        return index

    def __prepare_insert(self, index, *new_values):
        # type: (int, Tuple) -> Tuple[ListInsert, ListPop]
        """Prepare insert operation."""
        if not new_values:
            error = "no values provided"
            raise ValueError(error)
        new_values = tuple(self._parameters.fabricate(value) for value in new_values)
        index = self.__normalize_index(index, clamp=True)
        last_index = index + len(new_values) - 1
        return (
            ListInsert(index=index, last_index=last_index, new_values=new_values),
            ListPop(index=index, last_index=last_index, old_values=new_values),
        )

    def __prepare_pop(self, index=-1, last_index=None):
        # type: (int, Optional[int]) -> Tuple[ListPop, ListInsert]
        """Prepare pop operation."""
        index = self.__normalize_index(index)
        if last_index is None:
            last_index = index
        else:
            last_index = self.__normalize_index(last_index)
        old_values = tuple(self.__state[index : last_index + 1])
        if not old_values:
            error = "no values in index range {} to {}".format(index, last_index)
            raise IndexError(error)
        return (
            ListPop(index=index, last_index=last_index, old_values=old_values),
            ListInsert(index=index, last_index=last_index, new_values=old_values),
        )

    def __prepare_move(self, index, target_index, last_index=None):
        # type: (int, int, Optional[int]) -> Tuple[ListMove, ListMove]
        """Prepare move operation."""
        index = self.__normalize_index(index)
        target_index = self.__normalize_index(target_index, clamp=True)
        if last_index is None:
            last_index = index
        else:
            last_index = self.__normalize_index(last_index)
        values = tuple(self.__state[index : last_index + 1])
        if not values:
            error = "no values in index range {} to {}".format(index, last_index)
            raise IndexError(error)
        if target_index < index:
            undo_move = ListMove(
                index=target_index,
                target_index=last_index + index - target_index,
                values=values,
                last_index=target_index + last_index - index,
            )
        elif target_index > last_index:
            undo_move = ListMove(
                index=index + target_index - last_index,
                target_index=index,
                values=values,
                last_index=target_index,
            )
        else:
            error = "target index is within range of index and last index"
            raise IndexError(error)
        return (
            ListMove(
                index=index,
                target_index=target_index,
                values=values,
                last_index=last_index,
            ),
            undo_move,
        )

    def __prepare_change(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> Tuple[ListChange, ListChange]
        """Prepare change operation."""
        if not new_values:
            error = "no values provided"
            raise ValueError(error)
        index = self.__normalize_index(index)
        new_values = tuple(self._parameters.fabricate(value) for value in new_values)
        last_index = self.__normalize_index(index + len(new_values) - 1)
        old_values = tuple(self.__state[index : last_index + 1])
        return (
            ListChange(
                index=index,
                last_index=last_index,
                new_values=new_values,
                old_values=old_values,
            ),
            ListChange(
                index=index,
                last_index=last_index,
                new_values=old_values,
                old_values=new_values,
            ),
        )

    def __insert(self, insert):
        # type: (ListInsert) -> None
        """Insert values at an index."""
        self.__state[insert.index : insert.index] = insert.new_values

    def __pop(self, pop):
        # type: (ListPop) -> Tuple
        """Pop a range of values out."""
        del self.__state[pop.index : pop.last_index + 1]
        return pop.old_values

    def __move(self, move):
        # type: (ListMove) -> None
        """Move a range of values to a different index."""
        if move.target_index < move.index:
            del self.__state[move.index : move.last_index + 1]
            self.__state[move.target_index : move.target_index] = move.values
        elif move.target_index > move.last_index:
            self.__state[move.target_index : move.target_index] = move.values
            del self.__state[move.index : move.last_index + 1]

    def __change(self, change):
        # type: (ListChange) -> None
        """Change a range of values."""
        self.__state[change.index : change.last_index + 1] = change.new_values

    def _insert(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> None
        """Insert values at an index."""
        if not new_values:
            return

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Prepare insert
        redo_insert, undo_pop = self.__prepare_insert(index, *new_values)

        # Count children
        child_count = Counter()
        if self._parameters.parent:
            for value in redo_insert.new_values:
                if isinstance(value, BaseObject):
                    child_count[value] += 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Prepare history adopters
        history_adopters = set()
        if self._parameters.history:
            for value in redo_insert.new_values:
                if isinstance(value, BaseObject):
                    history_adopters.add(value)
        history_adopters = frozenset(history_adopters)

        # Create partials
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            self.__insert, redo_insert
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            self.__pop, undo_pop
        )

        # Create events
        redo_event = ListInsertEvent(
            obj=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            index=redo_insert.index,
            last_index=redo_insert.last_index,
            new_values=redo_insert.new_values,
        )
        undo_event = ListPopEvent(
            obj=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            index=undo_pop.index,
            last_index=undo_pop.last_index,
            old_values=undo_pop.old_values,
        )

        # Dispatch
        self.__dispatch__(
            "Insert Values", redo, redo_event, undo, undo_event, history_adopters
        )

    def _pop(self, index=-1, last_index=None):
        # type: (int, Optional[int]) -> Union[Any, Tuple[Any, ...]]
        """Pop a value/range of values out."""

        # Single pop?
        single_pop = last_index is None

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Prepare pop
        redo_pop, undo_insert = self.__prepare_pop(index=index, last_index=last_index)

        # Count children
        child_count = Counter()
        if self._parameters.parent:
            for value in redo_pop.old_values:
                if isinstance(value, BaseObject):
                    child_count[value] -= 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # No history adopters
        history_adopters = frozenset()

        # Create partials
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            self.__pop, redo_pop
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            self.__insert, undo_insert
        )

        # Create events
        redo_event = ListPopEvent(
            obj=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            index=redo_pop.index,
            last_index=redo_pop.last_index,
            old_values=redo_pop.old_values,
        )
        undo_event = ListInsertEvent(
            obj=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            index=undo_insert.index,
            last_index=undo_insert.last_index,
            new_values=undo_insert.new_values,
        )

        # Dispatch
        self.__dispatch__(
            "Pop Values", redo, redo_event, undo, undo_event, history_adopters
        )

        # Return old value(s)
        if single_pop:
            return redo_pop.old_values[0]
        else:
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

        # No history adopters
        history_adopters = frozenset()

        # Create partials
        redo = Partial(self.__move, redo_move)
        undo = Partial(self.__move, undo_move)

        # No children updates
        child_count = Counter()
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create events
        redo_event = ListMoveEvent(
            obj=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            index=redo_move.index,
            target_index=redo_move.target_index,
            last_index=redo_move.last_index,
            values=redo_move.values,
        )
        undo_event = ListMoveEvent(
            obj=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            index=undo_move.index,
            target_index=undo_move.target_index,
            last_index=undo_move.last_index,
            values=undo_move.values,
        )

        # Dispatch
        self.__dispatch__(
            "Move Values", redo, redo_event, undo, undo_event, history_adopters
        )

    def _change(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> None
        """Change a range of values."""
        if not new_values:
            return

        # Normalize index
        index = self.__normalize_index(index)

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Prepare change
        redo_change, undo_change = self.__prepare_change(index, *new_values)

        # Create partials
        redo = Partial(self.__change, redo_change)
        undo = Partial(self.__change, undo_change)

        # Count children
        child_count = Counter()
        if self._parameters.parent:
            for value in redo_change.new_values:
                if isinstance(value, BaseObject):
                    child_count[value] += 1
            for value in redo_change.old_values:
                if isinstance(value, BaseObject):
                    child_count[value] -= 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Prepare history adopters
        history_adopters = set()
        if self._parameters.history:
            for value in redo_change.new_values:
                if isinstance(value, BaseObject):
                    history_adopters.add(value)
        history_adopters = frozenset(history_adopters)

        # Create events
        redo_event = ListChangeEvent(
            obj=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            index=redo_change.index,
            last_index=redo_change.last_index,
            new_values=redo_change.new_values,
            old_values=redo_change.old_values,
        )
        undo_event = ListChangeEvent(
            obj=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            index=undo_change.index,
            last_index=undo_change.last_index,
            new_values=undo_change.new_values,
            old_values=undo_change.old_values,
        )

        # Dispatch
        self.__dispatch__(
            "Change Values", redo, redo_event, undo, undo_event, history_adopters
        )

    def _append(self, *new_values):
        # type: (Tuple[Any, ...]) -> None
        """Insert values at the end of the list."""
        with self._batch_context("Append Values"):
            self._insert(len(self), *new_values)

    def _extend(self, *iterables):
        # type: (Any) -> None
        """Extend the list with one or more iterables."""
        if not iterables:
            return
        with self._batch_context("Extend Values"):
            self._append(*chain(*iterables))

    def _remove(self, value, start=None, stop=None):
        # type: (Any, Optional[int], Optional[int]) -> None
        """Remove value from list."""
        index = self._index(value, start=start, stop=stop)
        with self._batch_context("Remove Value"):
            self._pop(index)

    def _reverse(self):
        # type: () -> None
        """Reverse values."""
        with self._batch_context("Reverse Values"):
            self._extend(reversed(self._pop(0, -1)))

    def _sort(self, key=None, reverse=False):
        # type: (Optional[Callable], bool) -> None
        """Sort values."""
        with self._batch_context("Sort Values"):
            self._extend(sorted(self._pop(0, -1), key=key, reverse=reverse))

    def index(self, value, start=None, stop=None):
        # type: (Any, Optional[int], Optional[int]) -> int
        """Get the index of a value."""
        if start is None and stop is None:
            return self.__state.index(value)
        elif start is not None and stop is None:
            return self.__state.index(value, start)
        elif start is not None and stop is not None:
            return self.__state.index(value, start, stop)
        else:
            error = "provided 'stop' but did not provide 'start'"
            raise ValueError(error)

    def count(self, value):
        # type: (Any) -> int
        """Count occurrences of a value in the list."""
        return self.__state.count(value)

    @property
    def default_type_name(self):
        # type: () -> str
        """Default type name."""
        value_type = self._parameters.value_type
        if isinstance(value_type, type):
            type_name = "{}List".format(value_type.__name__.capitalize())
        elif isinstance(value_type, string_types):
            type_name = "{}List".format(value_type.split(".")[-1].capitalize())
        else:
            type_name = "List"
        return type_name

    @property
    def __state(self):
        # type: () -> List
        """Internal state."""
        return cast(List, super(ListObject, self).__get_state__())


class MutableListObject(ListObject):
    """List object with public mutable methods."""

    __slots__ = ()

    def __setitem__(self, item, value):
        # type: (Union[slice, int], Any) -> None
        """Change/insert value/values at index/range."""
        if isinstance(item, slice):
            index, stop, step = item.indices(len(self))
            if step != 1:
                error = "slice {} is not continuous".format(item)
                raise IndexError(error)
            if stop - index != len(value):
                # Insert
                if stop - index == 0:
                    self.insert(index, *value)
                else:
                    error = "slice {} has a span of {}, but provided {} values".format(
                        item, stop - index, len(value)
                    )
                    raise ValueError(error)
            else:
                # Change range
                self.change(index, *value)
        else:

            # Change single
            self.change(item.__index__(), value)

    def __delitem__(self, item):
        # type: (Union[slice, int]) -> None
        """Pop value/values from index/range."""
        if isinstance(item, slice):
            index, stop, step = item.indices(len(self))
            if step != 1:
                error = "slice {} is not continuous".format(item)
                raise IndexError(error)
            if stop <= index:
                return
            # Pop range
            self.pop(index, stop - 1)
        else:
            # Pop single
            self.pop(item.__index__())

    def insert(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> None
        """Insert values at an index."""
        self._insert(index, *new_values)

    def pop(self, index=-1, last_index=None):
        # type: (int, Optional[int]) -> Union[Any, Tuple[Any, ...]]
        """Pop a value/range of values out."""
        return self._pop(index=index, last_index=last_index)

    def move(self, index, target_index, last_index=None):
        # type: (int, int, Optional[int]) -> None
        """Move a range of values to a different index."""
        self._move(index, target_index, last_index=last_index)

    def change(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> None
        """Change a range of values."""
        self._change(index, *new_values)

    def append(self, *new_values):
        # type: (Tuple[Any, ...]) -> None
        """Insert values at the end of the list."""
        self._append(*new_values)

    def extend(self, *iterables):
        # type: (Any) -> None
        """Extend the list with one or more iterables."""
        self._extend(*iterables)

    def remove(self, value, start=None, stop=None):
        # type: (Any, Optional[int], Optional[int]) -> None
        """Remove value from list."""
        self._remove(value, start=start, stop=stop)

    def reverse(self):
        # type: () -> None
        """Reverse values."""
        self._reverse()

    def sort(self, key=None, reverse=False):
        # type: (Optional[Callable], bool) -> None
        """Sort values."""
        self._sort(key=key, reverse=reverse)


class ListProxyObject(ListObject):
    """Read-only list object that reflects the values of another list object."""

    __slots__ = ("__source", "__reaction_phase")

    def __init__(
        self,
        source=None,  # type: Optional[ListObject]
        source_factory=None,  # type: Optional[Callable]
        reaction_phase=EventPhase.POST,  # type: EventPhase
        value_factory=None,  # type: Optional[Callable]
        comparable=True,  # type: bool
        represented=False,  # type: bool
        printed=True,  # type: bool
        parent=None,  # type: Optional[bool]
        history=None,  # type: Optional[bool]
        type_name=None,  # type: Optional[None]
        reaction=None,  # type: Optional[Callable]
    ):
        if source is None:
            if source_factory is None:
                error = "need to provide exactly one of 'source' or 'source_factory'"
                raise ValueError(error)
            source = source_factory()
        elif source_factory is not None:
            error = "can't provide both 'source' and 'source_factory'"
            raise ValueError(error)

        assert_is_instance(source, ListObject)
        assert_is_instance(reaction_phase, EventPhase)

        parent = bool(parent) if parent is not None else not source.parent
        history = bool(history) if history is not None else not source.history

        if getattr(source, "_parameters").parent and parent:
            error = "both source and proxy container objects have 'parent' set to True"
            raise ValueError(error)
        if getattr(source, "_parameters").history and history:
            error = "both source and proxy container objects have 'history' set to True"
            raise ValueError(error)

        super(ListProxyObject, self).__init__(
            value_type=None,
            value_factory=value_factory,
            exact_value_type=None,
            default_module=None,
            accepts_none=None,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=parent,
            history=history,
            type_name=type_name,
            reaction=reaction,
        )

        self.__source = source
        self.__reaction_phase = reaction_phase

        self._extend(source)
        source.events.add_listener(self)

    def __react__(self, event, phase):
        # type: (BaseObjectEvent, EventPhase) -> None
        """React to an event."""
        if isinstance(event, BaseObjectEvent) and event.obj is self._source:
            if phase is self.__reaction_phase:
                if type(event) is ListInsertEvent:
                    event = cast(ListInsertEvent, event)
                    self._insert(event.index, *event.new_values)
                elif type(event) is ListPopEvent:
                    event = cast(ListPopEvent, event)
                    self._pop(event.index, event.last_index)
                elif type(event) is ListMoveEvent:
                    event = cast(ListMoveEvent, event)
                    self._move(event.index, event.target_index, event.last_index)
                elif type(event) is ListChangeEvent:
                    event = cast(ListChangeEvent, event)
                    self._change(event.index, *event.new_values)

    @property
    def _source(self):
        # type: () -> ListObject
        """Source list object."""
        return self.__source

    @property
    def reaction_phase(self):
        # type: () -> EventPhase
        """Phase in which the reaction takes place."""
        return self.__reaction_phase


ListInsert = namedtuple("ListInsert", "index last_index new_values")
ListPop = namedtuple("ListPop", "index last_index old_values")
ListMove = namedtuple("ListMove", "index target_index values last_index")
ListChange = namedtuple("ListChange", "index last_index new_values old_values")
