# -*- coding: utf-8 -*-
"""Default factories."""

import re
from typing import Any, Optional, Callable, Tuple

from .utils.partial import Partial

__all__ = [
    "int_factory",
    "float_factory",
    "regex_match_factory",
    "regex_sub_factory",
    "curated_factory",
]


def concatenated_factories(*factories):
    # type: (Tuple[Callable, ...]) -> Callable
    """Concatenate multiple factories into one."""
    return sum(Partial(f) for f in factories)


def int_factory(minimum=None, maximum=None, clamp=False):
    # type: (Optional[int], Optional[int], bool) -> Callable
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


def float_factory(minimum=None, maximum=None, clamp=False):
    # type: (Optional[float], Optional[float], bool) -> Callable
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


def regex_match_factory(pattern):
    # type: (str) -> Callable
    """String regex match factory."""
    compiled = re.compile(pattern)

    def factory(value):
        """Factory function."""
        value = str(value)
        if not re.match(compiled, value):
            error_msg = "'{}' does not match regex pattern '{}'".format(value, pattern)
            raise ValueError(error_msg)

    return factory


def regex_sub_factory(pattern, repl):
    # type: (str, str) -> Callable
    """String regex sub factory."""
    compiled = re.compile(pattern)

    def factory(value):
        """Factory function."""
        value = str(value)
        return re.sub(compiled, repl, value)

    return factory


def curated_factory(*curated_values):
    # type: (Tuple[Any, ...]) -> Callable
    """Curated values factory."""

    def factory(value):
        """Factory function."""
        if value not in curated_values:
            raise ValueError(
                "expected one of {}, got {}".format(curated_values, repr(value))
            )
        return value

    return factory
