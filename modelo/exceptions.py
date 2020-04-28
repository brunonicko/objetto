# -*- coding: utf-8 -*-
"""Exceptions."""

from ._base.exceptions import ModeloException, ModeloError, SpecialValueError
from ._components.attributes import (
    AttributesException,
    AttributesError,
    AttributeNameError,
    AttributeNotDelegatedError,
    AttributeMissingDelegatesError,
    AlreadyHasDelegateError,
    IncompatibleParametersError,
    IncompatibleDependenciesError,
    MissingDependencyError,
)
from ._components.broadcaster import (
    BroadcasterException,
    BroadcasterError,
    AlreadyEmittingError,
    PhaseError,
    StopEventPropagationException,
    RejectEventException,
)
from ._components.hierarchy import (
    HierarchyException,
    HierarchyError,
    AlreadyParentedError,
    NotParentedError,
    ParentCycleError,
    MultipleParentingError,
    MultipleUnparentingError,
)
from ._components.history import (
    HistoryException,
    HistoryError,
    WhileRunningError,
    AlreadyRanError,
    CannotUndoError,
    CannotRedoError,
)

__all__ = [
    "ModeloException",
    "ModeloError",
    "SpecialValueError",
    "AttributesException",
    "AttributesError",
    "AttributeNameError",
    "AttributeNotDelegatedError",
    "AttributeMissingDelegatesError",
    "AlreadyHasDelegateError",
    "IncompatibleParametersError",
    "IncompatibleDependenciesError",
    "MissingDependencyError",
    "BroadcasterException",
    "BroadcasterError",
    "AlreadyEmittingError",
    "PhaseError",
    "StopEventPropagationException",
    "RejectEventException",
    "HierarchyException",
    "HierarchyError",
    "AlreadyParentedError",
    "NotParentedError",
    "ParentCycleError",
    "MultipleParentingError",
    "MultipleUnparentingError",
    "HistoryException",
    "HistoryError",
    "WhileRunningError",
    "AlreadyRanError",
    "CannotUndoError",
    "CannotRedoError",
]
