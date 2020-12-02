# -*- coding: utf-8 -*-
"""Factories."""

from abc import abstractmethod
from re import compile as re_compile
from re import match as re_match
from re import sub as re_sub
from typing import TYPE_CHECKING, cast

from six import string_types

from ._bases import Base
from .utils.factoring import format_factory, run_factory
from .utils.reraise_context import ReraiseContext
from .utils.type_checking import assert_is_callable, assert_is_instance

if TYPE_CHECKING:
    from re import Pattern
    from typing import Any, Callable, Iterable, Optional, Tuple, Union

    from .utils.factoring import LazyFactory

    FactoryType = Union[Callable[[Any, Any], Any], "BaseFactory"]

__all__ = [
    "BaseFactory",
    "MultiFactory",
    "Integer",
    "FloatingPoint",
    "RegexMatch",
    "RegexSub",
    "String",
    "Curated",
]


class BaseFactory(Base):
    """Base callable factory object."""

    __slots__ = ("__factories",)

    @abstractmethod
    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        raise NotImplementedError()

    def __add__(self, other):
        # type: (Union[BaseFactory, FactoryType, LazyFactory]) -> MultiFactory
        """Add with another factory."""
        with ReraiseContext(TypeError, "adding factories together"):
            if not isinstance(other, string_types):
                assert_is_callable(other)
        return MultiFactory((self, other))


class MultiFactory(BaseFactory):
    """Adds multiple factories together."""

    __slots__ = ("__factories",)

    def __init__(
        self,
        factories,  # type: Iterable[Union[BaseFactory, FactoryType, LazyFactory]]
        module=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        self.__factories = tuple(format_factory(r, module=module) for r in factories)

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        for factory in self.factories:
            value = run_factory(factory, args=(value,), kwargs=kwargs)
        return value

    def __add__(self, other):
        # type: (Union[BaseFactory, FactoryType, LazyFactory]) -> MultiFactory
        """Add with another factory."""
        if isinstance(other, MultiFactory):
            return MultiFactory(self.__factories + other.__factories)
        else:
            return MultiFactory(self.__factories + (other,))

    @property
    def factories(self):
        # type: () -> Tuple[Union[BaseFactory, FactoryType, LazyFactory], ...]
        return self.__factories


class Integer(BaseFactory):
    """Integer factory."""

    __slots__ = (
        "__minimum",
        "__maximum",
        "__clamp_minimum",
        "__clamp_maximum",
        "__accepts_none",
    )

    def __init__(
        self,
        minimum=None,  # type: Optional[int]
        maximum=None,  # type: Optional[int]
        clamp_minimum=False,  # type: bool
        clamp_maximum=False,  # type: bool
        accepts_none=False,  # type: bool
    ):
        # type: (...) -> None
        if clamp_minimum and minimum is None:
            error = "parameter 'clamp_minimum' was set to True, but no minimum provided"
            raise ValueError(error)
        if clamp_maximum and maximum is None:
            error = "parameter 'clamp_maximum' was set to True, but no maximum provided"
            raise ValueError(error)

        if minimum is not None:
            minimum = int(minimum)
        if maximum is not None:
            maximum = int(maximum)

        self.__minimum = minimum
        self.__maximum = maximum
        self.__clamp_minimum = bool(clamp_minimum)
        self.__clamp_maximum = bool(clamp_maximum)
        self.__accepts_none = bool(accepts_none)

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        if value is None and self.__accepts_none:
            return value
        value = int(value)
        if self.minimum is not None and value < self.minimum:
            if self.clamp_minimum:
                value = self.minimum
            else:
                error_msg = "minimum value is {}, got {}".format(self.minimum, value)
                raise ValueError(error_msg)
        if self.maximum is not None and value > self.maximum:
            if self.clamp_maximum:
                value = self.maximum
            else:
                error_msg = "maximum value is {}, got {}".format(self.minimum, value)
                raise ValueError(error_msg)
        return value

    @property
    def minimum(self):
        return self.__minimum

    @property
    def maximum(self):
        return self.__maximum

    @property
    def clamp_minimum(self):
        return self.__clamp_minimum

    @property
    def clamp_maximum(self):
        return self.__clamp_maximum

    @property
    def accepts_none(self):
        return self.__accepts_none


class FloatingPoint(BaseFactory):
    """Floating point factory."""

    __slots__ = (
        "__minimum",
        "__maximum",
        "__clamp_minimum",
        "__clamp_maximum",
        "__accepts_none",
    )

    def __init__(
        self,
        minimum=None,  # type: Optional[float]
        maximum=None,  # type: Optional[float]
        clamp_minimum=False,  # type: bool
        clamp_maximum=False,  # type: bool
        accepts_none=False,  # type: bool
    ):
        # type: (...) -> None
        if clamp_minimum and minimum is None:
            error = "parameter 'clamp_minimum' was set to True, but no minimum provided"
            raise ValueError(error)
        if clamp_maximum and maximum is None:
            error = "parameter 'clamp_maximum' was set to True, but no maximum provided"
            raise ValueError(error)

        if minimum is not None:
            minimum = float(minimum)
        if maximum is not None:
            maximum = float(maximum)

        self.__minimum = minimum
        self.__maximum = maximum
        self.__clamp_minimum = bool(clamp_minimum)
        self.__clamp_maximum = bool(clamp_maximum)
        self.__accepts_none = bool(accepts_none)

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        if value is None and self.__accepts_none:
            return value
        value = float(value)
        if self.minimum is not None and value < self.minimum:
            if self.clamp_minimum:
                value = self.minimum
            else:
                error_msg = "minimum value is {}, got {}".format(self.minimum, value)
                raise ValueError(error_msg)
        if self.maximum is not None and value > self.maximum:
            if self.clamp_maximum:
                value = self.maximum
            else:
                error_msg = "maximum value is {}, got {}".format(self.minimum, value)
                raise ValueError(error_msg)
        return value

    @property
    def minimum(self):
        return self.__minimum

    @property
    def maximum(self):
        return self.__maximum

    @property
    def clamp_minimum(self):
        return self.__clamp_minimum

    @property
    def clamp_maximum(self):
        return self.__clamp_maximum

    @property
    def accepts_none(self):
        return self.__accepts_none


class String(BaseFactory):
    """
    String factory.

    :param accepts_none: Whether accepts None.
    """

    __slots__ = ("__accepts_none",)

    def __init__(self, accepts_none=False):
        # type: (bool) -> None
        self.__accepts_none = bool(accepts_none)

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        if value is None and self.__accepts_none:
            return value
        if not isinstance(value, string_types):
            return str(value)
        else:
            return value

    @property
    def accepts_none(self):
        # type: () -> bool
        """Whether accepts None."""
        return self.__accepts_none


class RegexMatch(String):
    """
    Regex match check factory.

    :param pattern: Regex pattern.
    :param accepts_none: Whether accepts None.
    """

    __slots__ = ("__pattern", "__compiled_pattern")

    def __init__(self, pattern, accepts_none=False):
        # type: ("Union[str, bytes]", bool) -> None
        super(RegexMatch, self).__init__(accepts_none=accepts_none)
        self.__pattern = cast("Union[str, bytes]", pattern)
        self.__compiled_pattern = re_compile(pattern)  # type: Pattern

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        value = super(RegexMatch, self).__call__(value, **kwargs)
        if value is None:
            return value
        if not re_match(self.compiled_pattern, value):
            error_msg = "'{}' does not match regex pattern '{}'".format(
                value, str(self.pattern)
            )
            raise ValueError(error_msg)
        return value

    @property
    def pattern(self):
        # type: () -> "Union[str, bytes]"
        """Regex pattern."""
        return self.__pattern

    @property
    def compiled_pattern(self):
        # type: () -> Pattern
        """Compiled regex pattern."""
        return self.__compiled_pattern


class RegexSub(String):
    """Regex substitution factory."""

    __slots__ = ("__pattern", "__compiled_pattern", "__repl", "__accepts_none")

    def __init__(self, pattern, repl, accepts_none=False):
        # type: (str, str, bool) -> None
        super(RegexSub, self).__init__(accepts_none=accepts_none)
        with ReraiseContext(TypeError, "'pattern' parameter"):
            assert_is_instance(pattern, string_types)
        with ReraiseContext(TypeError, "'repl' parameter"):
            assert_is_instance(repl, string_types)
        self.__pattern = pattern
        self.__compiled_pattern = re_compile(pattern)
        self.__repl = repl

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        value = super(RegexSub, self).__call__(value, **kwargs)
        return re_sub(self.compiled_pattern, self.repl, value)

    @property
    def pattern(self):
        return self.__pattern

    @property
    def compiled_pattern(self):
        return self.__compiled_pattern

    @property
    def repl(self):
        return self.__repl


class Curated(BaseFactory):
    """Curated values factory."""

    __slots__ = ("__values",)

    def __init__(self, *values):
        # type: (Any) -> None
        self.__values = values

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        if value not in self.values:
            error = "expected one of {}, got {}".format(self.values, repr(value))
            raise ValueError(error)
        return value

    @property
    def values(self):
        return self.__values
