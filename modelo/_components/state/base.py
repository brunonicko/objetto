# -*- coding: utf-8 -*-
"""Base state component."""

from typing import Type, cast

from slotted import Slotted
from componente import CompositeMixin, Component

from ..._base.exceptions import ModeloException, ModeloError

__all__ = ["State", "StateException", "StateError"]


class State(Slotted, Component):
    """Abstract component. Holds values."""

    __slots__ = ()

    @staticmethod
    def get_type():
        # type: () -> Type[State]
        """Get component key type."""
        return State

    def __init__(self, obj):
        # type: (CompositeMixin) -> None
        """Initialize."""
        super(State, self).__init__(obj)

    @classmethod
    def get_component(cls, obj):
        # type: (CompositeMixin) -> State
        """Get state component of a composite object."""
        return cast(State, super(State, cls).get_component(obj))


class StateException(ModeloException):
    """State exception."""


class StateError(ModeloError, StateException):
    """State error."""
