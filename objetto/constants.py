# -*- coding: utf-8 -*-
"""Constants."""

from ._applications import Phase
from ._constants import BASE_STRING_TYPES, INTEGER_TYPES, STRING_TYPES, TEXT_TYPE
from ._objects import DELETED
from .utils.lazy_import import (
    IMPORT_PATH_REGEX,
    PARTIAL_IMPORT_PATH_REGEX,
    PRE_IMPORT_PATH_VALIDATION_REGEX,
    RELATIVE_IMPORT_PATH_REGEX,
)

__all__ = [
    "DELETED",
    "PRE",
    "POST",
    "PRE_IMPORT_PATH_VALIDATION_REGEX",
    "PARTIAL_IMPORT_PATH_REGEX",
    "RELATIVE_IMPORT_PATH_REGEX",
    "IMPORT_PATH_REGEX",
    "TEXT_TYPE",
    "BASE_STRING_TYPES",
    "STRING_TYPES",
    "INTEGER_TYPES",
]


PRE = Phase.PRE
"""
Phase before the changes are applied.

Inherits from:
  - :class:`objetto.bases.Phase`
"""

POST = Phase.POST
"""
Phase after the changes are applied.

Inherits from:
  - :class:`objetto.bases.Phase`
"""
