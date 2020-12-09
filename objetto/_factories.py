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
    "Boolean",
]


class BaseFactory(Base):
    """
    Base callable factory object.

    Inherits from:
      - :class:`objetto.bases.Base`

    Inherited By:
      - :class:`objetto.factories.MultiFactory`
      - :class:`objetto.factories.Integer`
      - :class:`objetto.factories.FloatingPoint`
      - :class:`objetto.factories.RegexMatch`
      - :class:`objetto.factories.RegexSub`
      - :class:`objetto.factories.String`
      - :class:`objetto.factories.Curated`
      - :class:`objetto.factories.Boolean`
    """

    __slots__ = ("__factories",)

    @abstractmethod
    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        """
        Call with input value and optional keyword arguments.

        :param value: Input value.

        :param kwargs: Keyword arguments.

        :return: Output value.
        """
        raise NotImplementedError()

    def __add__(self, other):
        # type: (Union[BaseFactory, FactoryType, LazyFactory]) -> MultiFactory
        """
        Add with another factory.

        :param other: Another factory.
        :type other: objetto.bases.BaseFactoryor str or collections.abc.Callable or None

        :return: Multi factory with added factories.
        :rtype: objetto.factories.MultiFactory
        """
        with ReraiseContext(TypeError, "adding factories together"):
            if not isinstance(other, string_types):
                assert_is_callable(other)
        return MultiFactory((self, other))


class MultiFactory(BaseFactory):
    """
    Adds multiple factories together.

    Inherits from:
      - :class:`objetto.bases.BaseFactory`

    :param factories: Factories to be added together.
    :type factories: collections.abc.Iterable[objetto.bases.BaseFactory or \
 collections.abc.Callable or function or str or None]
    """

    __slots__ = ("__factories",)

    def __init__(
        self,
        factories,  # type: Iterable[Union[BaseFactory, FactoryType, LazyFactory]]
        module=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        self.__factories = tuple(
            format_factory(r, module=module) for r in factories if r is not None
        )

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        """
        Call with input value and optional keyword arguments.

        :param value: Input value.

        :param kwargs: Keyword arguments.

        :return: Output value.
        """
        for factory in self.factories:
            value = run_factory(factory, args=(value,), kwargs=kwargs)
        return value

    def __add__(self, other):
        # type: (Union[BaseFactory, FactoryType, LazyFactory]) -> MultiFactory
        """
        Add with another factory.

        :param other: Another factory.
        :type other: objetto.bases.BaseFactoryor str or collections.abc.Callable or None

        :return: Multi factory with added factories.
        :rtype: objetto.factories.MultiFactory
        """
        if isinstance(other, MultiFactory):
            return MultiFactory(self.__factories + other.__factories)
        else:
            return MultiFactory(self.__factories + (other,))

    @property
    def factories(self):
        # type: () -> Tuple[Union[BaseFactory, FactoryType, LazyFactory], ...]
        """
        Factories.

        :return: tuple[objetto.bases.BaseFactory or \
 collections.abc.Callable or function or str]
        """
        return self.__factories


class Integer(BaseFactory):
    """
    Integer factory.

    Inherits from:
      - :class:`objetto.bases.BaseFactory`

    :param minimum: Minimum.
    :type minimum: int or None

    :param maximum: Maximum.
    :type maximum: int or None

    :param clamp_minimum: Whether to clamp to minimum value instead of erroring.
    :type clamp_minimum: bool

    :param clamp_maximum: Whether to clamp to maximum value instead of erroring.
    :type clamp_maximum: bool

    :param accepts_none: Whether to accept None as a value.
    :type accepts_none: bool

    :raises ValueError: Invalid parameter value.
    """

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
        """
        Call with input value and optional keyword arguments.

        :param value: Input value.
        :type value: int or None

        :param kwargs: Keyword arguments.

        :return: Output value.
        :rtype: int or None

        :raises ValueError: Value out of bounds.
        """
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
        # type: () -> Optional[int]
        """
        Minimum.

        :rtype: int or None
        """
        return self.__minimum

    @property
    def maximum(self):
        # type: () -> Optional[int]
        """
        Maximum.

        :rtype: int or None
        """
        return self.__maximum

    @property
    def clamp_minimum(self):
        # type: () -> bool
        """
        Whether to clamp to minimum value instead of erroring.

        :rtype: bool
        """
        return self.__clamp_minimum

    @property
    def clamp_maximum(self):
        # type: () -> bool
        """
        Whether to clamp to maximum value instead of erroring.

        :rtype: bool
        """
        return self.__clamp_maximum

    @property
    def accepts_none(self):
        # type: () -> bool
        """
        Whether to accept None as a value.

        :rtype: bool
        """
        return self.__accepts_none


class FloatingPoint(BaseFactory):
    """
    Floating point factory.

    Inherits from:
      - :class:`objetto.bases.BaseFactory`

    :param minimum: Minimum.
    :type minimum: float or None

    :param maximum: Maximum.
    :type maximum: float or None

    :param clamp_minimum: Whether to clamp to minimum value instead of erroring.
    :type clamp_minimum: bool

    :param clamp_maximum: Whether to clamp to maximum value instead of erroring.
    :type clamp_maximum: bool

    :param accepts_none: Whether to accept None as a value.
    :type accepts_none: bool

    :raises ValueError: Invalid parameter value.
    """

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
        """
        Call with input value and optional keyword arguments.

        :param value: Input value.
        :type value: float or None

        :param kwargs: Keyword arguments.

        :return: Output value.
        :rtype: float or None

        :raises ValueError: Value out of bounds.
        """
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
        # type: () -> Optional[float]
        """
        Minimum.

        :rtype: float or None
        """
        return self.__minimum

    @property
    def maximum(self):
        # type: () -> Optional[float]
        """
        Maximum.

        :rtype: float or None
        """
        return self.__maximum

    @property
    def clamp_minimum(self):
        # type: () -> bool
        """
        Whether to clamp to minimum value instead of erroring.

        :rtype: bool
        """
        return self.__clamp_minimum

    @property
    def clamp_maximum(self):
        # type: () -> bool
        """
        Whether to clamp to maximum value instead of erroring.

        :rtype: bool
        """
        return self.__clamp_maximum

    @property
    def accepts_none(self):
        # type: () -> bool
        """
        Whether to accept None as a value.

        :rtype: bool
        """
        return self.__accepts_none


class String(BaseFactory):
    """
    String factory.

    Inherits from:
      - :class:`objetto.bases.BaseFactory`

    :param accepts_none: Whether to accept None.
    :type accepts_none: bool
    """

    __slots__ = ("__accepts_none",)

    def __init__(self, accepts_none=False):
        # type: (bool) -> None
        self.__accepts_none = bool(accepts_none)

    def __call__(self, value, **kwargs):
        """
        Call with input value and optional keyword arguments.

        :param value: Input value.
        :type value: str or None

        :param kwargs: Keyword arguments.

        :return: Output value.
        :rtype: str or None

        :raises ValueError: Value out of bounds.
        """
        if value is None and self.__accepts_none:
            return value
        if not isinstance(value, string_types):
            return str(value)
        else:
            return value

    @property
    def accepts_none(self):
        # type: () -> bool
        """
        Whether to accept None.

        :rtype: bool
        """
        return self.__accepts_none


class RegexMatch(String):
    """
    Regex match check factory.

    Inherits from:
      - :class:`objetto.factories.String`

    :param pattern: Regex pattern.
    :type pattern: str

    :param accepts_none: Whether to accept None.
    :type accepts_none: bool
    """

    __slots__ = ("__pattern", "__compiled_pattern")

    def __init__(self, pattern, accepts_none=False):
        # type: ("Union[str, bytes]", bool) -> None
        super(RegexMatch, self).__init__(accepts_none=accepts_none)
        self.__pattern = cast("Union[str, bytes]", pattern)
        self.__compiled_pattern = re_compile(pattern)  # type: Pattern

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        """
        Call with input value and optional keyword arguments.

        :param value: Input value.
        :type value: str or None

        :param kwargs: Keyword arguments.

        :return: Output value.
        :rtype: str or None

        :raises ValueError: Value out of bounds.
        """
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
        """
        Regex pattern.

        :rtype: str
        """
        return self.__pattern

    @property
    def compiled_pattern(self):
        # type: () -> Pattern
        """
        Compiled regex pattern.

        :rtype: re.Pattern
        """
        return self.__compiled_pattern


class RegexSub(String):
    """
    Regex substitution factory.

    Inherits from:
      - :class:`objetto.factories.String`

    :param pattern: Regex pattern.
    :type pattern: str

    :param repl: Substitution.
    :type repl: str

    :param accepts_none: Whether to accept None.
    :type accepts_none: bool
    """

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
        """
        Call with input value and optional keyword arguments.

        :param value: Input value.
        :type value: str or None

        :param kwargs: Keyword arguments.

        :return: Output value.
        :rtype: str or None

        :raises ValueError: Value out of bounds.
        """
        value = super(RegexSub, self).__call__(value, **kwargs)
        return re_sub(self.compiled_pattern, self.repl, value)

    @property
    def pattern(self):
        # type: () -> "Union[str, bytes]"
        """
        Regex pattern.

        :rtype: str
        """
        return self.__pattern

    @property
    def compiled_pattern(self):
        # type: () -> Pattern
        """
        Compiled regex pattern.

        :rtype: re.Pattern
        """
        return self.__compiled_pattern

    @property
    def repl(self):
        """
        Substitution.

        :rtype: str
        """
        return self.__repl


class Curated(BaseFactory):
    """
    Curated values factory.

    Inherits from:
      - :class:`objetto.bases.BaseFactory`

    :param values: Accepted values.
    """

    __slots__ = ("__values",)

    def __init__(self, *values):
        # type: (Any) -> None
        self.__values = values

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        """
        Call with input value and optional keyword arguments.

        :param value: Input value.

        :param kwargs: Keyword arguments.

        :return: Output value.
        """
        if value not in self.values:
            error = "expected one of {}, got {}".format(self.values, repr(value))
            raise ValueError(error)
        return value

    @property
    def values(self):
        """
        Accepted values.

        :rtype: tuple
        """
        return self.__values


class Boolean(BaseFactory):
    """
    Boolean factory.

    Inherits from:
      - :class:`objetto.bases.BaseFactory`
    """

    __slots__ = ()

    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> bool
        """
        Call with input value and optional keyword arguments.

        :param value: Input value.

        :param kwargs: Keyword arguments.

        :return: Output value (True or False).
        :rtype: bool
        """
        return bool(value)
