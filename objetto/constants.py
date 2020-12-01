# -*- coding: utf-8 -*-
"""Constants."""

from ._applications import Phase
from ._objects import DELETED
from .utils.lazy_import import (
    PARTIAL_IMPORT_PATH_REGEX,
    RELATIVE_IMPORT_PATH_REGEX,
    IMPORT_PATH_REGEX,
)

__all__ = [
    "DELETED",
    "PRE",
    "POST",
    "PARTIAL_IMPORT_PATH_REGEX",
    "RELATIVE_IMPORT_PATH_REGEX",
    "IMPORT_PATH_REGEX",
]


PRE = Phase.PRE
"""Phase before the changes are applied."""

POST = Phase.POST
"""Phase after the changes are applied."""
