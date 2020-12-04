# -*- coding: utf-8 -*-
"""Immutable list state."""

from itertools import chain
from typing import TYPE_CHECKING, TypeVar, cast, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from pyrsistent import pvector
from six import iteritems

from .._bases import BaseInteractiveList, final
from ..utils.custom_repr import custom_iterable_repr, custom_mapping_repr
from ..utils.list_operations import pre_move, resolve_continuous_slice, resolve_index
from ..utils.recursive_repr import recursive_repr
from .bases import BaseState

if TYPE_CHECKING:
    from typing import Any, Iterable, Iterator, Optional, Tuple, Type, Union

    from pyrsistent.typing import PVector

__all__ = ["ListState"]


T = TypeVar("T")  # Any type.


# noinspection PyTypeChecker
_LS = TypeVar("_LS", bound="ListState")


@final
class ListState(BaseState[T], BaseInteractiveList[T]):
    """
    Immutable list state.

    Inherits from:
      - :class:`objetto.bases.BaseState`
      - :class:`objetto.bases.BaseInteractiveList`

    :param initial: Initial values.
    :type initial: collections.abc.Iterable
    """

    __slots__ = ()

    @classmethod
    def _make(cls, internal=pvector()):
        # type: (Type[_LS], PVector[T]) -> _LS
        """
        Make new state by directly setting the internal state.

        :param internal: Internal state.
        :return: State.
        """
        return super(ListState, cls)._make(internal)

    @staticmethod
    def _make_internal(initial):
        # type: (Iterable[T]) -> PVector[T]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pvector(initial)

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        super(ListState, self).__init__(initial=initial)

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        :rtype: int
        """
        return super(ListState, self).__hash__()

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.

        :return: True if equal.
        :rtype: bool
        """
        if self is other:
            return True
        if not isinstance(other, collections_abc.Hashable):
            return self._internal == other
        if isinstance(other, ListState):
            return self._internal == other._internal
        return False

    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.

        :return: True if contains.
        :rtype: bool
        """
        return value in self._internal

    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Values iterator.
        :rtype: collections.abc.Iterator
        """
        for value in self._internal:
            yield value

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        :rtype: int
        """
        return len(self._internal)

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        :rtype: str
        """
        return custom_iterable_repr(
            self._internal,
            prefix="{}([".format(type(self).__fullname__),
            suffix="])",
        )

    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        :rtype: collections.abc.Iterator
        """
        return reversed(self._internal)

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> ListState[T]
        pass

    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :type index: int or slice

        :return: Value/values.
        :rtype: Any or objetto.states.ListState
        """
        if isinstance(index, slice):
            return self._make(self._internal[index])
        else:
            return self._internal[index]

    def _clear(self):
        # type: (_LS) -> _LS
        """
        Clear.

        :return: Transformed.
        :rtype: objetto.states.ListState
        """
        return self._make()

    def _insert(self, index, *values):
        # type: (_LS, int, T) -> _LS
        """
        Insert value(s) at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :rtype: objetto.states.ListState

        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        index = self.resolve_index(index, clamp=True)
        if index == len(self._internal):
            return self.extend(values)
        elif index == 0:
            return self._make(pvector(values) + self._internal)
        else:
            return self._make(
                self._internal[:index] + pvector(values) + self._internal[index:]
            )

    def _append(self, value):
        # type: (_LS, T) -> _LS
        """
        Append value at the end.

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.states.ListState
        """
        return self._make(self._internal.append(value))

    def _extend(self, iterable):
        # type: (_LS, Iterable[T]) -> _LS
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Transformed.
        :rtype: objetto.states.ListState
        """
        return self._make(self._internal.extend(iterable))

    def _remove(self, value):
        # type: (_LS, T) -> _LS
        """
        Remove first occurrence of value.

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.states.ListState

        :raises ValueError: Value is not present.
        """
        return self._make(self._internal.remove(value))

    def _reverse(self):
        # type: (_LS) -> _LS
        """
        Reverse values.

        :return: Transformed.
        :rtype: objetto.states.ListState
        """
        return self._make(pvector(reversed(self._internal)))

    def _move(self, item, target_index):
        # type: (_LS, Union[slice, int], int) -> _LS
        """
        Move values internally.

        :param item: Index/slice.
        :type item: int or slice

        :param target_index: Target index.
        :type target_index: int

        :return: Transformed.
        :rtype: objetto.states.ListState
        """
        result = pre_move(len(self._internal), item, target_index)
        if result is None:
            return self
        index, stop, target_index, post_index = result

        values = self._internal[index:stop]
        internal = self._internal.delete(index, stop)

        if post_index == len(internal):
            return self._make(internal.extend(values))
        elif post_index == 0:
            return self._make(pvector(values) + internal)
        else:
            return self._make(
                internal[:post_index] + pvector(values) + internal[post_index:]
            )

    def _delete(self, item):
        # type: (_LS, Union[slice, int]) -> _LS
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :type item: int or slice

        :return: Transformed.
        :rtype: objetto.states.ListState
        """
        if isinstance(item, slice):
            index, stop = self.resolve_continuous_slice(item)
            return self._make(self._internal.delete(index, stop))
        else:
            index = self.resolve_index(item)
            return self._make(self._internal.delete(index, None))

    def _update(self, index, *values):
        # type: (_LS, int, T) -> _LS
        """
        Update value(s) starting at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :rtype: objetto.states.ListState

        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        index = self.resolve_index(index)
        stop = self.resolve_index(index + len(values) - 1) + 1
        pairs = chain.from_iterable(zip(range(index, stop), values))
        new_internal = self._internal.mset(*pairs)  # type: ignore
        return self._make(new_internal)

    def count(self, value):
        # type: (Any) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.

        :return: Number of occurrences.
        :rtype: int
        """
        return self._internal.count(value)

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
        if start is None and stop is None:
            args = (value,)  # type: Tuple[Any, ...]
        elif start is not None and stop is None:
            args = (value, start)
        elif start is not None and stop is not None:
            args = (value, start, stop)
        else:
            error = "provided 'stop' argument but did not provide 'start'"
            raise ValueError(error)
        return self._internal.index(*args)

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
        return resolve_index(len(self._internal), index, clamp=clamp)

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
        return resolve_continuous_slice(len(self._internal), slc)

    def find_with_attributes(self, **attributes):
        # type: (Any) -> T
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.

        :return: Value that has matching attributes.

        :raises ValueError: No attributes provided or no match found.
        """
        if not attributes:
            error = "no attributes provided"
            raise ValueError(error)
        for value in self._internal:
            for a_name, a_value in iteritems(attributes):
                if not hasattr(value, a_name) or getattr(value, a_name) != a_value:
                    break
            else:
                return value
        error = "could not find a match for {}".format(
            custom_mapping_repr(
                attributes,
                prefix="(",
                template="{key}={value}",
                suffix=")",
                key_repr=str,
            ),
        )
        raise ValueError(error)

    @property
    def _internal(self):
        # type: () -> PVector[T]
        """Internal values."""
        return cast("PVector[T]", super(ListState, self)._internal)
