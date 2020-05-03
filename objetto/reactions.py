# -*- coding: utf-8 -*-
"""Container event reactions."""

from collections import defaultdict
from slotted import Slotted
from weakref import WeakSet
from six import string_types, iteritems
from typing import Any, Tuple, Dict, Callable, Mapping, Union, Optional, FrozenSet, cast

from ._components.events import EventListenerMixin, EventPhase, RejectEventException
from ._objects.base import BaseObjectEvent
from ._objects.container import ContainerObject
from ._objects.object import AttributesUpdateEvent, Object

from .utils.partial import MergeableCallableMixin, Partial
from .utils.type_checking import assert_is_instance
from .utils.wrapped_dict import WrappedDict

__all__ = ["unique_attributes", "limit"]


class UniqueAttributesReaction(MergeableCallableMixin, EventListenerMixin, Slotted):
    """Asserts that children have unique attributes within a collection."""

    __slots__ = ("__names", "__incrementers", "__watching")

    def __init__(self, *names, **incrementers):
        # type: (Tuple[str, ...], Dict[str, Callable]) -> None
        """Initialize with attribute names and optional incrementer functions."""

        # Check names
        for name in names:
            assert_is_instance(name, string_types)
        names = frozenset(names).union(incrementers)

        # Check incrementers
        incrementers = WrappedDict(incrementers)
        for name, incrementer in iteritems(incrementers):
            if not callable(incrementer):
                error = "expected a callable incrementer for '{}', got '{}'".format(
                    name, type(incrementer).__name__
                )
                raise TypeError(error)

        self.__names = names
        self.__incrementers = incrementers
        self.__watching = WeakSet()

    def __react__(self, event, phase):
        # type: (Union[BaseObjectEvent, Any], EventPhase) -> None
        """React to an event coming from a container's child."""
        if (
            isinstance(event.obj, Object)
            and isinstance(event, AttributesUpdateEvent)
            and phase is EventPhase.INTERNAL_PRE
        ):
            # React before they are actually get updated
            child = event.obj
            parent = child.hierarchy.parent
            if parent in self.__watching:
                child = cast(Object, child)
                children = frozenset((cast(Object, event.obj),))
                container = cast(ContainerObject, event.obj.hierarchy.parent)
                all_new_values = self.__react(
                    container, children, {child: event.new_values}
                )
                if child in all_new_values:
                    new_values = all_new_values[child]
                    new_input_values = tuple(
                        (name, new_values.get(name, value))
                        for name, value in event.input_values
                    )

                    # Update children with new values
                    def callback():
                        child.update(*new_input_values)

                    raise RejectEventException(callback)

    def __react(
        self,
        container,  # type: ContainerObject
        children,  # type: FrozenSet[Object, ...]
        child_new_values=None,  # type: Optional[Dict[Object, Mapping[str, Any]]]
    ):
        # type: (...) -> Dict[Object, Dict[str, Any]]
        """React and return new values."""

        # Build a dictionary with existing values
        all_values = defaultdict(set)
        existing_children = frozenset(
            child for child in container.hierarchy.children if isinstance(child, Object)
        )
        for child in existing_children:

            # Skip child if it's also being tested (not a new child)
            if child in children:
                continue

            # Get value
            for name in self.__names:
                all_values[name].add(getattr(child, name))

        # Check children's values for collisions
        all_new_values = defaultdict(dict)
        for child in children:
            for name in self.__names:

                # If specifying children new values, skip the ones not specified
                if child_new_values is not None:
                    if child not in child_new_values:
                        continue
                    if name not in child_new_values[child]:
                        continue
                    value = child_new_values[child][name]
                else:
                    # Get existing values and child's value for this attribute
                    value = getattr(child, name)

                # Get all values for this attribute
                values = frozenset(all_values[name])

                # There's a collision
                if value in values:

                    # Prepare error message
                    error = (
                        "another object in '{}' already has '{}' set to '{}'"
                    ).format(container.default_type_name, name, repr(value))

                    # Try to use incrementer to get a unique value
                    if name in self.__incrementers:
                        incrementer = self.__incrementers[name]
                        new_value = incrementer(value, values)

                        # Incrementer was able to provide a unique value, so
                        # keep track of it and update all values dictionary
                        if new_value not in values:
                            all_new_values[child][name] = new_value
                            all_values[name].add(new_value)
                            continue

                        # Incrementer failed to make it unique, add to the error
                        # message and error out as a runtime error.
                        else:
                            error += (
                                ", incrementer {} failed to make it unique "
                                "(result was {})"
                            ).format(incrementer, repr(new_value))
                            raise RuntimeError(error)

                    # Not unique, raise value error
                    raise ValueError(error)

        return all_new_values

    def __call__(self, container, event, phase):
        """Reaction."""

        # Children are being added to the container
        if isinstance(event, BaseObjectEvent) and event.obj is container:

            # Add container to 'watching' set
            self.__watching.add(container)

            # React before they are actually added
            if phase is EventPhase.INTERNAL_PRE and event.adoptions:
                children = frozenset(
                    child for child in event.adoptions if isinstance(child, Object)
                )
                all_new_values = self.__react(container, children)

                # Update children with new values
                for child, new_values in iteritems(all_new_values):
                    child.update(*new_values.items())

            # After children are added, listen to their events in case they decide to
            # change their values later.
            elif phase is EventPhase.POST:
                for child in event.adoptions:
                    if isinstance(child, Object):
                        child.events.__add_listener__(self, force=True)
                for child in event.releases:
                    if isinstance(child, Object):
                        child.events.__remove_listener__(self, force=True)

    @property
    def names(self):
        # type: () -> FrozenSet[str, ...]
        """Names."""
        return self.__names

    @property
    def incrementers(self):
        # type: () -> Mapping[str, Callable]
        """Incrementer functions."""
        return self.__incrementers


unique_attributes = UniqueAttributesReaction


def limit(minimum=None, maximum=None):
    # type: (Optional[int], Optional[int]) -> Callable
    """Limit the number of children."""
    if minimum is not None:
        minimum = int(minimum)
        if minimum < 0:
            error = "minimum cannot be less than zero"
            raise ValueError(error)
    if maximum is not None:
        maximum = int(maximum)

    @Partial
    def reaction(container, event, phase):
        """Reaction."""

        # Children are being added to the container
        if isinstance(event, BaseObjectEvent) and event.obj is container:
            if phase is EventPhase.INTERNAL_PRE and (event.adoptions or event.releases):
                current_len = len(container)
                new_len = current_len - len(event.releases) + len(event.adoptions)

                # Growing, check for maximum
                if new_len > current_len:
                    if maximum is not None and new_len > maximum:
                        error_msg = (
                            "tried to add too many items (maximum is {})"
                        ).format(maximum)
                        raise ValueError(error_msg)

                # Shrinking, check for minimum
                elif new_len < current_len:
                    if minimum is not None and new_len < minimum:
                        error_msg = (
                            "tried to remove too many items (minimum is {})"
                        ).format(minimum)
                        raise ValueError(error_msg)

    return reaction
