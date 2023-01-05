from estruttura.exceptions import (
    ConversionError,
    EstrutturaException,
    InvalidTypeError,
    ProcessingError,
    SerializationError,
    ValidationError,
)

__all__ = [
    "EstrutturaException",
    "ProcessingError",
    "ConversionError",
    "ValidationError",
    "InvalidTypeError",
    "SerializationError",
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


class ContextError(Exception):
    """Context-related error."""


class NotInitializedError(Exception):
    """Object not initialized in context."""


class AlreadyInitializedError(Exception):
    """Object already initialized in context."""


class AlreadyActingError(Exception):
    """Object is already acting."""


class HierarchyLockedError(Exception):
    """Hierarchy is locked."""


class AlreadyParentedError(Exception):
    """Object is already parented."""


class ParentCycleError(Exception):
    """Parent cycle."""


class NotAChildError(Exception):
    """Not a child."""


class MultiParentError(Exception):
    """Can't parent more than once."""


class MultiUnparentError(Exception):
    """Can't unparent more than once."""
