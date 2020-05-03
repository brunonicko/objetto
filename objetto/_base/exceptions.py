# -*- coding: utf-8 -*-
"""Base exceptions."""


class ObjettoException(Exception):
    """Objetto exception."""


class ObjettoError(StandardError, ObjettoException):
    """Objetto error."""
