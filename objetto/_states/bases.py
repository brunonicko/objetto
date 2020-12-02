# -*- coding: utf-8 -*-
"""Immutable state types."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, cast

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from .._bases import BaseHashable, BaseInteractiveCollection, final

if TYPE_CHECKING:
    from typing import Any, Optional, Type, Union

    from pyrsistent.typing import PMap, PSet, PVector

__all__ = ["BaseState"]


T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.


# noinspection PyTypeChecker
_BS = TypeVar("_BS", bound="BaseState")


class BaseState(BaseHashable, BaseInteractiveCollection[T]):
    """
    Base immutable state.

    Inherits from:
      - :class:`objetto.bases.BaseHashable`
      - :class:`objetto.bases.BaseInteractiveCollection`

    Inherited By:
      - :class:`objetto.states.DictState`
      - :class:`objetto.states.ListState`
      - :class:`objetto.states.SetState`

    :param initial: Initial values.

    :raises NotImplementedError: Abstract methods not implemented.
    """

    __slots__ = ("__hash", "__internal")

    @classmethod
    @abstractmethod
    def _make(cls, internal):
        # type: (Type[_BS], Any) -> _BS
        """
        Make new state by directly setting the internal state.

        :param internal: Internal state.

        :return: State.
        :rtype: objetto.bases.BaseState
        """
        self = cast("_BS", cls.__new__(cls))
        self.__internal = internal
        self.__hash = None
        return self

    @staticmethod
    @abstractmethod
    def _make_internal(initial):
        # type: (Any) -> Union[PMap, PVector, PSet]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        raise NotImplementedError()

    @abstractmethod
    def __init__(self, initial=()):
        # type: (Any) -> None
        self.__internal = self._make_internal(initial)
        self.__hash = None  # type: Optional[int]

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        :rtype: int
        """
        if self.__hash is None:
            self.__hash = hash(self._internal)
        return self.__hash

    @abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.

        :return: True if equal.
        :rtype: bool

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @final
    def __copy__(self):
        # type: (_BS) -> _BS
        """
        Get copy.

        :return: Copy.
        :rtype: objetto.bases.BaseState
        """
        return self

    @abstractmethod
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        :rtype: str

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    def __str__(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        :rtype: str
        """
        return self.__repr__()

    @property
    @abstractmethod
    def _internal(self):
        # type: () -> Union[PMap, PVector, PSet]
        """Internal values."""
        return self.__internal
