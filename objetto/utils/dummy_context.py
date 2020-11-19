# -*- coding: utf-8 -*-
"""Dummy context manager."""

__all__ = ["DummyContext"]


class DummyContext(object):
    """
    Dummy context manager.

    .. code:: python

        >>> from objetto.utils.dummy_context import DummyContext

        >>> with DummyContext():
        ...     pass
    """

    __slots__ = ()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
