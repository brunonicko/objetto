# -*- coding: utf-8 -*-
"""Immutable collection types."""

from abc import abstractmethod
from itertools import chain

from pyrsistent import pmap, pvector, pset
from slotted import SlottedHashable
from typing import TYPE_CHECKING, TypeVar, Generic, cast, overload

from six import iteritems, iterkeys, itervalues
from six.moves import collections_abc

from .interfaces import (
    InteractiveInterface,
    InteractiveDictInterface,
    InteractiveListInterface,
    InteractiveSetInterface,
)
from .custom_repr import custom_iterable_repr, custom_mapping_repr
from .list_operations import resolve_index, resolve_continuous_slice, pre_move

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

__all__ = ["Immutable", "ImmutableDict", "ImmutableList", "ImmutableSet"]

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_T = TypeVar("_T")
_INTERNAL_DICT_TYPE = type(pmap())  # type: Type[PMap]
_INTERNAL_LIST_TYPE = type(pvector())  # type: Type[PVector]
_INTERNAL_SET_TYPE = type(pset())  # type: Type[PSet]


class Immutable(SlottedHashable, InteractiveInterface):
    """Abstract immutable collection."""

    @abstractmethod
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        raise NotImplementedError()

    def __str__(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        """
        return self.__repr__()

    def __ne__(self, other):
        # type: (Any) -> bool
        """
        Compare for inequality.

        :param other: Other.
        :return: True if not equal.
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def copy(self):
        # type: () -> Immutable
        """
        Get copy.

        :return: Copy.
        """
        return self

    def clear(self):
        # type: () -> Immutable
        """
        Clear all keys and values.

        :return: New version.
        """
        return type(self)()

    @abstractmethod
    def find(self, **attributes):
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        """
        raise NotImplementedError()


class ImmutableDict(Immutable, InteractiveDictInterface, Generic[_KT, _VT]):
    """
    Immutable dictionary.

    .. code:: python

        >>> from objetto.utils.immutable import ImmutableDict

        >>> ImmutableDict({"a": 1, "b": 2})
        ImmutableDict({'a': 1, 'b': 2})

    :param initial: Initial values.
    """

    __slots__ = ("__internal", "__hash")

    def __init__(self, initial=()):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> None
        self.__hash = None  # type: Optional[int]
        initial_type = type(initial)
        if initial_type is _INTERNAL_DICT_TYPE:
            self.__internal = cast("PMap[_KT, _VT]", initial)
        elif initial_type is type(self):
            self.__internal = cast("ImmutableDict", initial).__internal
            self.__hash = cast("ImmutableDict", initial).__hash
        else:
            self.__internal = pmap(initial)

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        if self.__hash is None:
            self.__hash = hash(self.__internal)
        return self.__hash

    def __eq__(self, other):
        # type: (Any) -> bool
        """
        Compare for equality.

        :param other: Other.
        :return: True if equal.
        """
        if self is other:
            return True
        elif isinstance(other, ImmutableDict):
            return self.__internal == other.__internal
        else:
            return False

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_mapping_repr(
            self.__internal,
            prefix="{}({{".format(type(self).__name__),
            suffix="})",
            sorting=True,
            sort_key=lambda i: hash(i[0])
        )

    def __str__(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        """
        return self.__repr__()

    def __copy__(self):
        # type: () -> ImmutableDict
        """
        Get copy.

        :return: Copy.
        """
        return self

    def __getitem__(self, key):
        # type: (_KT) -> _VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        """
        return self.__internal[key]

    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self.__internal)

    def __iter__(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key in iterkeys(self.__internal):
            yield key

    def iteritems(self):
        # type: () -> Iterator[Tuple[_KT, _VT]]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key, value in iteritems(self.__internal):
            yield key, value

    def iterkeys(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in iterkeys(self.__internal):
            yield key

    def itervalues(self):
        # type: () -> Iterator[_VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in itervalues(self.__internal):
            yield value

    def find(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value or None if nothing was found.
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

    def discard(self, key):
        # type: (_KT) -> ImmutableDict
        """
        Discard key if it exists.

        :param key: Key.
        :return: New version.
        """
        return type(self)(self.__internal.discard(key))

    def remove(self, key):
        # type: (_KT) -> ImmutableDict
        """
        Delete existing key.

        :param key: Key.
        :return: New version.
        """
        return type(self)(self.__internal.remove(key))

    def set(self, key, value):
        # type: (_KT, _VT) -> ImmutableDict
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: New version.
        """
        return type(self)(self.__internal.set(key, value))

    def update(self, update):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> ImmutableDict
        """
        Update keys and values.

        :param update: Updates.
        :return: New version.
        """
        if isinstance(update, collections_abc.Mapping):
            return type(self)(self.__internal.update(update))
        else:
            return type(self)(self.__internal.update(pmap(update)))


class ImmutableList(Immutable, InteractiveListInterface, Generic[_T]):
    """
    Immutable list.

    .. code:: python

        >>> from objetto.utils.immutable import ImmutableList

        >>> ImmutableList(["a", "b", "c", "c"])
        ImmutableList(['a', 'b', 'c', 'c'])

    :param initial: Initial values.
    """

    __slots__ = ("__internal", "__hash")

    def __init__(self, initial=()):
        # type: (Iterable[_T]) -> None
        self.__hash = None  # type: Optional[int]
        initial_type = type(initial)
        if initial_type is _INTERNAL_LIST_TYPE:
            self.__internal = cast("PVector[_T]", initial)
        elif initial_type is type(self):
            self.__internal = cast("ImmutableList", initial).__internal
            self.__hash = cast("ImmutableList", initial).__hash
        else:
            self.__internal = pvector(initial)

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        if self.__hash is None:
            self.__hash = hash(self.__internal)
        return self.__hash

    def __eq__(self, other):
        # type: (Any) -> bool
        """
        Compare for equality.

        :param other: Other.
        :return: True if equal.
        """
        if self is other:
            return True
        elif isinstance(other, ImmutableList):
            return self.__internal == other.__internal
        else:
            return False

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_iterable_repr(
            self.__internal,
            prefix="{}([".format(type(self).__name__),
            suffix="])",
        )

    def __str__(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        """
        return self.__repr__()

    def __copy__(self):
        # type: () -> ImmutableList
        """
        Get copy.

        :return: Copy.
        """
        return self

    @overload
    def __getitem__(self, index):
        # type: (int) -> _T
        """
        Get value at index.

        :param index: Index.
        :return: Value.
        """
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> ImmutableList[_T]
        """
        Get values from slice.

        :param index: Slice.
        :return: Values.
        """
        pass

    def __getitem__(self, index):
        # type: (Union[int, slice]) -> Union[_T, ImmutableList[_T]]
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        if isinstance(index, slice):
            return type(self)(self.__internal[index])
        else:
            return self.__internal[index]

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self.__internal)

    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return resolve_index(len(self.__internal), index, clamp=clamp)

    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return resolve_continuous_slice(len(self.__internal), slc)

    def find(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value or None if nothing was found.
        :raises ValueError: No attributes provided or no match found.
        """
        if not attributes:
            error = "no attributes provided"
            raise ValueError(error)
        for value in self:
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

    def change(self, index, *values):
        # type: (int, _T) -> ImmutableList
        """
        Change value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: New version.
        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        index = self.resolve_index(index)
        stop = self.resolve_index(index + len(values) - 1) + 1
        pairs = chain.from_iterable(zip(range(index, stop), values))
        return type(self)(self.__internal.mset(*pairs))

    def append(self, value):
        # type: (_T) -> ImmutableList
        """
        Append value at the end.

        :param value: Value.
        :return: New version.
        """
        return type(self)(self.__internal.append(value))

    def extend(self, iterable):
        # type: (Iterable[_T]) -> ImmutableList
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: New version.
        """
        return type(self)(self.__internal.extend(iterable))

    def insert(self, index, *values):
        # type: (int, _T) -> ImmutableList
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: New version.
        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        if index == len(self.__internal):
            return self.extend(values)
        elif index == 0:
            return type(self)(pvector(values).extend(self.__internal))
        else:
            return type(self)(
                self.__internal[:index] + pvector(values) + self.__internal[index:]
            )

    def remove(self, value):
        # type: (_T) -> ImmutableList
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: New version.
        """
        return type(self)(self.__internal.remove(value))

    def reverse(self):
        # type: () -> ImmutableList
        """
        Reverse values.

        :return: New version.
        """
        return type(self)(reversed(self.__internal))

    def move(self, item, target_index):
        # type: (Union[slice, int], int) -> Any
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: New version.
        """

        # Pre-move checks.
        result = pre_move(len(self.__internal), item, target_index)
        if result is None:
            return self
        index, stop, target_index, post_index = result

        # Pop and re-insert values.
        values = self.__internal[index:stop]
        intermediary = self.__internal.delete(index, stop)

        if post_index == len(intermediary):
            return type(self)(intermediary.extend(values))
        elif post_index == 0:
            return type(self)(values.extend(intermediary))
        else:
            return type(self)(
                intermediary[:post_index] + values + intermediary[post_index:]
            )

    def sort(self, key=None, reverse=False):
        # type: (...) -> ImmutableList
        """
        Sort values.

        :param key: Sorting key function.
        :param reverse: Whether to reverse sort.
        :return: New version.
        """
        return type(self)(sorted(self.__internal, key=key, reverse=reverse))


class ImmutableSet(Immutable, InteractiveSetInterface, Generic[_T]):
    """
    Immutable set.

    .. code:: python

        >>> from objetto.utils.immutable import ImmutableSet

        >>> ImmutableSet([1, 2, 3, 3])
        ImmutableSet([1, 2, 3])

    :param initial: Initial values.
    """

    __slots__ = ("__internal", "__hash")

    def __init__(self, initial=()):
        # type: (Iterable[_T]) -> None
        self.__hash = None  # type: Optional[int]
        initial_type = type(initial)
        if initial_type is _INTERNAL_SET_TYPE:
            self.__internal = cast("PSet[_T]", initial)
        elif initial_type is type(self):
            self.__internal = cast("ImmutableSet", initial).__internal
            self.__hash = cast("ImmutableSet", initial).__hash
        else:
            self.__internal = pset(initial)

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        if self.__hash is None:
            self.__hash = hash(self.__internal)
        return self.__hash

    def __eq__(self, other):
        # type: (Any) -> bool
        """
        Compare for equality.

        :param other: Other.
        :return: True if equal.
        """
        if self is other:
            return True
        elif isinstance(other, ImmutableSet):
            return self.__internal == other.__internal
        else:
            return False

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_iterable_repr(
            self.__internal,
            prefix="{}([".format(type(self).__name__),
            suffix="])",
            sorting=True,
            sort_key=lambda v: hash(v)
        )

    def __str__(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        """
        return self.__repr__()

    def __copy__(self):
        # type: () -> ImmutableSet
        """
        Get copy.

        :return: Copy.
        """
        return self

    def __contains__(self, value):
        # type: (object) -> bool
        """
        Get whether contains value.

        :param value: Value.
        :return: True if contains.
        """
        return value in self.__internal

    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self.__internal)

    def __iter__(self):
        # type: () -> Iterator[_T]
        """
        Iterate over values.

        :return: Value iterator.
        """
        for value in self.__internal:
            yield value

    def find(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value or None if nothing was found.
        :raises ValueError: No attributes provided or no match found.
        """
        if not attributes:
            error = "no attributes provided"
            raise ValueError(error)
        for value in self:
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

    def issubset(self, iterable):
        # type: (Iterable[_T]) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self.__internal.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable[_T]) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self.__internal.issuperset(iterable)

    def add(self, *values):
        # type: (_T) -> ImmutableSet
        """
        Add value(s).

        :param values: Value(s).
        :return: New version.
        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        return type(self)(self.__internal.update(values))

    def difference(self, iterable):
        # type: (Iterable[_T]) -> ImmutableSet
        """
        Get difference.

        :param iterable: Iterable.
        :return: New version.
        """
        return type(self)(self.__internal.difference(iterable))

    def discard(self, value):
        # type: (_T) -> ImmutableSet
        """
        Discard value if it exists.

        :param value: Value.
        :return: New version.
        """
        return type(self)(self.__internal.discard(value))

    def remove(self, value):
        # type: (_T) -> ImmutableSet
        """
        Remove existing value.

        :param value: Value.
        :return: New version.
        """
        return type(self)(self.__internal.remove(value))

    def replace(self, value, new_value):
        # type: (_T, _T) -> ImmutableSet
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :param new_value: New value.
        :return: New version.
        """
        return type(self)(self.__internal.remove(value).add(new_value))

    def intersection(self, iterable):
        # type: (Iterable[_T]) -> ImmutableSet
        """
        Get intersection.

        :param iterable: Iterable.
        :return: New version.
        """
        return type(self)(self.__internal.intersection(iterable))

    def symmetric_difference(self, iterable):
        # type: (Iterable[_T]) -> ImmutableSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: New version.
        """
        return type(self)(self.__internal.symmetric_difference(pset(iterable)))

    def union(self, iterable):
        # type: (Iterable[_T]) -> ImmutableSet
        """
        Get union.

        :param iterable: Iterable.
        :return: New version.
        """
        return type(self)(self.__internal.union(iterable))

    def update(self, iterable):
        # type: (Iterable[_T]) -> ImmutableSet
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: New version.
        """
        return type(self)(self.__internal.update(iterable))
