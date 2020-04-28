# -*- coding: utf-8 -*-
"""Base exceptions."""


class ModeloException(Exception):
    """Base exception."""


class ModeloError(StandardError, ModeloException):
    """Base error."""


class SpecialValueError(ModeloError):
    """Raised when using a special value where it is not allowed."""
