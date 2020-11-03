# -*- coding: utf-8 -*-
"""Immutable container types."""

from pyrsistent import pmap, pvector, pset
from slotted import SlottedMapping, SlottedSequence, SlottedSet, SlottedHashable
from typing import TYPE_CHECKING, TypeVar, Generic, cast, overload

from six import iteritems
from six.moves import collections_abc

from .custom_repr import custom_iterable_repr, custom_mapping_repr

if TYPE_CHECKING:
    from pyrsistent.typing import PMap, PVector, PSet
    from typing import (
        Any,
        Callable,
        Type,
        Mapping,
        Iterable,
        Tuple,
        Union,
        Iterator,
        Sequence,
        Set,
        Optional,
    )

__all__ = ["ImmutableDict", "ImmutableList", "ImmutableSet"]


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_T = TypeVar("_T")
_INTERNAL_DICT_TYPE = type(pmap())  # type: Type[PMap]
_INTERNAL_LIST_TYPE = type(pvector())  # type: Type[PVector]
_INTERNAL_SET_TYPE = type(pset())  # type: Type[PSet]


class ImmutableDict(Generic[_KT, _VT], SlottedHashable, SlottedMapping):
    """Immutable dictionary."""

    __slots__ = ("__internal", "__hash")

    def __init__(self, initial=()):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> None
        self.__hash = None
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
        if self.__hash is None:
            self.__hash = hash(self.__internal)
        return self.__hash

    def __eq__(self, other):
        # type: (Any) -> bool
        if self is other:
            return True
        elif isinstance(other, ImmutableDict):
            return self.__internal == other.__internal
        else:
            return False

    def __repr__(self):
        # type: () -> str
        return custom_mapping_repr(
            self.__internal,
            prefix="{}({{".format(type(self).__name__),
            suffix="})",
        )

    def __str__(self):
        return self.__repr__()

    def __copy__(self):
        # type: () -> ImmutableDict
        return self

    def __getitem__(self, key):
        # type: (_KT) -> _VT
        return self.__internal[key]

    def __len__(self):
        # type: () -> int
        return len(self.__internal)

    def __iter__(self):
        # type: () -> Iterator[_KT]
        for key in self.__internal:
            yield key

    def copy(self):
        # type: () -> ImmutableDict
        return self

    def clear(self):
        # type: () -> ImmutableDict
        return type(self)()

    def discard(self, key):
        # type: (_KT) -> ImmutableDict
        return type(self)(self.__internal.discard(key))

    def remove(self, key):
        # type: (_KT) -> ImmutableDict
        return type(self)(self.__internal.remove(key))

    def set(self, key, value):
        # type: (_KT, _VT) -> ImmutableDict
        return type(self)(self.__internal.set(key, value))

    def update(self, update):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> ImmutableDict
        if isinstance(update, collections_abc.Mapping):
            return type(self)(self.__internal.update(update))
        else:
            return type(self)(self.__internal.update(pmap(update)))


class ImmutableList(Generic[_T], SlottedHashable, SlottedSequence):
    """Immutable list."""

    __slots__ = ("__internal", "__hash")

    def __init__(self, initial=()):
        # type: (Iterable[_T]) -> None
        self.__hash = None
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
        if self.__hash is None:
            self.__hash = hash(self.__internal)
        return self.__hash

    def __eq__(self, other):
        # type: (Any) -> bool
        if self is other:
            return True
        elif isinstance(other, ImmutableList):
            return self.__internal == other.__internal
        else:
            return False

    def __repr__(self):
        # type: () -> str
        return custom_iterable_repr(
            self.__internal,
            prefix="{}([".format(type(self).__name__),
            suffix="])",
        )

    def __str__(self):
        return self.__repr__()

    def __copy__(self):
        # type: () -> ImmutableList
        return self

    @overload
    def __getitem__(self, index):
        # type: (int) -> _T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> ImmutableList
        pass

    def __getitem__(self, index):
        # type: (Union[int, slice]) -> Union[_T, ImmutableList]
        if isinstance(index, slice):
            return type(self)(self.__internal[index])
        else:
            return self.__internal[index]

    def __len__(self):
        # type: () -> int
        return len(self.__internal)

    def copy(self):
        # type: () -> ImmutableList
        return self

    def clear(self):
        # type: () -> ImmutableList
        return type(self)()

    def append(self, value):
        # type: (_T) -> ImmutableList
        return type(self)(self.__internal.append(value))

    def extend(self, iterable):
        # type: (Iterable[_T]) -> ImmutableList
        return type(self)(self.__internal.extend(iterable))

    def insert(self, index, value):
        # type: (int, _T) -> ImmutableList
        if index == len(self.__internal):
            return self.append(value)
        elif index == 0:
            return type(self)(pvector((value,)) + self.__internal)
        else:
            return type(self)(
                self.__internal[:index] + pvector((value,)) + self.__internal[index:]
            )

    def remove(self, value):
        # type: (_T) -> ImmutableList
        return type(self)(self.__internal.remove(value))

    def reverse(self):
        # type: () -> ImmutableList
        return type(self)(reversed(self.__internal))

    def sort(self, key=None, reverse=False):
        # type: (...) -> ImmutableList
        return type(self)(sorted(self.__internal, key=key, reverse=reverse))


class ImmutableSet(Generic[_T], SlottedHashable, SlottedSet):
    """Immutable set."""

    __slots__ = ("__internal", "__hash")

    def __init__(self, initial=()):
        # type: (Iterable[_T]) -> None
        self.__hash = None
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
        if self.__hash is None:
            self.__hash = hash(self.__internal)
        return self.__hash

    def __eq__(self, other):
        # type: (Any) -> bool
        if self is other:
            return True
        elif isinstance(other, ImmutableSet):
            return self.__internal == other.__internal
        else:
            return False

    def __repr__(self):
        # type: () -> str
        return custom_iterable_repr(
            self.__internal,
            prefix="{}({{".format(type(self).__name__),
            suffix="})",
        )

    def __str__(self):
        return self.__repr__()

    def __copy__(self):
        # type: () -> ImmutableSet
        return self

    def __contains__(self, value):
        # type: (object) -> bool
        return value in self.__internal

    def __len__(self):
        # type: () -> int
        return len(self.__internal)

    def __iter__(self):
        # type: () -> Iterator[_T]
        for value in self.__internal:
            yield value

    def add(self, value):
        # type: (_T) -> ImmutableSet
        return type(self)(self.__internal.add(value))

    def copy(self):
        # type: () -> ImmutableSet
        return self

    def clear(self):
        # type: () -> ImmutableSet
        return type(self)()

    def difference(self, iterable):
        # type: (Iterable[_T]) -> ImmutableSet
        return type(self)(self.__internal.difference(iterable))

    def discard(self, value):
        # type: (_T) -> ImmutableSet
        return type(self)(self.__internal.discard(value))

    def intersection(self, iterable):
        # type: (Iterable[_T]) -> ImmutableSet
        return type(self)(self.__internal.intersection(iterable))

    def issubset(self, iterable):
        # type: (Iterable[_T]) -> bool
        return self.__internal.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable[_T]) -> bool
        return self.__internal.issuperset(iterable)

    def remove(self, value):
        # type: (_T) -> ImmutableSet
        return type(self)(self.__internal.remove(value))

    def symmetric_difference(self, iterable):
        # type: (Iterable[_T]) -> ImmutableSet
        return type(self)(self.__internal.symmetric_difference(iterable))

    def union(self, iterable):
        # type: (Iterable[_T]) -> ImmutableSet
        return type(self)(self.__internal.union(iterable))

    def update(self, iterable):
        # type: (Iterable[_T]) -> ImmutableSet
        return type(self)(self.__internal.update(iterable))
