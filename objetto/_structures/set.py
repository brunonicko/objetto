# -*- coding: utf-8 -*-
"""Set structures."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import with_metaclass

from .._bases import BaseInteractiveSet, BaseMutableSet, BaseProtectedSet, final
from .._states import SetState
from ..utils.custom_repr import custom_iterable_repr
from ..utils.recursive_repr import recursive_repr
from .bases import (
    BaseAuxiliaryStructure,
    BaseAuxiliaryStructureMeta,
    BaseInteractiveAuxiliaryStructure,
    BaseMutableAuxiliaryStructure,
)

if TYPE_CHECKING:
    from typing import Any, Iterable, Iterator


__all__ = [
    "BaseSetStructureMeta",
    "BaseSetStructure",
    "BaseInteractiveSetStructure",
    "BaseMutableSetStructure",
]


T = TypeVar("T")  # Any type.


# noinspection PyAbstractClass
class BaseSetStructureMeta(BaseAuxiliaryStructureMeta):
    """
    Metaclass for :class:`objetto.bases.BaseSetStructure`.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructureMeta`

    Inherited by:
      - :class:`objetto.data.SetDataMeta`
      - :class:`objetto.objects.SetObjectMeta`
    """


class BaseSetStructure(
    with_metaclass(
        BaseSetStructureMeta,
        BaseAuxiliaryStructure[T],
        BaseProtectedSet[T],
    )
):
    """
    Base set structure.

    Metaclass:
      - :class:`objetto.bases.BaseSetStructureMeta`

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructure`
      - :class:`objetto.bases.BaseProtectedSet`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveSetStructure`
      - :class:`objetto.bases.BaseMutableSetStructure`
      - :class:`objetto.data.SetData`
      - :class:`objetto.objects.SetObject`
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
                sorting=True,
                sort_key=lambda v: hash(v),
            )
        else:
            return "<{}>".format(type(self).__fullname__)

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
        :rtype: collections.abc.Iterator[collections.abc.Hashable]
        """
        for value in self._state:
            yield value

    @final
    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :type value: collections.abc.Hashable

        :return: True if contains.
        :rtype: bool
        """
        return value in self._state

    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: True if is disjoint.
        :rtype: bool
        """
        return self._state.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: True if is subset.
        :rtype: bool
        """
        return self._state.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: True if is superset.
        :rtype: bool
        """
        return self._state.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get intersection.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Intersection.
        :rtype: objetto.states.SetState
        """
        return self._state.intersection(iterable)

    def difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get difference.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Difference.
        :rtype: objetto.states.SetState
        """
        return self._state.difference(iterable)

    def inverse_difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Inverse Difference.
        :rtype: objetto.states.SetState
        """
        return self._state.inverse_difference(iterable)

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Symmetric difference.
        :rtype: objetto.states.SetState
        """
        return self._state.symmetric_difference(iterable)

    def union(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get union.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Union.
        :rtype: objetto.states.SetState
        """
        return self._state.union(iterable)

    @property
    @abstractmethod
    def _state(self):
        # type: () -> SetState[T]
        """
        Internal state.

        :rtype: objetto.states.SetState

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseInteractiveSetStructure(
    BaseSetStructure[T],
    BaseInteractiveAuxiliaryStructure[T],
    BaseInteractiveSet[T],
):
    """
    Base interactive set structure.

    Inherits from:
      - :class:`objetto.bases.BaseSetStructure`
      - :class:`objetto.bases.BaseInteractiveAuxiliaryStructure`
      - :class:`objetto.bases.BaseInteractiveSet`

    Inherited By:
      - :class:`objetto.data.InteractiveSetData`
    """

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableSetStructure(
    BaseMutableSet[T],
    BaseSetStructure[T],
    BaseMutableAuxiliaryStructure[T],
):
    """
    Base mutable set structure.

    Inherits from:
      - :class:`objetto.bases.BaseMutableSet`
      - :class:`objetto.bases.BaseSetStructure`
      - :class:`objetto.bases.BaseMutableAuxiliaryStructure`

    Inherited By:
      - :class:`objetto.objects.MutableSetObject`
    """

    __slots__ = ()
