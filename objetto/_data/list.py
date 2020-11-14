# -*- coding: utf-8 -*-
"""List data."""

from typing import TYPE_CHECKING, Generic, TypeVar, cast, overload

from six import with_metaclass

from .._bases import final
from .._containers.list import ListContainerMeta, SemiInteractiveListContainer
from ..utils.custom_repr import custom_iterable_repr
from ..utils.immutable import ImmutableList
from ..utils.list_operations import resolve_continuous_slice, resolve_index
from .bases import (
    BaseAuxiliaryData,
    BaseAuxiliaryDataMeta,
    BaseInteractiveAuxiliaryData,
)

if TYPE_CHECKING:
    from typing import Any, Iterable, List, Tuple, Type, Union

__all__ = ["ListDataMeta", "ListData", "InteractiveListData"]

_T = TypeVar("_T")


class ListDataMeta(BaseAuxiliaryDataMeta, ListContainerMeta):
    """Metaclass for :class:`ListData`."""

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[ListData]
        """Base auxiliary container type."""
        return ListData


class ListData(
    with_metaclass(
        ListDataMeta,
        BaseAuxiliaryData,
        SemiInteractiveListContainer,
        Generic[_T],
    )
):
    """
    List data.

    :param initial: Initial values.
    """

    __slots__ = ()

    @classmethod
    @final
    def __make__(cls, state=ImmutableList()):
        # type: (ImmutableList) -> ListData
        """
        Make a new list data.

        :param state: Internal state.
        :return: New list data.
        """
        return cast("ListData", super(ListData, cls).__make__(state))

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
            )
        else:
            return "<{}>".format(type(self).__fullname__)

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

    @final
    def __getitem__(self, index):
        # type: (Union[int, slice]) -> Union[_T, ImmutableList[_T]]
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        if isinstance(index, slice):
            return ImmutableList(self._state[index])
        else:
            return self._state[index]

    @final
    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self._state)

    @classmethod
    @final
    def __get_initial_state(
        cls,
        input_values,  # type: Iterable
        factory=True,  # type: bool
    ):
        # type: (...) -> ImmutableList
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        if not cls._relationship.passthrough:
            state = ImmutableList(
                cls._relationship.fabricate_value(v, factory=factory)
                for v in input_values
            )
        else:
            state = ImmutableList(input_values)
        return state

    @final
    def _clear(self):
        # type: () -> ListData
        """
        Clear all values.

        :return: New version.
        """
        return type(self).__make__()

    @final
    def _set(self, index, value):
        # type: (int, _T) -> ListData
        """
        Set value at index.

        :param index: Index.
        :param value: Value.
        :return: New version.
        """
        return self._change(index, value)

    @final
    def _change(self, index, *values):
        # type: (int, _T) -> ListData
        """
        Change value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: New version.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            values = (cls._relationship.fabricate_value(v) for v in values)
        return cls.__make__(self._state.change(index, *values))

    @final
    def _append(self, value):
        # type: (_T) -> ListData
        """
        Append value at the end.

        :param value: Value.
        :return: New version.
        """
        cls = type(self)
        value = cls._relationship.fabricate_value(value)
        return cls.__make__(self._state.append(value))

    @final
    def _extend(self, iterable):
        # type: (Iterable[_T]) -> ListData
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: New version.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            iterable = (cls._relationship.fabricate_value(v) for v in iterable)
        return cls.__make__(self._state.extend(iterable))

    @final
    def _insert(self, index, *values):
        # type: (int, _T) -> ListData
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: New version.
        :raises ValueError: No values provided.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            values = (cls._relationship.fabricate_value(v) for v in values)
        return cls.__make__(self._state.insert(index, *values))

    @final
    def _remove(self, value):
        # type: (_T) -> ListData
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: New version.
        """
        return type(self).__make__(self._state.remove(value))

    @final
    def _reverse(self):
        # type: () -> ListData
        """
        Reverse values.

        :return: New version.
        """
        return type(self).__make__(self._state.reverse())

    @final
    def _move(self, item, target_index):
        # type: (Union[slice, int], int) -> Any
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: New version.
        """
        return type(self).__make__(self._state.move(item, target_index))

    @final
    def _sort(self, key=None, reverse=False):
        # type: (...) -> ListData
        """
        Sort values.

        :param key: Sorting key function.
        :param reverse: Whether to reverse sort.
        :return: New version.
        """
        return type(self).__make__(self._state.sort(key=key, reverse=reverse))

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (List, Any) -> ListData
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise RuntimeError(error)
        state = ImmutableList(
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
        return list(
            self.serialize_value(v, location=None, **kwargs) for v in self._state
        )

    @final
    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return resolve_index(len(self._state), index, clamp=clamp)

    @final
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return resolve_continuous_slice(len(self._state), slc)

    @property
    @final
    def _state(self):
        # type: () -> ImmutableList[_T]
        """Internal state."""
        return cast("ImmutableList", super(ListData, self)._state)


class InteractiveListData(ListData, BaseInteractiveAuxiliaryData):
    """Interactive list data."""

    @final
    def clear(self):
        # type: () -> InteractiveListData
        """
        Clear all values.

        :return: New version.
        """
        return self._clear()

    @final
    def set(self, index, value):
        # type: (int, _T) -> InteractiveListData
        """
        Set value at index.

        :param index: Index.
        :param value: Value.
        :return: New version.
        """
        return self._set(index, value)

    @final
    def change(self, index, *values):
        # type: (int, _T) -> InteractiveListData
        """
        Change value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: New version.
        """
        return self._change(index, *values)

    @final
    def append(self, value):
        # type: (_T) -> InteractiveListData
        """
        Append value at the end.

        :param value: Value.
        :return: New version.
        """
        return self._append(value)

    @final
    def extend(self, iterable):
        # type: (Iterable[_T]) -> InteractiveListData
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: New version.
        """
        return self._extend(iterable)

    @final
    def insert(self, index, *values):
        # type: (int, _T) -> InteractiveListData
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: New version.
        :raises ValueError: No values provided.
        """
        return self._insert(index, *values)

    @final
    def remove(self, value):
        # type: (_T) -> InteractiveListData
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: New version.
        """
        return self._remove(value)

    @final
    def reverse(self):
        # type: () -> InteractiveListData
        """
        Reverse values.

        :return: New version.
        """
        return self._reverse()

    @final
    def move(self, item, target_index):
        # type: (Union[slice, int], int) -> InteractiveListData
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: New version.
        """
        return self._move(item, target_index)

    @final
    def sort(self, key=None, reverse=False):
        # type: (...) -> InteractiveListData
        """
        Sort values.

        :param key: Sorting key function.
        :param reverse: Whether to reverse sort.
        :return: New version.
        """
        return self._sort(key=key, reverse=reverse)
