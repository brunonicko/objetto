# -*- coding: utf-8 -*-
"""List data structures."""

from typing import TYPE_CHECKING, TypeVar, cast

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import with_metaclass

from .._bases import final
from .._states import BaseState, ListState
from .._structures import (
    BaseInteractiveListStructure,
    BaseListStructure,
    BaseListStructureMeta,
)
from .bases import (
    BaseAuxiliaryData,
    BaseAuxiliaryDataMeta,
    BaseInteractiveAuxiliaryData,
)

if TYPE_CHECKING:
    from typing import Any, Iterable, List, Type, Union


__all__ = ["ListData", "InteractiveListData"]


T = TypeVar("T")  # Any type.


class ListDataMeta(BaseAuxiliaryDataMeta, BaseListStructureMeta):
    """Metaclass for :class:`ListData`."""

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[ListData]
        """Base auxiliary container type."""
        return ListData


# noinspection PyTypeChecker
_LD = TypeVar("_LD", bound="ListData")


class ListData(
    with_metaclass(
        ListDataMeta,
        BaseListStructure[T],
        BaseAuxiliaryData[T],
    )
):
    """
    List data.

    :param initial: Initial values.
    """

    __slots__ = ()

    @classmethod
    @final
    def __make__(cls, state=ListState()):
        # type: (Type[_LD], BaseState) -> _LD
        """
        Make a new list data.

        :param state: Internal state.
        :return: New dictionary data.
        """
        return super(ListData, cls).__make__(state)

    @final
    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        if type(initial) is type(self):
            self._init_state(getattr(initial, "_state"))
        else:
            self._init_state(self.__get_initial_state(initial))

    @classmethod
    @final
    def __get_initial_state(cls, input_values, factory=True):
        # type: (Iterable[T], bool) -> ListState[T]
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        if not cls._relationship.passthrough:
            state = ListState(
                cls._relationship.fabricate_value(v, factory=factory)
                for v in input_values
            )
        else:
            state = ListState(input_values)
        return state

    @final
    def _clear(self):
        # type: (_LD) -> _LD
        """
        Clear all values.

        :return: Transformed.
        """
        return type(self).__make__()

    @final
    def _insert(self, index, *values):
        # type: (_LD, int, T) -> _LD
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            fabricated_values = (cls._relationship.fabricate_value(v) for v in values)
            return type(self).__make__(self._state.insert(index, *fabricated_values))
        else:
            return type(self).__make__(self._state.insert(index, *values))

    @final
    def _append(self, value):
        # type: (_LD, T) -> _LD
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        cls = type(self)
        fabricated_value = cls._relationship.fabricate_value(value)
        return type(self).__make__(self._state.append(fabricated_value))

    @final
    def _extend(self, iterable):
        # type: (_LD, Iterable[T]) -> _LD
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            fabricated_iterable = (
                cls._relationship.fabricate_value(v) for v in iterable
            )
            return type(self).__make__(self._state.extend(fabricated_iterable))
        else:
            return type(self).__make__(self._state.extend(iterable))

    @final
    def _remove(self, value):
        # type: (_LD, T) -> _LD
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return type(self).__make__(self._state.remove(value))

    @final
    def _reverse(self):
        # type: (_LD) -> _LD
        """
        Reverse values.

        :return: Transformed.
        """
        return type(self).__make__(self._state.reverse())

    @final
    def _move(self, item, target_index):
        # type: (_LD, Union[slice, int], int) -> _LD
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        return type(self).__make__(self._state.move(item, target_index))

    @final
    def _delete(self, item):
        # type: (_LD, Union[slice, int]) -> _LD
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        return type(self).__make__(self._state.delete(item))

    @final
    def _update(self, index, *values):
        # type: (_LD, int, T) -> _LD
        """
        Update value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            fabricated_values = (cls._relationship.fabricate_value(v) for v in values)
            return type(self).__make__(self._state.update(index, *fabricated_values))
        else:
            return type(self).__make__(self._state.update(index, *values))

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Type[_LD], List, Any) -> _LD
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        :raises RuntimeError: Not deserializable.
        """
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise RuntimeError(error)
        state = ListState(
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
        :raises RuntimeError: Not serializable.
        """
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise RuntimeError(error)
        return list(
            self.serialize_value(v, location=None, **kwargs) for v in self._state
        )

    @property
    @final
    def _state(self):
        # type: () -> ListState[T]
        """Internal state."""
        return cast("ListState", super(BaseListStructure, self)._state)


class InteractiveListData(
    ListData[T],
    BaseInteractiveListStructure[T],
    BaseInteractiveAuxiliaryData[T],
):
    """Interactive list data."""

    __slots__ = ()