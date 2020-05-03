# -*- coding: utf-8 -*-
"""Abstract container object."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from six import with_metaclass
from typing import Any, Optional, Callable, Iterable, Union
from slotted import Slotted

from .._base.constants import MISSING, DELETED
from .._components.events import EventPhase

from ..utils.type_checking import UnresolvedType as UType
from ..utils.recursive_repr import recursive_repr
from ..utils.type_checking import assert_is_unresolved_type, assert_is_instance

from .base import BaseObjectEvent, BaseObjectMeta, BaseObject

__all__ = [
    "ContainerObjectEvent",
    "ContainerObjectMeta",
    "ContainerObject",
    "ContainerObjectParameters",
]


class ContainerObjectEvent(BaseObjectEvent):
    """Container object event."""


class ContainerObjectMeta(BaseObjectMeta):
    """Metaclass for 'ContainerObject'."""


class ContainerObject(with_metaclass(ContainerObjectMeta, BaseObject)):
    """Object that stores values in a container."""

    __slots__ = ("__type_name", "__state", "__parameters", "__reaction")
    __state_type__ = NotImplemented

    def __init__(
        self,
        value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        value_factory=None,  # type: Optional[Callable]
        exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        default_module=None,  # type: Optional[str]
        accepts_none=None,  # type: Optional[bool]
        comparable=True,  # type: bool
        represented=False,  # type: bool
        printed=True,  # type: bool
        parent=True,  # type: bool
        history=True,  # type: bool
        type_name=None,  # type: Optional[str]
        reaction=None,  # type: Optional[Callable]
    ):
        # type: (...) -> None
        """Initialize with parameters."""
        super(ContainerObject, self).__init__()

        # Type name
        self.__type_name = (str(type_name) if type_name is not None else None) or None

        # State
        state_type = type(self).__state_type__
        if state_type is NotImplemented:
            error = "cannot instantiate abstract class '{}'".format(type(self).__name__)
            raise NotImplementedError(error)
        self.__state = state_type()

        # Parameters
        self.__parameters = ContainerObjectParameters(
            value_type=value_type,
            value_factory=value_factory,
            exact_value_type=exact_value_type,
            default_module=default_module,
            accepts_none=accepts_none,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=parent,
            history=history,
        )

        # Reaction
        if reaction is not None and not callable(reaction):
            error = "specified 'reaction' of type '{}' is not callable".format(
                type(reaction).__name__
            )
            raise TypeError(error)
        self.__reaction = reaction
        if reaction is not None:
            self.events.__add_listener__(self, force=True)

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """Get representation."""
        return "<{} {}{}>".format(
            self.type_name,
            hex(id(self)),
            (
                " | {}".format(self.__state)
                if self._parameters.represented and self.__state
                else ""
            ),
        )

    @recursive_repr
    def __str__(self):
        # type: () -> str
        """Get string representation."""
        return "<{}{}>".format(
            self.type_name,
            (
                " {}".format(self.__state)
                if self._parameters.printed and self.__state
                else ""
            ),
        )

    def __eq__(self, other):
        # type: (ContainerObject) -> bool
        """Compare for equality."""
        if self is other:
            return True
        if not isinstance(other, type(self)):
            return False
        if not self.comparable or not other.comparable:
            return False
        self_state = self.__state
        other_state = other.__state
        return self_state == other_state

    def __react__(self, event, phase):
        # type: (BaseObjectEvent, EventPhase) -> None
        """React to an event."""
        if self.__reaction is not None:
            self.__reaction(self, event, phase)

    @property
    def default_type_name(self):
        # type: () -> str
        """Default type name."""
        raise NotImplementedError()

    @property
    def type_name(self):
        # type: () -> str
        """Type name."""
        return self.__type_name or self.default_type_name

    def __get_state__(self):
        # type: () -> collections_abc.Container
        """Get internal state."""
        return self.__state

    @property
    def _parameters(self):
        # type: () -> ContainerObjectParameters
        """Container parameters."""
        return self.__parameters


class ContainerObjectParameters(Slotted):
    """Holds parameter values for a container obj."""

    __slots__ = (
        "__value_type",
        "__value_factory",
        "__exact_value_type",
        "__default_module",
        "__accepts_none",
        "__comparable",
        "__represented",
        "__printed",
        "__parent",
        "__history",
    )

    def __init__(
        self,
        value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        value_factory=None,  # type: Optional[Callable]
        exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        default_module=None,  # type: Optional[str]
        accepts_none=None,  # type: Optional[bool]
        comparable=True,  # type: bool
        represented=False,  # type: bool
        printed=True,  # type: bool
        parent=True,  # type: bool
        history=True,  # type: bool
    ):

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

        # Store 'comparable', 'represented' and 'printed'
        self.__comparable = bool(comparable)
        self.__represented = bool(represented)
        self.__printed = bool(printed)

        # Store 'parent' and 'history'
        self.__parent = bool(parent)
        self.__history = bool(history)

    def fabricate(self, value, accepts_missing=False, accepts_deleted=False):
        # type: (Any, bool, bool) -> Any
        """Fabricate value by running it through type checks and factory."""
        if self.value_factory is not None:
            value = self.value_factory(value)

        if self.value_type is not None:
            assert_is_instance(
                value,
                self.value_type,
                optional=self.accepts_none,
                exact=False,
                default_module_name=self.default_module,
            )
        elif self.exact_value_type is not None:
            assert_is_instance(
                value,
                self.exact_value_type,
                optional=self.accepts_none,
                exact=True,
                default_module_name=self.default_module,
            )
        elif not self.accepts_none and value is None:
            error = "can't use None"
            raise TypeError(error)

        if not accepts_missing and value is MISSING:
            error = "can't use special value {}".format(value)
            raise ValueError(error)
        if not accepts_deleted and value is DELETED:
            error = "can't use special value {}".format(value)
            raise ValueError(error)

        return value

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
    def comparable(self):
        # type: () -> bool
        """Whether values should be leveraged in '__eq__' method."""
        return self.__comparable

    @property
    def represented(self):
        # type: () -> bool
        """Whether values should be displayed in the result of '__repr__'."""
        return self.__represented

    @property
    def printed(self):
        # type: () -> bool
        """Whether values should be displayed in the result of '__str__'."""
        return self.__printed

    @property
    def parent(self):
        # type: () -> bool
        """Whether obj used as value should attach as a child."""
        return self.__parent

    @property
    def history(self):
        # type: () -> bool
        """Whether obj used as value should be assigned to the same history."""
        return self.__history
