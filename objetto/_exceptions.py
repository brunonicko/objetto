# -*- coding: utf-8 -*-
"""Base exceptions."""

__all__ = ["BaseObjettoException"]


class BaseObjettoException(Exception):
    """
    Base `Objetto` exception.

    Inherits from:
      - :class:`Exception`

    Inherited By:
      - :class:`objetto.exceptions.ActionObserversFailedError`
      - :class:`objetto.exceptions.RejectChangeException`
      - :class:`objetto.exceptions.HistoryError`
    """
