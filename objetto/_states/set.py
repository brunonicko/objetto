# -*- coding: utf-8 -*-
"""Immutable set state."""

from typing import TYPE_CHECKING, TypeVar, cast

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from pyrsistent import pset
from six import iteritems

from .._bases import BaseInteractiveSet, final
from ..utils.custom_repr import custom_iterable_repr, custom_mapping_repr
from ..utils.recursive_repr import recursive_repr
from .bases import BaseState

if TYPE_CHECKING:
    from typing import Any, Iterable, Iterator, Type

    from pyrsistent.typing import PSet

__all__ = ["SetState"]


T = TypeVar("T")  # Any type.


# noinspection PyTypeChecker
_SS = TypeVar("_SS", bound="SetState")


@final
class SetState(BaseState[T], BaseInteractiveSet[T]):
    """
    Immutable set state.

    Inherits from:
      - :class:`objetto.bases.BaseState`
      - :class:`objetto.bases.BaseInteractiveSet`

    :param initial: Initial values.
    :type initial: collections.abc.Iterable
    """

    __slots__ = ()

    @classmethod
    def _make(cls, internal=pset()):
        # type: (Type[_SS], PSet[T]) -> _SS
        """
        Make new state by directly setting the internal state.

        :param internal: Internal state.
        :return: State.
        """
        return super(SetState, cls)._make(internal)

    @staticmethod
    def _make_internal(initial):
        # type: (Iterable[T]) -> PSet[T]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pset(initial)

    @classmethod
    def _from_iterable(cls, iterable):
        # type: (Iterable) -> SetState
        """
        Make set state from iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Set state.
        :rtype: objetto.states.SetState
        """
        if isinstance(iterable, type(pset())):
            return SetState._make(iterable)
        else:
            return SetState(iterable)

    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        super(SetState, self).__init__(initial=initial)

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        :rtype: int
        """
        return super(SetState, self).__hash__()

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
        if isinstance(other, SetState):
            return self._internal == other._internal
        return False

    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :type value: collections.abc.Hashable

        :return: True if contains.
        :rtype: bool
        """
        return value in self._internal

    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over values.

        :return: Values iterator.
        :rtype: collections.abc.Iterator[collections.abc.Hashable]
        """
        for key in self._internal:
            yield key

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
            prefix="{}([".format(type(self).__name__),
            suffix="])",
            sorting=True,
            sort_key=lambda v: hash(v),
        )

    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        :rtype: int
        """
        return hash(self)

    def _clear(self):
        # type: (_SS) -> _SS
        """
        Clear.

        :return: Transformed.
        :rtype: objetto.states.SetState
        """
        return self._make()

    def _add(self, value):
        # type: (_SS, T) -> _SS
        """
        Add value.

        :param value: Value.
        :type value: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.states.SetState
        """
        return self._make(self._internal.add(value))

    def _discard(self, *values):
        # type: (_SS, T) -> _SS
        """
        Discard value(s).

        :param values: Value(s).
        :type values: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.states.SetState

        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        return self._make(self._internal.discard(*values))

    def _remove(self, *values):
        # type: (_SS, T) -> _SS
        """
        Remove existing value(s).

        :param values: Value(s).
        :type values: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.states.SetState

        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        return self._make(self._internal.difference(values))

    def _replace(self, old_value, new_value):
        # type: (_SS, T, T) -> _SS
        """
        Replace existing value with a new one.

        :param old_value: Existing value.
        :type old_value: collections.abc.Hashable

        :param new_value: New value.
        :type new_value: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.states.SetState

        :raises KeyError: Value is not present.
        """
        return self._make(self._internal.remove(old_value).add(new_value))

    def _update(self, iterable):
        # type: (_SS, Iterable[T]) -> _SS
        """
        Update with iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable[collections.abc.Hashable]

        :return: Transformed.
        :rtype: objetto.states.SetState
        """
        return self._make(self._internal.update(iterable))

    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: True if is disjoint.
        :rtype: bool
        """
        return self._internal.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: True if is subset.
        :rtype: bool
        """
        return self._internal.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: True if is superset.
        :rtype: bool
        """
        return self._internal.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get intersection.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Intersection.
        :rtype: objetto.states.SetState
        """
        return SetState._make(self._internal.intersection(iterable))

    def difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get difference.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Difference.
        :rtype: objetto.states.SetState
        """
        return SetState._make(self._internal.difference(iterable))

    def inverse_difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Inverse Difference.
        :rtype: objetto.states.SetState
        """
        return SetState._make(pset(iterable).difference(self._internal))

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Symmetric difference.
        :rtype: objetto.states.SetState
        """
        return SetState._make(self._internal.symmetric_difference(iterable))

    def union(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get union.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Union.
        :rtype: objetto.states.SetState
        """
        return SetState._make(self._internal.union(iterable))

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
        # type: () -> PSet[T]
        """Internal values."""
        return cast("PSet[T]", super(SetState, self)._internal)
