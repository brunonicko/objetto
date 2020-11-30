# -*- coding: utf-8 -*-
"""Exceptions."""

from ._applications import ObserversFailedError, RejectChangeException
from ._history import HistoryError

__all__ = [
    "ObserversFailedError",
    "RejectChangeException",
    "HistoryError",
]
