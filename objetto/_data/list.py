# -*- coding: utf-8 -*-
"""List data."""
from typing import Generic, TYPE_CHECKING, TypeVar, cast, overload

from six import with_metaclass

from .base import BaseAuxiliaryData, BaseAuxiliaryDataMeta
from .._bases import final, init_context
from .._containers.list import ListContainer, ListContainerMeta
from ..utils.custom_repr import custom_iterable_repr
from ..utils.immutable import ImmutableList

if TYPE_CHECKING:
    from typing import Any, Type, Union, Iterable, List

__all__ = ["ListDataMeta", "ListData", "InteractiveListData"]

_T = TypeVar("_T")


class ListDataMeta(BaseAuxiliaryDataMeta, ListContainerMeta):
    """Metaclass for :class:`ListData`."""

    @property
    @final
    def _auxiliary_data_type(cls):
        # type: () -> Type[ListData]
        """Base auxiliary data type."""
        return ListData


class ListData(
    with_metaclass(ListDataMeta, BaseAuxiliaryData, ListContainer, Generic[_T])
):
    """List data."""

    __slots__ = ("__state",)

    @classmethod
    @final
    def __make__(cls, state=ImmutableList()):
        # type: (Any) -> ListData
        self = cast("ListData", cls.__new__(cls))
        with init_context(self):
            self.__state = state
        return self

    @final
    def __init__(self, initial=()):
        # type: (Iterable) -> None
        if type(initial) is type(self):
            self.__state = cast("ListData", initial).__state
        else:
            self.__state = self.__get_initial_state(initial)

    def __repr__(self):
        # type: () -> str
        """Get representation."""
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
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> ImmutableList
        pass

    def __getitem__(self, index):
        # type: (Union[int, slice]) -> Union[_T, ImmutableList]
        if isinstance(index, slice):
            return type(self).__make__(self._state[index])
        else:
            return self._state[index]

    def __len__(self):
        # type: () -> int
        return len(self._state)

    @classmethod
    @final
    def __get_initial_state(
        cls,
        input_values,  # type: Iterable
        factory=True,  # type: bool
    ):
        # type: (...) -> ImmutableList
        """Get initial state."""
        state = ImmutableList(
            cls._relationship.fabricate_value(v, factory=factory)
            for v in input_values
        )
        return state

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (List, Any) -> ListData
        """Deserialize."""
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise RuntimeError(error)

        input_values = (cls.deserialize_value(v, None, **kwargs) for v in serialized)
        state = cls.__get_initial_state(input_values, factory=False)
        return cls.__make__(state)

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> List
        """Serialize."""
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise RuntimeError(error)

        return list(self.serialize_value(v, None, **kwargs) for v in self._state)

    def _copy(self):
        # type: () -> ListData
        return self

    def _clear(self):
        # type: () -> ListData
        return type(self).__make__()

    def _append(self, value):
        # type: (_T) -> ListData
        cls = type(self)
        value = cls._relationship.fabricate_value(value)
        return cls.__make__(self._state.append(value))

    def _extend(self, iterable):
        # type: (Iterable[_T]) -> ListData
        cls = type(self)
        iterable = (v for v in cls._relationship.fabricate_value(iterable))
        return cls.__make__(self._state.extend(iterable))

    def _insert(self, index, value):
        # type: (int, _T) -> ListData
        cls = type(self)
        value = cls._relationship.fabricate_value(value)
        return cls.__make__(self._state.insert(index, value))

    def _remove(self, value):
        # type: (_T) -> ListData
        return type(self).__make__(self._state.remove(value))

    def _reverse(self):
        # type: () -> ListData
        return type(self).__make__(self._state.reverse())

    def _sort(self, key=None, reverse=False):
        # type: (...) -> ListData
        return type(self).__make__(self._state.sort(key=key, reverse=reverse))

    @property
    @final
    def _state(self):
        # type: () -> ImmutableList[_T]
        """Internal state."""
        return self.__state


class InteractiveListData(ListData):
    """Interactive list data."""

    def copy(self):
        # type: () -> InteractiveListData
        return self._copy()

    def clear(self):
        # type: () -> InteractiveListData
        return self._clear()

    def append(self, value):
        # type: (_T) -> InteractiveListData
        return self._append(value)

    def extend(self, iterable):
        # type: (Iterable[_T]) -> InteractiveListData
        return self._extend(iterable)

    def insert(self, index, value):
        # type: (int, _T) -> InteractiveListData
        return self._insert(index, value)

    def remove(self, value):
        # type: (_T) -> InteractiveListData
        return self._remove(value)

    def reverse(self):
        # type: () -> InteractiveListData
        return self._reverse()

    def sort(self, key=None, reverse=False):
        # type: (...) -> InteractiveListData
        return self._sort(key=key, reverse=reverse)
