# -*- coding: utf-8 -*-

from typing import Optional, Callable

# Base


class ModeloException(Exception):
    pass


class ModeloError(ModeloException):
    pass


# Hierarchy


class HierarchyException(ModeloException):
    pass


class HierarchyError(HierarchyException, ModeloError):
    pass


class AlreadyParentedError(HierarchyError):
    pass


class NotParentedError(HierarchyError):
    pass


class ParentCycleError(HierarchyError):
    pass


class MultipleParentingError(HierarchyError):
    pass


class MultipleUnparentingError(HierarchyError):
    pass


# Broadcaster


class BroadcasterException(ModeloException):
    pass


class BroadcasterError(BroadcasterException, ModeloError):
    pass


class StopEventPropagationException(BroadcasterException):
    pass


class RejectEventException(BroadcasterException):
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
    pass


class RunnerError(RunnerException, ModeloError):
    pass


class CannotUndoError(RunnerError):
    pass


class CannotRedoError(RunnerError):
    pass
