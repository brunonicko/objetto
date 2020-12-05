# -*- coding: utf-8 -*-
"""Base set classes."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from slotted import SlottedMutableSet, SlottedSet

from .bases import (
    BaseCollection,
    BaseInteractiveCollection,
    BaseMutableCollection,
    BaseProtectedCollection,
    Generic,
    final,
)

if TYPE_CHECKING:
    from typing import AbstractSet, Iterable

__all__ = [
    "BaseSet",
    "BaseProtectedSet",
    "BaseInteractiveSet",
    "BaseMutableSet",
]


T = TypeVar("T")  # Any type.
T_co = TypeVar("T_co", covariant=True)  # Any type covariant containers.


class BaseSet(SlottedSet, BaseCollection[T_co], Generic[T_co]):
    """
    Base set collection.

    Inherits from:
      - :class:`objetto.bases.BaseCollection`
      - :class:`slotted.SlottedSet`
      - :class:`typing.Generic`

    Inherited By:
      - :class:`objetto.bases.BaseProtectedSet`
    """

    __slots__ = ()

    def __hash__(self):
        """
        Prevent hashing (not hashable by default).

        :raises TypeError: Not hashable.
        """
        error = "unhashable type: '{}'".format(type(self).__fullname__)
        raise TypeError(error)

    @final
    def __le__(self, other):
        # type: (AbstractSet) -> bool
        """
        Less equal operator (self <= other).

        :param other: Another set or any object.
        :type other: collections.abc.Set

        :return: True if considered less equal.
        :rtype: bool
        """
        if not isinstance(other, collections_abc.Set):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__le__(other)

    @final
    def __lt__(self, other):
        # type: (AbstractSet) -> bool
        """
        Less than operator: `self < other`.

        :param other: Another set or any object.
        :type other: collections.abc.Set

        :return: True if considered less than.
        :rtype: bool
        """
        if not isinstance(other, collections_abc.Set):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__lt__(other)

    @final
    def __gt__(self, other):
        # type: (AbstractSet) -> bool
        """
        Greater than operator: `self > other`.

        :param other: Another set or any object.
        :type other: collections.abc.Set

        :return: True if considered greater than.
        :rtype: bool
        """
        if not isinstance(other, collections_abc.Set):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__gt__(other)

    @final
    def __ge__(self, other):
        # type: (AbstractSet) -> bool
        """
        Greater equal operator: `self >= other`.

        :param other: Another set or any object.
        :type other: collections.abc.Set

        :return: True if considered greater equal.
        :rtype: bool
        """
        if not isinstance(other, collections_abc.Set):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__ge__(other)

    @final
    def __and__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get intersection: `self & other`.

        :param other: Iterable or any other object.
        :type other: collections.abc.Iterable

        :return: Intersection or `NotImplemented` if not an iterable.
        :rtype: objetto.bases.BaseSet
        """
        if not isinstance(other, collections_abc.Iterable):
            return NotImplemented
        return self.intersection(other)

    @final
    def __rand__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get intersection: `other & self`.

        :param other: Iterable or any other object.
        :type other: collections.abc.Iterable

        :return: Intersection or `NotImplemented` if not an iterable.
        :rtype: objetto.bases.BaseSet
        """
        return self.__and__(other)

    @final
    def __sub__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get difference: `self - other`.

        :param other: Iterable or any other object.
        :type other: collections.abc.Iterable

        :return: Difference or `NotImplemented` if not an iterable.
        :rtype: objetto.bases.BaseSet
        """
        if not isinstance(other, collections_abc.Iterable):
            return NotImplemented
        return self.difference(other)

    @final
    def __rsub__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get inverse difference: `other - self`.

        :param other: Iterable or any other object.
        :type other: collections.abc.Iterable

        :return: Inverse difference or `NotImplemented` if not an iterable.
        :rtype: objetto.bases.BaseSet
        """
        if not isinstance(other, collections_abc.Iterable):
            return NotImplemented
        return self.inverse_difference(other)

    @final
    def __or__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get union: `self | other`.

        :param other: Iterable or any other object.
        :type other: collections.abc.Iterable

        :return: Union or `NotImplemented` if not an iterable.
        :rtype: objetto.bases.BaseSet
        """
        if not isinstance(other, collections_abc.Iterable):
            return NotImplemented
        return self.union(other)

    @final
    def __ror__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get union: `other | self`.

        :param other: Iterable or any other object.
        :type other: collections.abc.Iterable

        :return: Union or `NotImplemented` if not an iterable.
        :rtype: objetto.bases.BaseSet
        """
        return self.__or__(other)

    @final
    def __xor__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get symmetric difference: `self ^ other`.

        :param other: Iterable or any other object.
        :type other: collections.abc.Iterable

        :return: Symmetric difference or `NotImplemented` if not an iterable.
        :rtype: objetto.bases.BaseSet
        """
        if not isinstance(other, collections_abc.Iterable):
            return NotImplemented
        return self.symmetric_difference(other)

    @final
    def __rxor__(self, other):
        # type: (Iterable) -> BaseSet
        """
        Get symmetric difference: `other ^ self`.

        :param other: Iterable or any other object.
        :type other: collections.abc.Iterable

        :return: Symmetric difference or `NotImplemented` if not an iterable.
        :rtype: objetto.bases.BaseSet
        """
        return self.__xor__(other)

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

    @classmethod
    @abstractmethod
    def _from_iterable(cls, iterable):
        # type: (Iterable) -> BaseSet
        """
        Make set from iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Set.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        :rtype: int

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: True if is disjoint.
        :rtype: bool

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: True if is subset.
        :rtype: bool

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: True if is superset.
        :rtype: bool

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def intersection(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get intersection.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Intersection.
        :rtype: objetto.bases.BaseSet

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def symmetric_difference(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Symmetric difference.
        :rtype: objetto.bases.BaseSet

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def union(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get union.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Union.
        :rtype: objetto.bases.BaseSet

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def difference(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get difference.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Difference.
        :rtype: objetto.bases.BaseSet

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def inverse_difference(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Inverse Difference.
        :rtype: objetto.bases.BaseSet

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# noinspection PyCallByClass
type.__setattr__(BaseSet, "__hash__", None)  # force non-hashable


# noinspection PyTypeChecker
_BPS = TypeVar("_BPS", bound="BaseProtectedSet")


class BaseProtectedSet(BaseSet[T], BaseProtectedCollection[T]):
    """
    Base protected set collection.

    Inherits from:
      - :class:`objetto.bases.BaseSet`
      - :class:`objetto.bases.BaseProtectedCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveSet`
      - :class:`objetto.bases.BaseMutableSet`
      - :class:`objetto.bases.BaseSetStructure`
    """

    __slots__ = ()

    @abstractmethod
    def _add(self, value):
        # type: (_BPS, T) -> _BPS
        """
        Add value.

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedSet

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _discard(self, *values):
        # type: (_BPS, T) -> _BPS
        """
        Discard value(s).

        :param values: Value(s).
        :type values: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedSet

        :raises ValueError: No values provided.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _remove(self, *values):
        # type: (_BPS, T) -> _BPS
        """
        Remove existing value(s).

        :param values: Value(s).
        :type values: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedSet

        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _replace(self, old_value, new_value):
        # type: (_BPS, T, T) -> _BPS
        """
        Replace existing value with a new one.

        :param old_value: Existing value.

        :param new_value: New value.

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedSet

        :raises KeyError: Value is not present.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _update(self, iterable):
        # type: (_BPS, Iterable[T]) -> _BPS
        """
        Update with iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable[collections.abc.Hashable]

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedSet

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BIS = TypeVar("_BIS", bound="BaseInteractiveSet")


# noinspection PyAbstractClass
class BaseInteractiveSet(BaseProtectedSet[T], BaseInteractiveCollection[T]):
    """
    Base interactive set collection.

    Inherits from:
      - :class:`objetto.bases.BaseProtectedSet`
      - :class:`objetto.bases.BaseInteractiveCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveSetStructure`
      - :class:`objetto.states.SetState`
    """

    __slots__ = ()

    @final
    def add(self, value):
        # type: (_BIS, T) -> _BIS
        """
        Add value.

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveSet
        """
        return self._add(value)

    @final
    def discard(self, *values):
        # type: (_BIS, T) -> _BIS
        """
        Discard value(s).

        :param values: Value(s).
        :type values: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveSet

        :raises ValueError: No values provided.
        """
        return self._discard(*values)

    @final
    def remove(self, *values):
        # type: (_BIS, T) -> _BIS
        """
        Remove existing value(s).

        :param values: Value(s).
        :type values: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveSet

        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        return self._remove(*values)

    @final
    def replace(self, old_value, new_value):
        # type: (_BIS, T, T) -> _BIS
        """
        Replace existing value with a new one.

        :param old_value: Existing value.

        :param new_value: New value.

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveSet

        :raises KeyError: Old value is not present.
        """
        return self._replace(old_value, new_value)

    @final
    def update(self, iterable):
        # type: (_BIS, Iterable[T]) -> _BIS
        """
        Update with iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveSet
        """
        return self._update(iterable)


class BaseMutableSet(SlottedMutableSet, BaseProtectedSet[T], BaseMutableCollection[T]):
    """
    Base mutable set collection.

    Inherits from:
      - :class:`slotted.SlottedMutableSet`
      - :class:`objetto.bases.BaseProtectedSet`
      - :class:`objetto.bases.BaseMutableCollection`

    Inherited By:
      - :class:`objetto.bases.BaseMutableSetStructure`
      - :class:`objetto.objects.ProxySetObject`
    """

    __slots__ = ()

    @final
    def __iand__(self, iterable):
        """
        Intersect in place: `self &= iterable`.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: This mutable set.
        :rtype: objetto.bases.BaseMutableSet
        """
        self.intersection_update(iterable)
        return self

    @final
    def __isub__(self, iterable):
        """
        Difference in place: `self -= iterable`.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: This mutable set.
        :rtype: objetto.bases.BaseMutableSet
        """
        self.difference(iterable)
        return self

    @final
    def __ior__(self, iterable):
        """
        Update in place: `self |= iterable`.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: This mutable set.
        :rtype: objetto.bases.BaseMutableSet
        """
        self.update(iterable)
        return self

    @final
    def __ixor__(self, iterable):
        """
        Symmetric difference in place: `self ^= iterable`.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: This mutable set.
        :rtype: objetto.bases.BaseMutableSet
        """
        if iterable is self:
            self.clear()
        else:
            self.symmetric_difference_update(iterable)
        return self

    @abstractmethod
    def pop(self):
        # type: () -> T
        """
        Pop value.

        :return: Value.

        :raises KeyError: Empty set.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def intersection_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Intersect.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def symmetric_difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Symmetric difference.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Difference.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()

    @final
    def add(self, value):
        # type: (T) -> None
        """
        Add value.

        :param value: Value.
        """
        self._add(value)

    @final
    def discard(self, *values):
        # type: (T) -> None
        """
        Discard value(s).

        :param values: Value(s).
        :type values: collections.abc.Hashable

        :raises ValueError: No values provided.
        """
        self._discard(*values)

    @final
    def remove(self, *values):
        # type: (T) -> None
        """
        Remove existing value(s).

        :param values: Value(s).
        :type values: collections.abc.Hashable

        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        self._remove(*values)

    @final
    def replace(self, old_value, new_value):
        # type: (T, T) -> None
        """
        Replace existing value with a new one.

        :param old_value: Existing value.

        :param new_value: New value.
        """
        self._replace(old_value, new_value)

    @final
    def update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Update with iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable
        """
        self._update(iterable)
