# -*- coding: utf-8 -*-

from functools import partial

__all__ = ["Partial"]


class ConcatenatedCallables(object):
    __slots__ = ("callables",)

    def __init__(self, *callables):
        self.callables = callables

    def __call__(self):
        for func in self.callables:
            func()


class Partial(partial):
    __slots__ = ("__partials",)

    def __add__(self, other):
        return type(self)(ConcatenatedCallables(self, other))
