# -*- coding: utf-8 -*-
"""Immutable state types."""

from abc import abstractmethod
from itertools import chain
from typing import TYPE_CHECKING, TypeVar, Generic, cast, overload

from pyrsistent import pmap, pvector, pset
from six import iteritems, iterkeys, itervalues, raise_from

from ._bases import (
    final,
    BaseHashable,
    BaseInteractiveCollection,
    BaseInteractiveDict,
    BaseInteractiveList,
    BaseInteractiveSet,
)
from .utils.custom_repr import custom_iterable_repr, custom_mapping_repr
from .utils.list_operations import resolve_index, resolve_continuous_slice, pre_move
from .utils.list_operations import resolve_index, resolve_continuous_slice

if TYPE_CHECKING:
    from pyrsistent.typing import PMap, PVector, PSet
    from typing import (
        Any,
        Type,
        Mapping,
        Iterable,
        Tuple,
        Union,
        Iterator,
        Optional,
    )

__all__ = ["BaseState", "DictState", "ListState", "SetState"]


_T = TypeVar("_T")  # Any type.
_KT = TypeVar("_KT")  # Key type.
_VT = TypeVar("_VT")  # Value type.

if TYPE_CHECKING:
    DictInternal = PMap[_KT, _VT]
    ListInternal = PVector[_T]
    SetInternal = PSet[_T]


_BS = TypeVar("_BS", bound="BaseState")


class BaseState(BaseHashable, BaseInteractiveCollection[_T]):
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
        self = cls.__new__(cls)
        self.__internal = internal
        self.__hash = None
        return self

    @staticmethod
    @abstractmethod
    def _make_internal(initial):
        # type: (Any) -> Any
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
        # type: () -> Any
        """Internal state."""
        return self.__internal


_DS = TypeVar("_DS", bound="DictState")


@final
class DictState(BaseState[_KT], BaseInteractiveDict[_KT, _VT]):
    __slots__ = ()

    @classmethod
    def _make(cls, internal=pmap()):
        # type: (Type[_DS], DictInternal) -> _DS
        """
        Make new state by directly setting the internal state.

        :param internal: Internal state.
        :return: State.
        """
        return super(DictState, cls)._make(internal)

    @staticmethod
    def _make_internal(initial):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> DictInternal
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pmap(initial)

    def __init__(self, initial=()):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> None
        super(DictState, self).__init__(initial=initial)
    
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return super(DictState, self).__hash__()

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if self is other:
            return True
        if isinstance(other, DictState):
            return self._internal == other._internal
        if isinstance(other, dict):
            return self._internal == other
        return False

    def __contains__(self, key):
        # type: (Any) -> bool
        """
        Get whether key is present.

        :param key: Key.
        :return: True if contains.
        """
        return key in self._internal

    def __iter__(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in self.iterkeys():
            yield key

    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self._internal)
    
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_mapping_repr(
            self._internal,
            prefix="{}({{".format(type(self).__fullname__),
            suffix="})",
            sorting=True,
            sort_key=lambda i: hash(i[0])
        )
    
    def __reversed__(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        """
        return reversed(list(self.__iter__()))

    def __getitem__(self, key):
        # type: (_KT) -> _VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Key is not present.
        """
        return self._internal[key]

    def _clear(self):
        # type: (_DS) -> _DS
        """
        Clear.

        :return: Transformed.
        """
        return self._make()
    
    def _discard(self, key):
        # type: (_DS, _KT) -> _DS
        """
        Discard key if it exists.

        :param key: Key.
        :return: New version.
        """
        return self._make(self._internal.discard(key))

    def _remove(self, key):
        # type: (_DS, _KT) -> _DS
        """
        Delete existing key.

        :param key: Key.
        :return: New version.
        :raises KeyError: Key is not present.
        """
        return self._make(self._internal.remove(key))

    def _set(self, key, value):
        # type: (_DS, _KT, _VT) -> _DS
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: New version.
        """
        return self._make(self._internal.set(key, value))

    def _update(self, update):
        # type: (_DS, Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> _DS
        """
        Update keys and values.

        :param update: Updates.
        :return: Transformed.
        """
        return self._make(self._internal.update(dict(update)))

    def get(self, key, fallback=None):
        # type: (_KT, Any) -> Union[_VT, Any]
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._internal.get(key, fallback)

    def iteritems(self):
        # type: () -> Iterator[Tuple[_KT, _VT]]
        """
        Iterate over items.

        :return: Items iterator.
        """
        for key, value in iteritems(self._internal):
            yield key, value

    def iterkeys(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in iterkeys(self._internal):
            yield key

    def itervalues(self):
        # type: () -> Iterator[_VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in itervalues(self._internal):
            yield value

    def items(self):  # type: ignore
        # type: () -> ListState[Tuple[_KT, _VT]]
        """
        Get items.

        :return: Items.
        """
        return ListState(self.iteritems())

    def keys(self):  # type: ignore
        # type: () -> ListState[_KT]
        """
        Get keys.

        :return: Keys.
        """
        return ListState(self.iterkeys())

    def values(self):  # type: ignore
        # type: () -> ListState[_VT]
        """
        Get values.

        :return: Values.
        """
        return ListState(self.itervalues())

    def find_with_attributes(self, **attributes):
        # type: (Any) -> _VT
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        if not attributes:
            error = "no attributes provided"
            raise ValueError(error)
        for value in self.itervalues():
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
        # type: () -> DictInternal
        """Internal state."""
        return super(DictState, self)._internal


_LS = TypeVar("_LS", bound="ListState")


@final
class ListState(BaseState[_T], BaseInteractiveList[_T]):
    __slots__ = ()

    @classmethod
    def _make(cls, internal=pvector()):
        # type: (Type[_LS], ListInternal) -> _LS
        """
        Make new state by directly setting the internal state.

        :param internal: Internal state.
        :return: State.
        """
        return super(ListState, cls)._make(internal)

    @staticmethod
    def _make_internal(initial):
        # type: (Iterable[_T]) -> ListInternal
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pvector(initial)

    def __init__(self, initial=()):
        # type: (Iterable[_T]) -> None
        super(ListState, self).__init__(initial=initial)

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return super(ListState, self).__hash__()

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if self is other:
            return True
        if isinstance(other, ListState):
            return self._internal == other._internal
        if isinstance(other, list):
            return self._internal == other
        return False

    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :return: True if contains.
        """
        return value in self._internal

    def __iter__(self):
        # type: () -> Iterator[_T]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in self._internal:
            yield value

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self._internal)
    
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_iterable_repr(
            self._internal,
            prefix="{}([".format(type(self).__fullname__),
            suffix="])",
        )

    def __reversed__(self):
        # type: () -> Iterator[_T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._internal)

    @overload
    def __getitem__(self, index):  # type: ignore
        # type: (int) -> _T
        pass

    @overload
    def __getitem__(self, index):  # type: ignore
        # type: (slice) -> ListState[_T]
        pass

    def __getitem__(self, index):  # type: ignore
        # type: (Union[int, slice]) -> Union[_T, ListState[_T]]
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        if isinstance(index, slice):
            return ListState(self._internal[index])
        else:
            return self._internal[index]

    def _clear(self):
        # type: (_LS) -> _LS
        """
        Clear.

        :return: Transformed.
        """
        return self._make()
    
    def _insert(self, index, *values):
        # type: (_LS, int, _T) -> _LS
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        if not values:
            return self
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
        # type: (_LS, _T) -> _LS
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        return self._make(self._internal.append(value))

    def _extend(self, iterable):
        # type: (_LS, Iterable[_T]) -> _LS
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._make(self._internal.extend(iterable))

    def _remove(self, value):
        # type: (_LS, _T) -> _LS
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return self._make(self._internal.remove(value))

    def _reverse(self):
        # type: (_LS) -> _LS
        """
        Reverse values.

        :return: Transformed.
        """
        return self._make(pvector(reversed(self._internal)))

    def _change(self, index, *values):
        # type: (_LS, int, _T) -> _LS
        """
        Change value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
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

        :return: Number of occurrences.
        """
        return self._internal.count(value)

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
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return resolve_index(len(self._internal), index, clamp=clamp)

    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return resolve_continuous_slice(len(self._internal), slc)
    
    def find_with_attributes(self, **attributes):
        # type: (Any) -> _T
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
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
        # type: () -> ListInternal
        """Internal state."""
        return super(ListState, self)._internal


_SS = TypeVar("_SS", bound="SetState")


@final
class SetState(BaseState[_T], BaseInteractiveSet[_T]):
    __slots__ = ()

    @classmethod
    def _make(cls, internal=pset()):
        # type: (Type[_SS], SetInternal) -> _SS
        """
        Make new state by directly setting the internal state.

        :param internal: Internal state.
        :return: State.
        """
        return super(SetState, cls)._make(internal)

    @staticmethod
    def _make_internal(initial):
        # type: (Iterable[_T]) -> SetInternal
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pset(initial)

    def __init__(self, initial=()):
        # type: (Iterable[_T]) -> None
        super(SetState, self).__init__(initial=initial)

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return super(SetState, self).__hash__()

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if self is other:
            return True
        if isinstance(other, SetState):
            return self._internal == other._internal
        if isinstance(other, set):
            return self._internal == other
        return False

    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :return: True if contains.
        """
        return value in self._internal

    def __iter__(self):
        # type: () -> Iterator[_T]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for key in self._internal:
            yield key

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self._internal)
    
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_iterable_repr(
            self._internal,
            prefix="{}([".format(type(self).__name__),
            suffix="])",
            sorting=True,
            sort_key=lambda v: hash(v)
        )

    def _clear(self):
        # type: (_SS) -> _SS
        """
        Clear.

        :return: Transformed.
        """
        return self._make()

    def _add(self, value):
        # type: (_SS, _T) -> _SS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        return self._make(self._internal.add(value))

    def _discard(self, value):
        # type: (_SS, _T) -> _SS
        """
        Discard value if it exists.

        :param value: Value.
        :return: Transformed.
        """
        return self._make(self._internal.discard(value))

    def _remove(self, value):
        # type: (_SS, _T) -> _SS
        """
        Remove existing value.

        :param value: Value.
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        return self._make(self._internal.remove(value))

    def _replace(self, value, new_value):
        # type: (_SS, _T, _T) -> _SS
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :param new_value: New value.
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        return self._make(self._internal.remove(value).add(new_value))

    def _update(self, iterable):
        # type: (_SS, Iterable[_T]) -> _SS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._make(self._internal.update(iterable))
    
    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return self._internal.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._internal.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._internal.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return SetState._make(self._internal.intersection(iterable))

    def difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return SetState._make(self._internal.difference(iterable))

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return SetState._make(self._internal.symmetric_difference(iterable))

    def union(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return SetState._make(self._internal.union(iterable))

    def find_with_attributes(self, **attributes):
        # type: (Any) -> _T
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
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
        # type: () -> SetInternal
        """Internal state."""
        return super(SetState, self)._internal
