# -*- coding: utf-8 -*-
"""Base exceptions."""

__all__ = ["ModeloException", "ModeloError"]


class ModeloException(Exception):
    """Base exception."""


class ModeloError(StandardError, ModeloException):
    """Base error."""
