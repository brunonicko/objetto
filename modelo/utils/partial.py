# -*- coding: utf-8 -*-
"""Partials."""

from functools import partial
from typing import Any, Callable, Tuple, Dict

__all__ = ["Partial"]


class ConcatenatedCallables(object):
    """Concatenates callables and calls them in order through a single call."""

    __slots__ = ("callables",)

    def __init__(self, *callables):
        # type: (Tuple[Callable, ...]) -> None
        """Initialize with callables."""
        self.callables = callables

    def __call__(self, *args, **kwargs):
        # type: (Tuple, Dict[str, Any]) -> None
        """Call callables in order."""
        for func in self.callables:
            func(*args, **kwargs)


class Partial(partial):
    """Partial that can be added/concatenated with another callable/partial."""

    __slots__ = ("__partials",)

    def __add__(self, other):
        # type: (Callable) -> Partial
        """Add with another callable."""
        return type(self)(ConcatenatedCallables(self, other))
