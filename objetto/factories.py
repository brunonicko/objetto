# -*- coding: utf-8 -*-
"""Default factories."""

import re
from typing import Any, Optional, Tuple

from .utils.type_checking import assert_is_instance

__all__ = [
    "integer",
    "floating_point",
    "regex_match",
    "regex_sub",
    "curated",
]


class Factory(object):
    """Decorator that allows for concatenating/adding of factory functions."""

    __slots__ = ("__funcs",)

    def __init__(self, *funcs):
        self.__funcs = funcs

    def __call__(self, value):
        for func in self.__funcs:
            value = func(value)
        return value

    def __add__(self, other):
        # type: (Factory) -> Factory
        """Add with another factory."""
        assert_is_instance(other, Factory, exact=True)
        return Factory(*self.__funcs + other.__funcs)


def integer(minimum=None, maximum=None, clamp=False):
    # type: (Optional[int], Optional[int], bool) -> Factory
    """Integer factory maker."""
    if clamp and minimum is None and maximum is None:
        error = (
            "factory parameter 'clamp' was set to True, but no minimum and/or maximum "
            "provided"
        )
        raise ValueError(error)
    if minimum is not None:
        minimum = int(minimum)
    if maximum is not None:
        maximum = int(maximum)

    @Factory
    def factory(value):
        """Factory function."""
        value = int(value)
        if minimum is not None and value < minimum:
            if clamp:
                value = minimum
            else:
                error_msg = "minimum value is {}, got {}".format(minimum, value)
                raise ValueError(error_msg)
        if maximum is not None and value > maximum:
            if clamp:
                value = maximum
            else:
                error_msg = "maximum value is {}, got {}".format(minimum, value)
                raise ValueError(error_msg)
        return value

    return factory


def floating_point(minimum=None, maximum=None, clamp=False):
    # type: (Optional[float], Optional[float], bool) -> Factory
    """Float factory maker."""
    if clamp and minimum is None and maximum is None:
        error = (
            "factory parameter 'clamp' was set to True, but no minimum and/or maximum "
            "provided"
        )
        raise ValueError(error)
    if minimum is not None:
        minimum = float(minimum)
    if maximum is not None:
        maximum = float(maximum)

    @Factory
    def factory(value):
        """Factory function."""
        value = float(value)
        if minimum is not None and value < minimum:
            if clamp:
                value = minimum
            else:
                error_msg = "minimum value is {}, got {}".format(minimum, value)
                raise ValueError(error_msg)
        if maximum is not None and value > maximum:
            if clamp:
                value = maximum
            else:
                error_msg = "maximum value is {}, got {}".format(minimum, value)
                raise ValueError(error_msg)
        return value

    return factory


def regex_match(pattern):
    # type: (str) -> Factory
    """String regex match factory."""
    compiled = re.compile(pattern)

    @Factory
    def factory(value):
        """Factory function."""
        value = str(value)
        if not re.match(compiled, value):
            error_msg = "'{}' does not match regex pattern '{}'".format(value, pattern)
            raise ValueError(error_msg)
        return value

    return factory


def regex_sub(pattern, repl):
    # type: (str, str) -> Factory
    """String regex sub factory."""
    compiled = re.compile(pattern)

    @Factory
    def factory(value):
        """Factory function."""
        value = str(value)
        return re.sub(compiled, repl, value)

    return factory


def curated(*curated_values):
    # type: (Tuple[Any, ...]) -> Factory
    """Curated values factory."""

    @Factory
    def factory(value):
        """Factory function."""
        if value not in curated_values:
            raise ValueError(
                "expected one of {}, got {}".format(curated_values, repr(value))
            )
        return value

    return factory
