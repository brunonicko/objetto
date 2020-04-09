# -*- coding: utf-8 -*-

from typing import Type, Mapping, Any, Tuple
from slotted import Slotted


class Event(Slotted):
    """Event."""

    __slots__ = ()

    @property
    def type(self):
        # type: () -> Type[Event]
        """Event type."""
        return type(self)


class ModelEvent(Event):
    __slots__ = ("__adoptions", "__releases")

    def __init__(self, adoptions, releases):
        self.__adoptions = adoptions
        self.__releases = releases

    @property
    def adoptions(self):
        return self.__adoptions

    @property
    def releases(self):
        return self.__releases


class AttributesUpdateEvent(ModelEvent):
    __slots__ = ("__new_values", "__old_values")

    def __init__(self, adoptions, releases, new_values, old_values):
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
    __slots__ = ("__index", "__index", "__new_values")

    def __init__(self, adoptions, releases, index, new_values):
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
    __slots__ = ("__index", "__index", "__old_values")

    def __init__(self, adoptions, releases, index, old_values):
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
