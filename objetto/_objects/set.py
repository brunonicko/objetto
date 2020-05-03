# -*- coding: utf-8 -*-
"""Set object."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from collections import Counter
from six import with_metaclass, string_types
from typing import (
    FrozenSet,
    Set,
    Hashable,
    Iterable,
    Iterator,
    Optional,
    Callable,
    Tuple,
    cast,
)
from .._components.events import EventPhase, field

from ..utils.partial import Partial
from ..utils.type_checking import assert_is_instance

from .base import BaseObjectEvent, BaseObject
from .container import (
    ContainerObjectEvent,
    ContainerObjectMeta,
    ContainerObject,
)

__all__ = [
    "SetObjectEvent",
    "SetAddEvent",
    "SetRemoveEvent",
    "SetObjectMeta",
    "SetObject",
    "MutableSetObject",
    "SetProxyObject",
]


class SetObjectEvent(ContainerObjectEvent):
    """Set object event."""


class SetAddEvent(SetObjectEvent):
    """Emitted when values are added to a set object."""

    new_values = field()


class SetRemoveEvent(SetObjectEvent):
    """Emitted when values are removed from a set object."""

    old_values = field()


class SetObjectMeta(ContainerObjectMeta):
    """Metaclass for 'SetObject'."""


class SetObject(with_metaclass(SetObjectMeta, ContainerObject)):
    """Object that stores values in a set."""

    __slots__ = ()
    __state_type__ = set

    def __len__(self):
        # type: () -> int
        """Get value count."""
        return len(self.__state)

    def __iter__(self):
        # type: () -> Iterator[Hashable]
        """Iterate over values."""
        for value in self.__state:
            yield value

    def __contains__(self, value):
        # type: (Hashable) -> bool
        """Whether contains a value."""
        return value in self.__state

    def __prepare_add(self, new_values):
        # type: (Tuple[Hashable, ...]) -> FrozenSet[Hashable, ...]
        """Prepare add operation."""
        if not new_values:
            error = "no values provided"
            raise ValueError(error)
        processed_new_values = set()
        for value in set(new_values):
            processed_value = self._parameters.fabricate(value)
            if processed_value not in self.__state:
                processed_new_values.add(processed_value)
        return frozenset(processed_new_values)

    def __prepare_remove(self, old_values):
        # type: (Tuple[Hashable, ...]) -> FrozenSet[Hashable, ...]
        """Prepare remove operation."""
        if not old_values:
            error = "no values provided"
            raise ValueError(error)
        if not self.__state.issuperset(old_values):
            error = "some of the provided values are not in the set"
            raise KeyError(error)
        return frozenset(old_values)

    def __add(self, new_values):
        # type: (FrozenSet[Hashable, ...]) -> None
        """Add new values to the set."""
        self.__state.update(new_values)

    def __remove(self, old_values):
        # type: (FrozenSet[Hashable, ...]) -> None
        """Remove values from the set."""
        self.__state.difference_update(old_values)

    def _add(self, *new_values):
        # type: (Tuple[Hashable, ...]) -> None
        """Add new values to the set."""
        if not new_values:
            return

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Prepare add
        new_values = old_values = self.__prepare_add(new_values)

        # Count children
        child_count = Counter()
        if self._parameters.parent:
            for value in new_values:
                if isinstance(value, BaseObject):
                    child_count[value] += 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Prepare history adopters
        history_adopters = set()
        if self._parameters.history:
            for value in new_values:
                if isinstance(value, BaseObject):
                    history_adopters.add(value)
        history_adopters = frozenset(history_adopters)

        # Create partials
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            self.__add, new_values
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            self.__remove, old_values
        )

        # Create events
        redo_event = SetAddEvent(
            obj=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            new_values=new_values,
        )
        undo_event = SetRemoveEvent(
            obj=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            old_values=old_values,
        )

        # Dispatch
        self.__dispatch__(
            "Add Values", redo, redo_event, undo, undo_event, history_adopters
        )

    def _discard(self, *old_values):
        # type: (Tuple[Hashable, ...]) -> None
        """Discard values from the set."""
        old_values = tuple(self.__state.intersection(old_values))
        if not old_values:
            return

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Prepare remove
        old_values = new_values = self.__prepare_remove(old_values)

        # Count children
        child_count = Counter()
        if self._parameters.parent:
            for value in old_values:
                if isinstance(value, BaseObject):
                    child_count[value] -= 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # No history adopters
        history_adopters = frozenset()

        # Create partials
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            self.__remove, old_values
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            self.__add, new_values
        )

        # Create events
        redo_event = SetRemoveEvent(
            obj=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            old_values=old_values,
        )
        undo_event = SetAddEvent(
            obj=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            new_values=new_values,
        )

        # Dispatch
        self.__dispatch__(
            "Remove Values", redo, redo_event, undo, undo_event, history_adopters
        )

    def _clear(self):
        # type: () -> None
        """Clear set."""
        self._discard(*self.__state)

    def _pop(self):
        # type: () -> Hashable
        """Pop value from set."""
        if not self.__state:
            error = "set is empty"
            raise KeyError(error)
        value = next(iter(self.__state))
        self._discard(value)
        return value

    def _remove(self, *old_values):
        # type: (Tuple[Hashable, ...]) -> None
        """Remove values from the set."""
        if not old_values:
            return
        if not self.__state.issuperset(old_values):
            error = "set does not contain value{} {}".format(
                "s" if len(old_values) > 1 else "",
                old_values if len(old_values) > 1 else old_values[0],
            )
            raise KeyError(error)
        self._discard(*old_values)

    def _update(self, new_values):
        # type: (Iterable[Hashable, ...]) -> None
        """Update set with new values."""
        self._add(*new_values)

    def _difference_update(self, other):
        # type: (Iterable[Hashable, ...]) -> None
        """Get difference between this and another iterable and apply it."""
        self._discard(*other)

    def _symmetric_difference_update(self, other):
        # type: (Iterable[Hashable, ...]) -> None
        """Get symmetric difference between this and another iterable and apply it."""
        new_values = set(other).difference(self.__state)
        old_values = self.__state.intersection(other)
        with self._batch_context("Update Values"):
            self._discard(*old_values)
            self._add(*new_values)

    def _intersection_update(self, other):
        # type: (Iterable[Hashable, ...]) -> None
        """Get intersection between this and another iterable and apply it."""
        old_values = self.__state.difference(self.__state.intersection(other))
        self._discard(*old_values)

    def difference(self, other):
        # type: (Iterable[Hashable, ...]) -> Set[Hashable, ...]
        """Get difference between this and another iterable."""
        return self.__state.difference(other)

    def symmetric_difference(self, other):
        # type: (Iterable[Hashable, ...]) -> Set[Hashable, ...]
        """Get symmetric difference between this and another iterable."""
        return self.__state.symmetric_difference(other)

    def intersection(self, other):
        # type: (Iterable[Hashable, ...]) -> Set[Hashable, ...]
        """Get intersection between this and another iterable."""
        return self.__state.intersection(other)

    def union(self, other):
        # type: (Iterable[Hashable, ...]) -> Set[Hashable, ...]
        """Get union between this and another iterable."""
        return self.__state.union(other)

    def isdisjoint(self, other):
        # type: (Iterable[Hashable, ...]) -> bool
        """Get whether this and another iterable are disjoint sets or not."""
        return self.__state.isdisjoint(other)

    def issubset(self, other):
        # type: (Iterable[Hashable, ...]) -> bool
        """Get whether this is a subset of another iterable."""
        return self.__state.issubset(other)

    def issuperset(self, other):
        # type: (Iterable[Hashable, ...]) -> bool
        """Get whether this is a subset of another iterable."""
        return self.__state.issuperset(other)

    @property
    def default_type_name(self):
        # type: () -> str
        """Default type name."""
        value_type = self._parameters.value_type
        if isinstance(value_type, type):
            type_name = "{}Set".format(value_type.__name__.capitalize())
        elif isinstance(value_type, string_types):
            type_name = "{}Set".format(value_type.split(".")[-1].capitalize())
        else:
            type_name = "Set"
        return type_name

    @property
    def __state(self):
        # type: () -> Set
        """Internal state."""
        return cast(Set, super(SetObject, self).__get_state__())


class MutableSetObject(SetObject):
    """Set object with public mutable methods."""

    __slots__ = ()

    def add(self, *new_values):
        # type: (Tuple[Hashable, ...]) -> None
        """Add new values to the set."""
        self._add(*new_values)

    def discard(self, *old_values):
        # type: (Tuple[Hashable, ...]) -> None
        """Discard values from the set."""
        self._discard(*old_values)

    def clear(self):
        # type: () -> None
        """Clear set."""
        self._clear()

    def pop(self):
        # type: () -> Hashable
        """Pop value from set."""
        return self._pop()

    def remove(self, *old_values):
        # type: (Tuple[Hashable, ...]) -> None
        """Remove values from the set."""
        self._remove(*old_values)

    def update(self, new_values):
        # type: (Iterable[Hashable, ...]) -> None
        """Update set with new values."""
        self._update(new_values)

    def difference_update(self, other):
        # type: (Iterable[Hashable, ...]) -> None
        """Get difference between this and another iterable and update."""
        self._difference_update(other)

    def symmetric_difference_update(self, other):
        # type: (Iterable[Hashable, ...]) -> None
        """Get symmetric difference between this and another iterable and update."""
        self._symmetric_difference_update(other)

    def intersection_update(self, other):
        # type: (Iterable[Hashable, ...]) -> None
        """Get intersection between this and another iterable and update."""
        self._intersection_update(other)


class SetProxyObject(SetObject):
    """Read-only set object that reflects the values of another set object."""

    __slots__ = ("__source", "__reaction_phase")

    def __init__(
        self,
        source=None,  # type: Optional[SetObject]
        source_factory=None,  # type: Optional[Callable]
        reaction_phase=EventPhase.POST,  # type: EventPhase
        value_factory=None,  # type: Optional[Callable]
        comparable=True,  # type: bool
        represented=False,  # type: bool
        printed=True,  # type: bool
        parent=None,  # type: Optional[bool]
        history=None,  # type: Optional[bool]
        type_name=None,  # type: Optional[str]
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

        assert_is_instance(source, SetObject)
        assert_is_instance(reaction_phase, EventPhase)

        parent = bool(parent) if parent is not None else not source.parent
        history = bool(history) if history is not None else not source.history

        if getattr(source, "_parameters").parent and parent:
            error = "both source and proxy container objects have 'parent' set to True"
            raise ValueError(error)
        if getattr(source, "_parameters").history and history:
            error = "both source and proxy container objects have 'history' set to True"
            raise ValueError(error)

        super(SetProxyObject, self).__init__(
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
                if type(event) is SetAddEvent:
                    event = cast(SetAddEvent, event)
                    self._add(*event.new_values)
                elif type(event) is SetRemoveEvent:
                    event = cast(SetRemoveEvent, event)
                    self._remove(*event.old_values)

    @property
    def _source(self):
        # type: () -> SetObject
        """Source set object."""
        return self.__source

    @property
    def reaction_phase(self):
        # type: () -> EventPhase
        """Phase in which the reaction takes place."""
        return self.__reaction_phase
