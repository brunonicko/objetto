# -*- coding: utf-8 -*-
"""Partials."""

from functools import partial
from typing import Any, Callable, Union, Tuple, Dict, cast

__all__ = ["MergeableCallableMixin", "ConcatenatedCallables", "Partial"]


class MergeableCallableMixin(object):
    """Mix-in that enables callable object to be added/merged with another callable."""

    __slots__ = ()

    def __add__(self, other):
        # type: (Callable) -> ConcatenatedCallables
        """Add with another callable."""
        if isinstance(other, ConcatenatedCallables):
            return ConcatenatedCallables(
                *(self,) + cast(ConcatenatedCallables, other).callables
            )
        return ConcatenatedCallables(self, other)


class ConcatenatedCallables(MergeableCallableMixin):
    """Concatenates callables and calls them in order through a single call."""

    __slots__ = ("callables",)

    def __init__(self, *callables):
        # type: (Tuple[Union[Callable, MergeableCallableMixin], ...]) -> None
        """Initialize with callables."""
        self.callables = callables

    def __add__(self, other):
        # type: (Callable) -> ConcatenatedCallables
        """Add with another callable."""
        if isinstance(other, ConcatenatedCallables):
            return type(self)(
                *self.callables + cast(ConcatenatedCallables, other).callables
            )
        return type(self)(*self.callables + (other,))

    def __call__(self, *args, **kwargs):
        # type: (Tuple, Dict[str, Any]) -> None
        """Call callables in order."""
        for func in self.callables:
            func(*args, **kwargs)


class Partial(MergeableCallableMixin, partial):
    """Partial that can be added/concatenated with another callable/partial."""

    pass
