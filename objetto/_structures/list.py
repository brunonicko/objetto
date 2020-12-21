# -*- coding: utf-8 -*-
"""List structures."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import with_metaclass

from .._bases import BaseInteractiveList, BaseMutableList, BaseProtectedList, final
from ..utils.custom_repr import custom_iterable_repr
from ..utils.recursive_repr import recursive_repr
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
    """
    Metaclass for :class:`objetto.bases.BaseListStructure`.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructureMeta`

    Inherited by:
      - :class:`objetto.data.ListDataMeta`
      - :class:`objetto.objects.ListObjectMeta`
    """


class BaseListStructure(
    with_metaclass(
        BaseListStructureMeta,
        BaseAuxiliaryStructure[T],
        BaseProtectedList[T],
    )
):
    """
    Base list structure.

    Metaclass:
      - :class:`objetto.bases.BaseListStructureMeta`

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructure`
      - :class:`objetto.bases.BaseProtectedList`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveListStructure`
      - :class:`objetto.bases.BaseMutableListStructure`
      - :class:`objetto.data.ListData`
      - :class:`objetto.objects.ListObject`
    """

    __slots__ = ()

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        :rtype: str
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
        :rtype: collections.abc.Iterator
        """
        return reversed(self._state)

    @final
    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        :rtype: int
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Values iterator.
        :rtype: collections.abc.Iterator
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
        :rtype: bool
        """
        return value in self._state

    @final
    def count(self, value):
        # type: (Any) -> int
        """
        Count number of occurrences of a value.

        :return: Number of occurrences.
        :rtype: int
        """
        return self._state.count(value)

    @final
    def index(self, value, start=None, stop=None):
        # type: (Any, Optional[int], Optional[int]) -> int
        """
        Get index of a value.

        :param value: Value.

        :param start: Start index.
        :type start: int or None

        :param stop: Stop index.
        :type stop: int or None

        :return: Index of value.
        :rtype: int

        :raises ValueError: Provided stop but did not provide start.
        """
        return self._state.index(value, start=start, stop=stop)

    @final
    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :type index: int

        :param clamp: Whether to clamp between zero and the length.
        :type clamp: bool

        :return: Resolved index.
        :rtype: int

        :raises IndexError: Index out of range.
        """
        return self._state.resolve_index(index, clamp=clamp)

    @final
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :type slc: slice

        :return: Index and stop.
        :rtype: tuple[int, int]

        :raises IndexError: Slice is noncontinuous.
        """
        return self._state.resolve_continuous_slice(slc)

    @property
    @abstractmethod
    def _state(self):
        # type: () -> ListState[T]
        """
        Internal state.

        :rtype: objetto.states.ListState

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseInteractiveListStructure(
    BaseListStructure[T],
    BaseInteractiveAuxiliaryStructure[T],
    BaseInteractiveList[T],
):
    """
    Base interactive list structure.

    Inherits from:
      - :class:`objetto.bases.BaseListStructure`
      - :class:`objetto.bases.BaseInteractiveAuxiliaryStructure`
      - :class:`objetto.bases.BaseInteractiveList`

    Inherited By:
      - :class:`objetto.data.InteractiveListData`
    """

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableListStructure(
    BaseMutableList[T],
    BaseListStructure[T],
    BaseMutableAuxiliaryStructure[T],
):
    """
    Base mutable list structure.

    Inherits from:
      - :class:`objetto.bases.BaseMutableList`
      - :class:`objetto.bases.BaseListStructure`
      - :class:`objetto.bases.BaseMutableAuxiliaryStructure`

    Inherited By:
      - :class:`objetto.objects.MutableListObject`
    """

    __slots__ = ()
