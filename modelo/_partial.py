# -*- coding: utf-8 -*-
"""Partials."""

from functools import partial
from typing import Callable, Tuple

__all__ = ["Partial"]


class ConcatenatedCallables(object):
    """Concatenates callables and calls them in order through a single call."""

    __slots__ = ("callables",)

    def __init__(self, *callables):
        # type: (Tuple[Callable, ...]) -> None
        """Initialize with callables."""
        self.callables = callables

    def __call__(self):
        # type: () -> None
        """Call callables in order."""
        for func in self.callables:
            func()


class Partial(partial):
    """Partial that can be added/concatenated with another callable/partial."""

    __slots__ = ("__partials",)

    def __add__(self, other):
        # type: (Callable) -> Partial
        """Add with another callable."""
        return type(self)(ConcatenatedCallables(self, other))
