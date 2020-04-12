# -*- coding: utf-8 -*-
"""Exceptions."""

from typing import Optional, Callable

# Base


class ModeloException(Exception):
    """Base exception."""


class ModeloError(ModeloException):
    """Base error."""


# Hierarchy


class HierarchyException(ModeloException):
    """Hierarchy exception."""


class HierarchyError(HierarchyException, ModeloError):
    """Hierarchy error."""


class AlreadyParentedError(HierarchyError):
    """Raised when already parented to another parent."""


class NotParentedError(HierarchyError):
    """Raised when not parented to given parent."""


class ParentCycleError(HierarchyError):
    """Raised when a parent cycle is detected."""


class MultipleParentingError(HierarchyError):
    """Raised when trying to parent more than once."""


class MultipleUnparentingError(HierarchyError):
    """Raised when trying to un-parent more than once."""


# Broadcaster


class BroadcasterException(ModeloException):
    """Broadcaster exception."""


class BroadcasterError(BroadcasterException, ModeloError):
    """Broadcaster error."""


class StopEventPropagationException(BroadcasterException):
    """When raised during event emission, will prevent next listeners to react."""


class RejectEventException(BroadcasterException):
    """
    When raised during event emission, will prevent the action that originated the
    event from happening at all.
    """

    __slots__ = ("__callback",)

    def __init__(self, callback=None):
        # type: (Optional[Callable]) -> None
        super(RejectEventException, self).__init__()
        self.__callback = callback

    @property
    def callback(self):
        # type: () -> Optional[Callable]
        return self.__callback


# Runner


class RunnerException(ModeloException):
    """Runner exception."""


class RunnerError(RunnerException, ModeloError):
    """Runner error."""


class CannotUndoError(RunnerError):
    """Raised when trying to undo but no more commands are available."""


class CannotRedoError(RunnerError):
    """Raised when trying to redo but no more commands are available."""
