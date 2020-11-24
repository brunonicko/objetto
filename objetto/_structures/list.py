# -*- coding: utf-8 -*-
"""List structures."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import with_metaclass

from .._bases import BaseInteractiveList, BaseMutableList, BaseProtectedList, final
from ..utils.custom_repr import custom_iterable_repr
from .bases import (
    BaseAuxiliaryStructure,
    BaseAuxiliaryStructureMeta,
    BaseInteractiveAuxiliaryStructure,
    BaseMutableAuxiliaryStructure,
)

if TYPE_CHECKING:
    from typing import Any, Iterator, Optional, Tuple

    from .._states import ListState

__all__ = [
    "BaseListStructureMeta",
    "BaseListStructure",
    "BaseInteractiveListStructure",
    "BaseMutableListStructure",
]


T = TypeVar("T")  # Any type.


# noinspection PyAbstractClass
class BaseListStructureMeta(BaseAuxiliaryStructureMeta):
    """Metaclass for :class:`ListStructure`."""


class BaseListStructure(
    with_metaclass(
        BaseListStructureMeta,
        BaseAuxiliaryStructure[T],
        BaseProtectedList[T],
    )
):
    """Base list structure."""

    __slots__ = ()

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        if type(self)._relationship.represented:
            return custom_iterable_repr(
                self._state,
                prefix="{}([".format(type(self).__fullname__),
                suffix="])",
            )
        else:
            return "<{}>".format(type(self).__fullname__)

    @final
    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._state)

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> ListState[T]
        pass

    @final
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        return self._state[index]

    @final
    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in self._state:
            yield value

    @final
    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :return: True if contains.
        """
        return value in self._state

    @final
    def count(self, value):
        # type: (Any) -> int
        """
        Count number of occurrences of a value.

        :return: Number of occurrences.
        """
        return self._state.count(value)

    @final
    def index(self, value, start=None, stop=None):
        # type: (Any, Optional[int], Optional[int]) -> int
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :return: Index of value.
        :raises ValueError: Provided stop but did not provide start.
        """
        return self._state.index(value, start=start, stop=stop)

    @final
    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return self._state.resolve_index(index, clamp=clamp)

    @final
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return self._state.resolve_continuous_slice(slc)

    @property
    @abstractmethod
    def _state(self):
        # type: () -> ListState[T]
        """Internal state."""
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseInteractiveListStructure(
    BaseListStructure[T],
    BaseInteractiveAuxiliaryStructure[T],
    BaseInteractiveList[T],
):
    """Base interactive list structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableListStructure(
    BaseListStructure[T],
    BaseMutableAuxiliaryStructure[T],
    BaseMutableList[T],
):
    """Base mutable list structure."""

    __slots__ = ()
