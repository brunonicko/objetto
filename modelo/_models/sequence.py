# -*- coding: utf-8 -*-

from collections import Counter
from typing import (
    Any,
    Optional,
    Union,
    Iterable,
    Iterator,
    Tuple,
    FrozenSet,
    Callable,
    cast,
)

from .._components.hierarchy import Hierarchy, ChildrenUpdates
from .._components.state.base import State
from .._components.state.sequence import SequenceState
from ..utils.type_checking import UnresolvedType as UType
from ..utils.recursive_repr import recursive_repr
from ..utils.partial import Partial
from .base import Model, ModelEvent

__all__ = ["ProtectedSequenceModel"]


class ProtectedSequenceModel(Model):
    """Model that stores values/children in a sequence. Mutable access is protected."""

    __slots__ = ("__parent", "__history")

    def __init__(
        self,
        value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        value_factory=None,  # type: Optional[Callable]
        exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        default_module=None,  # type: Optional[str]
        accepts_none=None,  # type: Optional[bool]
        parent=True,  # type: bool
        history=True,  # type: bool
    ):
        """Initialize with parameters."""
        super(ProtectedSequenceModel, self).__init__()
        self._.add_component(
            SequenceState,
            value_type=value_type,
            value_factory=value_factory,
            exact_value_type=exact_value_type,
            default_module=default_module,
            accepts_none=accepts_none,
        )
        self.__parent = bool(parent)
        self.__history = bool(history)

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """Get representation."""
        state = cast(SequenceState, self._[State])
        repr_list = list(state)
        return "<{}.{} object at {}{}{}>".format(
            type(self).__module__,
            type(self).__name__,
            hex(id(self)),
            " | " if repr_list else "",
            repr_list or "",
        )

    @recursive_repr
    def __str__(self):
        # type: () -> str
        """Get string representation."""
        state = cast(SequenceState, self._[State])
        str_list = list(state)
        return "{}({})".format(type(self).__name__, str_list)

    def __eq__(self, other):
        # type: (ProtectedSequenceModel) -> bool
        """Compare for equality."""
        raise NotImplementedError()

    def __getitem__(self, item):
        # type: (Union[int, slice]) -> Any
        """Get value at index/slice."""
        state = cast(SequenceState, self._[State])
        return state[item]

    def __len__(self):
        state = cast(SequenceState, self._[State])
        return len(state)

    def __iter__(self):
        # type: () -> Iterator[Any, ...]
        """Iterate over values."""
        state = cast(SequenceState, self._[State])
        for value in state:
            yield value

    def _insert(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> None
        """Insert values at an index."""
        if not new_values:
            return

        # Get 'state' and 'hierarchy' components
        state = cast(SequenceState, self._[State])
        hierarchy = cast(Hierarchy, self._[Hierarchy])

        # Prepare insert (redo) and pop (undo)  FIXME
        redo_insert = state.prepare_insert(index, *new_values)
        undo_pop = state.prepare_pop(
            index=redo_insert.index, last_index=redo_insert.last_index
        )

        # Count children
        child_count = Counter()
        if self.__parent:
            for value in redo_insert.new_values:
                if isinstance(value, Model):
                    child_count[value] += 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create partials
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            state.insert, redo_insert
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            state.pop, undo_pop
        )

        # Create events
        redo_event = SequenceInsertEvent(redo_children, undo_children)  # TODO
        undo_event = SequencePopEvent(undo_children, redo_children)  # TODO

        # Dispatch
        self.__dispatch__("Insert Values", redo, redo_event, undo, undo_event)

    def _pop(self, index=-1, last_index=None):
        # type: (int, Optional[int]) -> Tuple[Any, ...]
        """Pop a range of values out."""

        # Get 'state' and 'hierarchy' components
        state = cast(SequenceState, self._[State])
        hierarchy = cast(Hierarchy, self._[Hierarchy])

        # Prepare pop (redo) and insert (undo)  FIXME
        redo_pop = state.prepare_pop(index=index, last_index=last_index)
        undo_insert = state.prepare_insert(index, *redo_pop.old_values)

        # Count children
        child_count = Counter()
        if self.__parent:
            for value in redo_pop.old_values:
                if isinstance(value, Model):
                    child_count[value] -= 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create partials
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            state.pop, redo_pop
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            state.insert, undo_insert
        )

        # Create events
        redo_event = SequencePopEvent(redo_children, undo_children)  # TODO
        undo_event = SequenceInsertEvent(undo_children, redo_children)  # TODO

        # Dispatch
        self.__dispatch__("Pop Values", redo, redo_event, undo, undo_event)

        # Return old values
        return redo_pop.old_values

    def _move(self, index, target_index, last_index=None):
        # type: (int, int, Optional[int]) -> None
        """Move a range of values to a different index."""

        # Get 'state' and 'hierarchy' components
        state = cast(SequenceState, self._[State])
        hierarchy = cast(Hierarchy, self._[Hierarchy])

        # Prepare move (redo) and move (undo)  FIXME
        redo_move = state.prepare_move(index, target_index, last_index=last_index)
        undo_move = state.prepare_move(
            index, target_index, last_index=last_index
        )  # TODO

        # Create partials
        redo = Partial(state.move, redo_move)
        undo = Partial(state.move, undo_move)

        # No children updates
        child_count = Counter()
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create events
        redo_event = SequenceMoveEvent(redo_children, undo_children)  # TODO
        undo_event = SequenceMoveEvent(undo_children, redo_children)  # TODO

        # Dispatch
        self.__dispatch__("Move Values", redo, redo_event, undo, undo_event)

    def _change(self, index, *new_values):
        # type: (int, Tuple[Any, ...]) -> None
        """Change a range of values."""
        if not new_values:
            return

        # Get 'state' and 'hierarchy' components
        state = cast(SequenceState, self._[State])
        hierarchy = cast(Hierarchy, self._[Hierarchy])

        # Prepare change (redo) and change (undo)  FIXME
        redo_change = state.prepare_change(index, *new_values)
        undo_change = state.prepare_change(redo_change.index, *redo_change.old_values)

        # Count children
        child_count = Counter()
        if self.__parent:
            for value in redo_change.new_values:
                if isinstance(value, Model):
                    child_count[value] += 1
            for value in redo_change.old_values:
                if isinstance(value, Model):
                    child_count[value] -= 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create partials
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            state.change, redo_change
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            state.change, undo_change
        )

        # Create events
        redo_event = SequenceChangeEvent(
            redo_children,
            undo_children,
            redo_change.index,
            redo_change.last_index,
            redo_change.new_values,
            redo_change.old_values,
        )
        undo_event = SequenceChangeEvent(
            undo_children,
            redo_children,
            undo_change.index,
            undo_change.last_index,
            undo_change.new_values,
            undo_change.old_values,
        )

        # Dispatch
        self.__dispatch__("Change Values", redo, redo_event, undo, undo_event)

    @property
    def value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Value type."""
        state = cast(SequenceState, self._[State])
        return state.value_type

    @property
    def value_factory(self):
        # type: () -> Optional[Callable]
        """Value factory."""
        state = cast(SequenceState, self._[State])
        return state.value_factory

    @property
    def exact_value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Exact value type."""
        state = cast(SequenceState, self._[State])
        return state.exact_value_type

    @property
    def default_module(self):
        # type: () -> Optional[str]
        """Default module name for type checking."""
        state = cast(SequenceState, self._[State])
        return state.default_module

    @property
    def accepts_none(self):
        # type: () -> bool
        """Whether None can be accepted as a value."""
        state = cast(SequenceState, self._[State])
        return state.accepts_none

    @property
    def parent(self):
        # type: () -> bool
        """Whether model used as value should attach as a child."""
        return self.__parent

    @property
    def history(self):
        # type: () -> bool
        """Whether model used as value should be assigned to the same history."""
        return self.__history


class SequenceInsertEvent(ModelEvent):
    """Emitted when values are inserted into the sequence."""

    __slots__ = ("__index", "__last_index", "__new_values")

    def __init__(
        self,
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        index,  # type: int
        last_index,  # type: int
        new_values,  # type: Tuple[Any, ...]
    ):
        # type: (...) -> None
        """Initialize with index, last index, and new values."""
        super(SequenceInsertEvent, self).__init__(adoptions, releases)
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
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        index,  # type: int
        last_index,  # type: int
        old_values,  # type: Tuple[Any, ...]
    ):
        # type: (...) -> None
        """Initialize with index, last index, and old values."""
        super(SequencePopEvent, self).__init__(adoptions, releases)
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


class SequenceChangeEvent(ModelEvent):
    """Emitted when values in the sequence change."""

    __slots__ = ("__index", "__last_index", "__new_values", "__old_values")

    def __init__(
        self,
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        index,  # type: int
        last_index,  # type: int
        new_values,  # type: Tuple[Any, ...]
        old_values,  # type: Tuple[Any, ...]
    ):
        # type: (...) -> None
        """Initialize with index, last index, and old values."""
        super(SequenceChangeEvent, self).__init__(adoptions, releases)
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
