# -*- coding: utf-8 -*-
"""Base list classes."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from qualname import qualname  # type: ignore
from slotted import SlottedMutableSequence, SlottedSequence

from .bases import (
    BaseCollection,
    BaseInteractiveCollection,
    BaseMutableCollection,
    BaseProtectedCollection,
    final,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        Iterable,
        Iterator,
        MutableSequence,
        Optional,
        Sequence,
        Tuple,
        Union,
    )

__all__ = [
    "BaseList",
    "BaseProtectedList",
    "BaseInteractiveList",
    "BaseMutableList",
]


T = TypeVar("T")  # Any type.
T_co = TypeVar("T_co", covariant=True)  # Any type covariant containers.


class BaseList(BaseCollection[T_co], SlottedSequence):
    """
    Base list collection.

    Inherits from:
      - :class:`objetto.bases.BaseCollection`
      - :class:`slotted.SlottedSequence`
      - :class:`typing.Generic`

    Inherited By:
      - :class:`objetto.bases.BaseProtectedList`
    """

    __slots__ = ()

    def __hash__(self):
        """
        Prevent hashing (not hashable by default).

        :raises TypeError: Not hashable.
        """
        error = "unhashable type: '{}'".format(type(self).__fullname__)
        raise TypeError(error)

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

    @abstractmethod
    def __reversed__(self):
        # type: () -> Iterator[T_co]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        :rtype: collections.abc.Iterator

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @overload
    @abstractmethod
    def __getitem__(self, index):
        # type: (int) -> T_co
        pass

    @overload
    @abstractmethod
    def __getitem__(self, index):
        # type: (slice) -> Sequence[T_co]
        pass

    @abstractmethod
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :type index: int or slice

        :return: Value/values.
        :rtype: Any or tuple[Any]

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def count(self, value):
        # type: (Any) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.

        :return: Number of occurrences.
        :rtype: int

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
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
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
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
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :type slc: slice

        :return: Index and stop.
        :rtype: tuple[int, int]

        :raises IndexError: Slice is noncontinuous.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# noinspection PyCallByClass
type.__setattr__(BaseList, "__hash__", None)  # force non-hashable


# noinspection PyTypeChecker
_BPL = TypeVar("_BPL", bound="BaseProtectedList")


class BaseProtectedList(BaseList[T], BaseProtectedCollection[T]):
    """
    Base protected list collection.

    Inherits from:
      - :class:`objetto.bases.BaseList`
      - :class:`objetto.bases.BaseProtectedCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveList`
      - :class:`objetto.bases.BaseMutableList`
      - :class:`objetto.bases.BaseListStructure`
    """

    __slots__ = ()

    @abstractmethod
    def _insert(self, index, *values):
        # type: (_BPL, int, T) -> _BPL
        """
        Insert value(s) at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedList

        :raises ValueError: No values provided.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _append(self, value):
        # type: (_BPL, T) -> _BPL
        """
        Append value at the end.

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedList
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _extend(self, iterable):
        # type: (_BPL, Iterable[T]) -> _BPL
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedList
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _remove(self, value):
        # type: (_BPL, T) -> _BPL
        """
        Remove first occurrence of value.

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedList

        :raises ValueError: Value is not present.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _reverse(self):
        # type: (_BPL) -> _BPL
        """
        Reverse values.

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedList

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _move(self, item, target_index):
        # type: (_BPL, Union[slice, int], int) -> _BPL
        """
        Move values internally.

        :param item: Index/slice.
        :type item: int or slice

        :param target_index: Target index.
        :type target_index: int

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedList

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _delete(self, item):
        # type: (_BPL, Union[slice, int]) -> _BPL
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :type item: int or slice

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedList

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _update(self, index, *values):
        # type: (_BPL, int, T) -> _BPL
        """
        Update value(s) starting at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedList

        :raises ValueError: No values provided.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BIL = TypeVar("_BIL", bound="BaseInteractiveList")


# noinspection PyAbstractClass
class BaseInteractiveList(BaseProtectedList[T], BaseInteractiveCollection[T]):
    """
    Base interactive list collection.

    Inherits from:
      - :class:`objetto.bases.BaseProtectedList`
      - :class:`objetto.bases.BaseInteractiveCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveListStructure`
      - :class:`objetto.states.ListState`
    """

    __slots__ = ()

    @final
    def insert(self, index, *values):
        # type: (_BIL, int, T) -> _BIL
        """
        Insert value(s) at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveList

        :raises ValueError: No values provided.
        """
        return self._insert(index, *values)

    @final
    def append(self, value):
        # type: (_BIL, T) -> _BIL
        """
        Append value at the end.

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveList
        """
        return self._append(value)

    @final
    def extend(self, iterable):
        # type: (_BIL, Iterable[T]) -> _BIL
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveList
        """
        return self._extend(iterable)

    @final
    def remove(self, value):
        # type: (_BIL, T) -> _BIL
        """
        Remove first occurrence of value.

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveList

        :raises ValueError: Value is not present.
        """
        return self._remove(value)

    @final
    def reverse(self):
        # type: (_BIL) -> _BIL
        """
        Reverse values.

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveList
        """
        return self._reverse()

    @final
    def move(self, item, target_index):
        # type: (_BPL, Union[slice, int], int) -> _BPL
        """
        Move values internally.

        :param item: Index/slice.
        :type item: int or slice

        :param target_index: Target index.
        :type target_index: int

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveList
        """
        return self._move(item, target_index)

    @final
    def delete(self, item):
        # type: (_BPL, Union[slice, int]) -> _BPL
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :type item: int or slice

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveList
        """
        return self._delete(item)

    @final
    def update(self, index, *values):
        # type: (_BIL, int, T) -> _BIL
        """
        Update value(s) starting at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveList

        :raises ValueError: No values provided.
        """
        return self._update(index, *values)


class BaseMutableList(
    SlottedMutableSequence, BaseProtectedList[T], BaseMutableCollection[T]
):
    """
    Base mutable list collection.

    Inherits from:
      - :class:`slotted.SlottedMutableSequence`
      - :class:`objetto.bases.BaseProtectedList`
      - :class:`objetto.bases.BaseMutableCollection`

    Inherited By:
      - :class:`objetto.bases.BaseMutableListStructure`
      - :class:`objetto.objects.ProxyListObject`
    """

    __slots__ = ()

    @final
    def __iadd__(self, iterable):
        # type: (Iterable[T]) -> MutableSequence[T]
        """
        In place addition.

        :param iterable: Another iterable.
        :type iterable: collections.abc.Iterable

        :return: Added list.
        :rtype: objetto.bases.BaseMutableList
        """
        self._extend(iterable)
        return self

    @overload
    @abstractmethod
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    @abstractmethod
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T]
        pass

    @abstractmethod
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :type index: int or slice

        :return: Value/values.

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @overload
    @abstractmethod
    def __setitem__(self, index, value):
        # type: (int, T) -> None
        pass

    @overload
    @abstractmethod
    def __setitem__(self, slc, values):
        # type: (slice, Iterable[T]) -> None
        pass

    @abstractmethod
    def __setitem__(self, item, value):
        # type: (Union[int, slice], Union[T, Iterable[T]]) -> None
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :type item: int or slice

        :param value: Value/values.

        :raises IndexError: Slice is noncontinuous.
        :raises ValueError: Values length does not fit in slice.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @overload
    @abstractmethod
    def __delitem__(self, index):
        # type: (int) -> None
        pass

    @overload
    @abstractmethod
    def __delitem__(self, slc):
        # type: (slice) -> None
        pass

    @abstractmethod
    def __delitem__(self, item):
        # type: (Union[int, slice]) -> None
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :type item: int or slice

        :raises IndexError: Slice is noncontinuous.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def pop(self, index=-1):
        # type: (int) -> T
        """
        Pop value from index.

        :param index: Index.
        :type index: int

        :return: Value.

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()

    @final
    def insert(self, index, *values):
        # type: (int, T) -> None
        """
        Insert value(s) at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :raises ValueError: No values provided.
        """
        self._insert(index, *values)

    @final
    def append(self, value):
        # type: (T) -> None
        """
        Append value at the end.

        :param value: Value.
        """
        self._append(value)

    @final
    def extend(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable
        """
        self._extend(iterable)

    @final
    def remove(self, value):
        # type: (T) -> None
        """
        Remove first occurrence of value.

        :param value: Value.

        :raises ValueError: Value is not present.
        """
        self._remove(value)

    @final
    def reverse(self):
        # type: () -> None
        """Reverse values."""
        self._reverse()

    @final
    def move(self, item, target_index):
        # type: (Union[slice, int], int) -> None
        """
        Move values internally.

        :param item: Index/slice.
        :type item: int or slice

        :param target_index: Target index.
        :type target_index: int
        """
        self._move(item, target_index)

    @final
    def delete(self, item):
        # type: (_BPL, Union[slice, int]) -> None
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :type item: int or slice
        """
        self._delete(item)

    @final
    def update(self, index, *values):
        # type: (int, T) -> None
        """
        Update value(s) starting at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :raises ValueError: No values provided.
        """
        self._update(index, *values)
