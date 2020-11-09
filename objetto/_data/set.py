# -*- coding: utf-8 -*-
"""Set data."""

from typing import TYPE_CHECKING, Generic, TypeVar, cast

from six import with_metaclass

from .._bases import final
from .bases import (
    BaseAuxiliaryDataMeta, BaseAuxiliaryData, BaseInteractiveAuxiliaryData
)
from .._containers.set import SetContainerMeta, SemiInteractiveSetContainer
from ..utils.custom_repr import custom_iterable_repr
from ..utils.immutable import ImmutableSet

if TYPE_CHECKING:
    from typing import Any, Type, Iterator, Iterable, List

__all__ = ["SetDataMeta", "SetData", "InteractiveSetData"]

_T = TypeVar("_T")


class SetDataMeta(BaseAuxiliaryDataMeta, SetContainerMeta):
    """Metaclass for :class:`SetData`."""

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[SetData]
        """Base auxiliary container type."""
        return SetData


class SetData(
    with_metaclass(
        SetDataMeta,
        BaseAuxiliaryData,
        SemiInteractiveSetContainer,
        Generic[_T],
    )
):
    """
    Set data.

    :param initial: Initial values.
    """
    __slots__ = ()

    @classmethod
    @final
    def __make__(cls, state=ImmutableSet()):
        # type: (ImmutableSet) -> SetData
        """
        Make a new set data.

        :param state: Internal state.
        :return: New set data.
        """
        return cast("SetData", super(SetData, cls).__make__(state))

    @final
    def __init__(self, initial=()):
        # type: (Iterable) -> None
        if type(initial) is type(self):
            self._init_state(getattr(initial, "_state"))
        else:
            self._init_state(self.__get_initial_state(initial))

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
                sorting=True,
                sort_key=lambda v: hash(v)
            )
        else:
            return "<{}>".format(type(self).__fullname__)

    @final
    def __contains__(self, value):
        # type: (object) -> bool
        """
        Get whether contains value.

        :param value: Value.
        :return: True if contains.
        """
        return value in self.__internal

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
        # type: () -> Iterator[_T]
        """
        Iterate over values.

        :return: Value iterator.
        """
        for value in self.__internal:
            yield value

    @classmethod
    @final
    def __get_initial_state(
        cls,
        input_values,  # type: Iterable
        factory=True,  # type: bool
    ):
        # type: (...) -> ImmutableSet
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        if not cls._relationship.passthrough:
            state = ImmutableSet(
                cls._relationship.fabricate_value(v, factory=factory)
                for v in input_values
            )
        else:
            state = ImmutableSet(input_values)
        return state

    @final
    def _clear(self):
        # type: () -> SetData
        """
        Clear all values.

        :return: New version.
        """
        return type(self).__make__()

    @final
    def _set(self, value, new_value):
        # type: (_T, _T) -> SetData
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :param new_value: New value.
        :return: New version.
        """
        return self._replace(value, new_value)

    @final
    def _add(self, *values):
        # type: (_T) -> SetData
        """
        Add value(s).

        :param values: Value(s).
        :return: New version.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            values = (cls._relationship.fabricate_value(v) for v in values)
        return cls.__make__(self._state.add(*values))

    @final
    def _discard(self, value):
        # type: (_T) -> SetData
        """
        Discard value if it exists.

        :param value: Value.
        :return: New version.
        """
        cls = type(self)
        return cls.__make__(self._state.discard(value))

    @final
    def _remove(self, value):
        # type: (_T) -> SetData
        """
        Remove existing value.

        :param value: Value.
        :return: New version.
        """
        cls = type(self)
        return cls.__make__(self._state.remove(value))

    @final
    def _replace(self, value, new_value):
        # type: (_T, _T) -> SetData
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :param new_value: New value.
        :return: New version.
        """
        cls = type(self)
        new_value = cls._relationship.fabricate_value(new_value)
        return cls.__make__(self._state.replace(value, new_value))

    @final
    def _update(self, iterable):
        # type: (Iterable[_T]) -> SetData
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: New version.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            iterable = (cls._relationship.fabricate_value(v) for v in iterable)
        return cls.__make__(self._state.update(iterable))

    @final
    def get(self, value, fallback=None):
        # type: (_T, Any) -> _T
        """
        Get value if it's in the set, return fallback value otherwise.

        :param value: Value.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        if value in self._state:
            return value
        else:
            return fallback

    @final
    def difference(self, iterable):
        # type: (Iterable) -> ImmutableSet
        """
        Get difference.

        :param iterable: Iterable.
        :return: New version.
        """
        return self._state.difference(iterable)

    @final
    def intersection(self, iterable):
        # type: (Iterable) -> ImmutableSet
        """
        Get intersection.

        :param iterable: Iterable.
        :return: New version.
        """
        return self._state.intersection(iterable)

    @final
    def symmetric_difference(self, iterable):
        # type: (Iterable) -> ImmutableSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: New version.
        """
        return self._state.symmetric_difference(iterable)

    @final
    def union(self, iterable):
        # type: (Iterable) -> ImmutableSet
        """
        Get union.

        :param iterable: Iterable.
        :return: New version.
        """
        return self._state.union(iterable)

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (List, Any) -> SetData
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise RuntimeError(error)
        state = ImmutableSet(
            cls.deserialize_value(v, location=None, **kwargs) for v in serialized
        )
        return cls.__make__(state)

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> List
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized.
        """
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise RuntimeError(error)
        return sorted(
            (self.serialize_value(v, location=None, **kwargs) for v in self._state),
            key=lambda v: hash(v),
        )

    @final
    def copy(self):
        # type: () -> SetData
        """
        Get copy.

        :return: Copy.
        """
        return self

    @final
    def issubset(self, iterable):
        # type: (Iterable[_T]) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._state.issubset(iterable)

    @final
    def issuperset(self, iterable):
        # type: (Iterable[_T]) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._state.issuperset(iterable)

    @property
    @final
    def _state(self):
        # type: () -> ImmutableSet[_T]
        """Internal state."""
        return cast("ImmutableSet", super(SetData, self)._state)


class InteractiveSetData(SetData, BaseInteractiveAuxiliaryData):
    """Interactive set data."""

    @final
    def clear(self):
        # type: () -> SetData
        """
        Clear all values.

        :return: New version.
        """
        return self._clear()

    @final
    def set(self, value, new_value):
        # type: (_T, _T) -> SetData
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :param new_value: New value.
        :return: New version.
        """
        return self._set(value, new_value)

    @final
    def add(self, *values):
        # type: (_T) -> SetData
        """
        Add value(s).

        :param values: Value(s).
        :return: New version.
        """
        return self._add(*values)

    @final
    def discard(self, value):
        # type: (_T) -> SetData
        """
        Discard value if it exists.

        :param value: Value.
        :return: New version.
        """
        return self._discard(value)

    @final
    def remove(self, value):
        # type: (_T) -> SetData
        """
        Remove existing value.

        :param value: Value.
        :return: New version.
        """
        return self._remove(value)

    @final
    def replace(self, value, new_value):
        # type: (_T, _T) -> SetData
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :param new_value: New value.
        :return: New version.
        """
        return self._replace(value, new_value)

    @final
    def update(self, iterable):
        # type: (Iterable[_T]) -> SetData
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: New version.
        """
        return self._update(iterable)
