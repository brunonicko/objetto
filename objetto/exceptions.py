# -*- coding: utf-8 -*-
"""Exceptions."""

from ._base.exceptions import (
    ObjettoException,
    ObjettoError,
)
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
from ._components.events import (
    EventsException,
    EventsError,
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
    HistoryError,
    WhileRunningError,
    AlreadyRanError,
    CannotUndoError,
    CannotRedoError,
)

__all__ = [
    "ObjettoException",
    "ObjettoError",
    "AttributesException",
    "AttributesError",
    "AttributeNameError",
    "AttributeNotDelegatedError",
    "AttributeMissingDelegatesError",
    "AlreadyHasDelegateError",
    "IncompatibleParametersError",
    "IncompatibleDependenciesError",
    "MissingDependencyError",
    "EventsException",
    "EventsError",
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
    "HistoryError",
    "WhileRunningError",
    "AlreadyRanError",
    "CannotUndoError",
    "CannotRedoError",
]
