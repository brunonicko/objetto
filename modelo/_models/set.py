# -*- coding: utf-8 -*-
"""Set model."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from six import with_metaclass
from typing import FrozenSet, Set, Hashable, Iterable, Iterator, Tuple, cast
from collections import Counter

from ..utils.partial import Partial
from .base import Model, ModelEvent
from .container import ContainerModelMeta, ContainerModel

__all__ = [
    "SetAddEvent",
    "SetRemoveEvent",
    "SetModelMeta",
    "SetModel",
    "MutableSetModel",
]


class SetAddEvent(ModelEvent):
    """Emitted when values are added to a set model."""

    __slots__ = ("__new_values",)

    def __init__(
        self,
        model,  # type: SetModel
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        new_values,  # type: FrozenSet[Hashable, ...]
    ):
        # type: (...) -> None
        """Initialize with new values."""
        super(SetAddEvent, self).__init__(model, adoptions, releases)
        self.__new_values = new_values

    @property
    def new_values(self):
        # type: () -> FrozenSet[Hashable, ...]
        """New values."""
        return self.__new_values


class SetRemoveEvent(ModelEvent):
    """Emitted when values are removed from a set model."""

    __slots__ = ("__old_values",)

    def __init__(
        self,
        model,  # type: SetModel
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        old_values,  # type: FrozenSet[Hashable, ...]
    ):
        # type: (...) -> None
        """Initialize with old values."""
        super(SetRemoveEvent, self).__init__(model, adoptions, releases)
        self.__old_values = old_values

    @property
    def old_values(self):
        # type: () -> FrozenSet[Hashable, ...]
        """New values."""
        return self.__old_values


class SetModelMeta(ContainerModelMeta):
    """Metaclass for 'SetModel'."""


class SetModel(with_metaclass(SetModelMeta, ContainerModel)):
    """Model that stores values in a set."""

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
            processed_value = self._parameters.fabricate(
                value, accepts_missing=False, accepts_deleted=False
            )
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
                if isinstance(value, Model):
                    child_count[value] += 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Prepare history adopters
        history_adopters = set()
        if self._parameters.history:
            for value in new_values:
                if isinstance(value, Model):
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
            model=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            new_values=new_values
        )
        undo_event = SetRemoveEvent(
            model=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            old_values=old_values
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
                if isinstance(value, Model):
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
            model=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            old_values=old_values
        )
        undo_event = SetAddEvent(
            model=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            new_values=new_values
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
                old_values if len(old_values) > 1 else old_values[0]
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
        with self._batch_context("Symmetric Difference Update"):
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
    def __state(self):
        # type: () -> Set
        """Internal state."""
        return cast(Set, super(SetModel, self).__get_state__())


class MutableSetModel(SetModel):
    """Set model with public mutable methods."""

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
