__all__ = [
    "ObjettoException",
    "ContextError",
    "NotInitializedError",
    "AlreadyInitializedError",
    "AlreadyActingError",
    "HierarchyLockedError",
    "AlreadyParentedError",
    "ParentCycleError",
    "NotAChildError",
    "MultiParentError",
    "MultiUnparentError",
]


class ObjettoException(Exception):
    """Base exception."""


class ContextError(ObjettoException):
    """Context-related error."""


class NotInitializedError(ObjettoException):
    """Object not initialized in context."""


class AlreadyInitializedError(ObjettoException):
    """Object already initialized in context."""


class AlreadyActingError(ObjettoException):
    """Object is already acting."""


class HierarchyLockedError(ObjettoException):
    """Hierarchy is locked."""


class AlreadyParentedError(ObjettoException):
    """Object is already parented."""


class ParentCycleError(ObjettoException):
    """Parent cycle."""


class NotAChildError(ObjettoException):
    """Not a child."""


class MultiParentError(ObjettoException):
    """Can't parent more than once."""


class MultiUnparentError(ObjettoException):
    """Can't unparent more than once."""
