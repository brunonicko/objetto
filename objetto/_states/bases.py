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

    :param initial: Initial values.
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
        """
        raise NotImplementedError()

    @final
    def __copy__(self):
        # type: (_BS) -> _BS
        """
        Get copy.

        :return: Copy.
        """
        return self

    @abstractmethod
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        raise NotImplementedError()

    @final
    def __str__(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        """
        return self.__repr__()

    @property
    @abstractmethod
    def _internal(self):
        # type: () -> Union[PMap, PVector, PSet]
        """Internal state."""
        return self.__internal
