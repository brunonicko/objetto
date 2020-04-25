# -*- coding: utf-8 -*-
"""Base events."""

from abc import abstractmethod
from slotted import SlottedABC
from typing import Tuple, cast

from ..utils.recursive_repr import recursive_repr
from ..utils.object_repr import object_repr

__all__ = ["AbstractEvent", "Event"]


class AbstractEvent(SlottedABC):
    """Abstract event."""

    __slots__ = ()

    @abstractmethod
    def __repr__(self):
        # type: () -> str
        """Get representation."""
        raise NotImplementedError()

    @abstractmethod
    def __str__(self):
        # type: () -> str
        """Get string representation."""
        raise NotImplementedError()

    @abstractmethod
    def __eq__(self, other):
        # type: (AbstractEvent) -> bool
        """Compare with another event for equality."""
        if type(self) is not type(other):
            return False
        return True

    def __ne__(self, other):
        # type: (AbstractEvent) -> bool
        """Compare with another event for inequality."""
        return not self.__eq__(other)


class Event(AbstractEvent):
    """Event."""

    __slots__ = ()

    def __eq__(self, other):
        # type: (Event) -> bool
        """Compare with another event for equality."""
        if not super(Event, self).__eq__(other):
            return False
        other = cast(Event, other)
        for is_property in self.__eq_id_properties__():
            try:
                value = getattr(self, is_property)
                other_value = getattr(other, is_property)
            except AttributeError:
                return False
            if value is not other_value:
                return False
        for eq_property in self.__eq_equal_properties__():
            try:
                value = getattr(self, eq_property)
                other_value = getattr(other, eq_property)
            except AttributeError:
                return False
            if value != other_value:
                return False
        return True

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """Get representation."""
        module = type(self).__module__
        repr_dict = {}
        for repr_property in self.__repr_properties__():
            try:
                value = getattr(self, repr_property)
            except AttributeError:
                continue
            repr_dict[repr_property] = value
        return "<{}{} object at {}{}>".format(
            "{}.".format(module) if "_" not in module else "",
            type(self).__name__,
            hex(id(self)),
            " | {}".format(object_repr(**repr_dict)) if repr_dict else "",
        )

    @recursive_repr
    def __str__(self):
        # type: () -> str
        """Get string representation."""
        str_dict = {}
        for str_property in self.__str_properties__():
            try:
                value = getattr(self, str_property)
            except AttributeError:
                continue
            str_dict[str_property] = value
        return "<{}{}>".format(type(self).__name__, object_repr(**str_dict))

    @abstractmethod
    def __eq_id_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should compared using object identity."""
        raise NotImplementedError()

    @abstractmethod
    def __eq_equal_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should compared using equality."""
        raise NotImplementedError()

    @abstractmethod
    def __repr_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__repr__'."""
        raise NotImplementedError()

    @abstractmethod
    def __str_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__str__'."""
        raise NotImplementedError()
