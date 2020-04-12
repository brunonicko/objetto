# -*- coding: utf-8 -*-
"""Events."""

from typing import Type, Mapping, Any, Tuple, FrozenSet
from slotted import Slotted


class Event(Slotted):
    """Abstract event."""

    __slots__ = ()

    @property
    def type(self):
        # type: () -> Type[Event]
        """Event type."""
        return type(self)


class ModelEvent(Event):
    """Abstract event. Describes the adoption and/or release of child models."""

    __slots__ = ("__adoptions", "__releases")

    def __init__(self, adoptions, releases):
        # type: (FrozenSet["modelo.Model", ...], FrozenSet["modelo.Model", ...]) -> None
        """Initialize with adoptions and releases."""
        self.__adoptions = adoptions
        self.__releases = releases

    @property
    def adoptions(self):
        # type: () -> FrozenSet["modelo.Model", ...]
        """Adoptions."""
        return self.__adoptions

    @property
    def releases(self):
        # type: () -> FrozenSet["modelo.Model", ...]
        """Releases."""
        return self.__releases


class AttributesUpdateEvent(ModelEvent):
    """Emitted when values for an object model's attributes change."""

    __slots__ = ("__new_values", "__old_values")

    def __init__(
        self,
        adoptions,  # type: FrozenSet["modelo.Model", ...]
        releases,  # type: FrozenSet["modelo.Model", ...]
        new_values,  # type: Mapping[str, Any]
        old_values,  # type: Mapping[str, Any]
    ):
        # type: (...) -> None
        """Initialize with new values and old values."""
        super(AttributesUpdateEvent, self).__init__(adoptions, releases)
        self.__new_values = new_values
        self.__old_values = old_values

    @property
    def new_values(self):
        # type: () -> Mapping[str, Any]
        """New values."""
        return self.__new_values

    @property
    def old_values(self):
        # type: () -> Mapping[str, Any]
        """Old values."""
        return self.__old_values


class SequenceInsertEvent(ModelEvent):
    """Emitted when new values are inserted into a sequence model."""

    __slots__ = ("__index", "__index", "__new_values")

    def __init__(
        self,
        adoptions,  # type: FrozenSet["modelo.Model", ...]
        releases,  # type: FrozenSet["modelo.Model", ...]
        index,  # type: int
        new_values,  # type: Tuple
    ):
        # type: (...) -> None
        """Initialize with index and new values."""
        super(SequenceInsertEvent, self).__init__(adoptions, releases)
        self.__index = index
        self.__new_values = new_values

    @property
    def index(self):
        # type: () -> int
        """Index."""
        return self.__index

    @property
    def new_values(self):
        # type: () -> Tuple
        """New values."""
        return self.__new_values

    @property
    def count(self):
        # type: () -> int
        """Value count."""
        return len(self.__new_values)


class SequencePopEvent(ModelEvent):
    """Emitted when values are removed from a sequence model"""

    __slots__ = ("__index", "__index", "__old_values")

    def __init__(
        self,
        adoptions,  # type: FrozenSet["modelo.Model", ...]
        releases,  # type: FrozenSet["modelo.Model", ...]
        index,  # type: int
        old_values,  # type: Tuple
    ):
        # type: (...) -> None
        """Initialize with index and old values."""
        super(SequencePopEvent, self).__init__(adoptions, releases)
        self.__index = index
        self.__old_values = old_values

    @property
    def index(self):
        # type: () -> int
        """Index."""
        return self.__index

    @property
    def old_values(self):
        # type: () -> Tuple
        """Old values."""
        return self.__old_values

    @property
    def count(self):
        # type: () -> int
        """Value count."""
        return len(self.__old_values)
