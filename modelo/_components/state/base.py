# -*- coding: utf-8 -*-
"""Base state component."""

from abc import abstractmethod
from typing import Type, cast

from slotted import SlottedABC
from componente import CompositeMixin, Component

from ..._base.exceptions import ModeloException, ModeloError

__all__ = ["State", "StateException", "StateError"]


class State(SlottedABC, Component):
    """Abstract component. Holds values."""

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
        # type: (State) -> bool
        """Compare for equality."""
        raise NotImplementedError()

    def __ne__(self, other):
        # type: (State) -> bool
        """Compare for inequality."""
        return not self.__eq__(other)

    @staticmethod
    def get_type():
        # type: () -> Type[State]
        """Get component key type."""
        return State

    @classmethod
    def get_component(cls, obj):
        # type: (CompositeMixin) -> State
        """Get state component of a composite object."""
        return cast(State, super(State, cls).get_component(obj))


class StateException(ModeloException):
    """State exception."""


class StateError(ModeloError, StateException):
    """State error."""
