# -*- coding: utf-8 -*-
"""Abstract container model."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from six import with_metaclass, raise_from
from typing import Any, Optional, Callable, Iterable, Union

from ..utils.type_checking import UnresolvedType as UType
from ..utils.recursive_repr import recursive_repr
from ..utils.type_checking import assert_is_unresolved_type, assert_is_instance
from .base import ModelMeta, Model

__all__ = ["ContainerModelMeta", "ContainerModel"]


class ContainerModelMeta(ModelMeta):
    """Metaclass for 'ContainerModel'."""


class ContainerModel(with_metaclass(ContainerModelMeta, Model)):
    """Model that stores values in a mapping."""

    __slots__ = (
        "__state",
        "__value_type",
        "__value_factory",
        "__exact_value_type",
        "__default_module",
        "__accepts_none",
        "__represented",
        "__printed",
        "__parent",
        "__history",
    )
    __state_type__ = NotImplemented

    def __init__(
        self,
        value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        value_factory=None,  # type: Optional[Callable]
        exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        default_module=None,  # type: Optional[str]
        accepts_none=None,  # type: Optional[bool]
        represented=False,  # type: bool
        printed=True,  # type: bool
        parent=False,  # type: bool
        history=False,  # type: bool
    ):
        # type: (...) -> None
        """Initialize with parameters."""
        super(ContainerModel, self).__init__()

        # State
        state_type = type(self).__state_type__
        if state_type is NotImplemented:
            error = "cannot instantiate abstract class '{}'".format(type(self).__name__)
            raise NotImplementedError(error)
        self.__state = state_type()

        # Default module
        if default_module is None:
            self.__default_module = None
        else:
            self.__default_module = str(default_module)

        # Check, and store 'value_type', 'exact_value_type', and 'accepts_none'
        if value_type is not None and exact_value_type is not None:
            error = "cannot specify both 'value_type' and 'exact_value_type' arguments"
            raise ValueError(error)
        if value_type is not None:
            assert_is_unresolved_type(value_type)
            self.__value_type = value_type
            self.__exact_value_type = None
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else False
            )
        elif exact_value_type is not None:
            assert_is_unresolved_type(exact_value_type)
            self.__value_type = None
            self.__exact_value_type = exact_value_type
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else False
            )
        else:
            self.__value_type = None
            self.__exact_value_type = None
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else True
            )

        # Check and store 'value_factory'
        if value_factory is not None and not callable(value_factory):
            error = "expected a callable for 'value_factory', got '{}'".format(
                type(value_factory).__name__
            )
            raise TypeError(error)
        self.__value_factory = value_factory

        # Store 'represented' and 'printed'
        self.__represented = bool(represented)
        self.__printed = bool(printed)

        # Store 'parent' and 'history'
        self.__parent = bool(parent)
        self.__history = bool(history)

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """Get representation."""
        module = type(self).__module__
        return "<{}{} object at {}{}>".format(
            "{}.".format(module) if "_" not in module else "",
            type(self).__name__,
            hex(id(self)),
            " | {}".format(self.__state) if self.__represented and self.__state else "",
        )

    @recursive_repr
    def __str__(self):
        # type: () -> str
        """Get string representation."""
        return "<{}{}>".format(
            type(self).__name__,
            " {}".format(self.__state) if self.__printed and self.__state else ""
        )

    def __eq__(self, other):
        # type: (ContainerModel) -> bool
        """Compare for equality."""
        if not isinstance(other, type(self)):
            return False
        self_state = self.__state
        other_state = other.__state
        return self_state == other_state

    def __factory__(self, value):
        # type: (Any) -> Any
        """Fabricate value by running it through type checks and factory."""
        if self.__value_factory is not None:
            value = self.__value_factory(value)
        try:
            if self.__value_type is not None:
                assert_is_instance(
                    value,
                    self.__value_type,
                    optional=self.__accepts_none,
                    exact=False,
                    default_module_name=self.__default_module,
                )
            elif self.__exact_value_type is not None:
                assert_is_instance(
                    value,
                    self.__exact_value_type,
                    optional=self.__accepts_none,
                    exact=True,
                    default_module_name=self.__default_module,
                )
            elif not self.__accepts_none and value is None:
                error = "'{}' object does not accept None as a value".format(
                    type(self).__name__
                )
                raise TypeError(error)
        except TypeError as e:
            exc = TypeError("{} in '{}' object".format(e, type(self).__name__))
            raise_from(exc, None)
            raise exc
        return value

    def __get_state__(self):
        # type: () -> collections_abc.Container
        """Get internal state."""
        return self.__state

    @property
    def value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Value type."""
        return self.__value_type

    @property
    def value_factory(self):
        # type: () -> Optional[Callable]
        """Value factory."""
        return self.__value_factory

    @property
    def exact_value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Exact value type."""
        return self.__exact_value_type

    @property
    def default_module(self):
        # type: () -> Optional[str]
        """Default module name for type checking."""
        return self.__default_module

    @property
    def accepts_none(self):
        # type: () -> bool
        """Whether None can be accepted as a value."""
        return self.__accepts_none

    @property
    def represented(self):
        # type: () -> bool
        """Whether this is leveraged in state's '__repr__' method."""
        return self.__represented

    @property
    def printed(self):
        # type: () -> bool
        """Whether this is leveraged in state's '__str__' method."""
        return self.__printed

    @property
    def parent(self):
        # type: () -> bool
        """Whether model used as value should attach as a child."""
        return self.__parent

    @property
    def history(self):
        # type: () -> bool
        """Whether model used as value should be assigned to the same history."""
        return self.__history
