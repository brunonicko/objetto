# -*- coding: utf-8 -*-
"""List data structures."""

from typing import TYPE_CHECKING, TypeVar, cast, overload

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
    SerializationError,
)
from .bases import (
    BaseAuxiliaryData,
    BaseAuxiliaryDataMeta,
    BaseInteractiveAuxiliaryData,
)

if TYPE_CHECKING:
    from typing import Any, Iterable, List, Sequence, Type, Union


__all__ = ["ListDataMeta", "ListData", "InteractiveListData"]


T = TypeVar("T")  # Any type.


class ListDataMeta(BaseAuxiliaryDataMeta, BaseListStructureMeta):
    """
    Metaclass for :class:`objetto.data.ListData`.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryDataMeta`
      - :class:`objetto.bases.BaseListStructureMeta`

    Features:
      - Defines a base auxiliary type.
    """

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[ListData]
        """
        Base auxiliary container type.

        :rtype: type[objetto.data.ListData]
        """
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

    Metaclass:
      - :class:`objetto.data.ListDataMeta`

    Inherits from:
      - :class:`objetto.bases.BaseListStructure`
      - :class:`objetto.bases.BaseAuxiliaryData`

    Inherited by:
      - :class:`objetto.data.InteractiveListData`

    :param initial: Initial values.
    :type initial: collections.abc.Iterable
    """

    __slots__ = ()

    @classmethod
    @final
    def __make__(cls, state=ListState()):
        # type: (Type[_LD], BaseState) -> _LD
        """
        Make a new list data.

        :param state: Internal state.
        :return: New list data.
        """
        return super(ListData, cls).__make__(state)

    @final
    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        self._init_state(self.__get_initial_state(initial))

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> Sequence[T]
        pass

    @final
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :type index: int or slice

        :return: Value/values.
        :rtype: Any or objetto.states.ListState
        """
        return self._state[index]

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
        :rtype: objetto.data.ListData
        """
        return type(self).__make__()

    @final
    def _insert(self, index, *values):
        # type: (_LD, int, T) -> _LD
        """
        Insert value(s) at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).
        :type values: collections.abc.Iterable

        :return: Transformed.
        :rtype: objetto.data.ListData

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
        :rtype: objetto.data.ListData
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
        :type iterable: collections.abc.Iterable

        :return: Transformed.
        :rtype: objetto.data.ListData
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
        :rtype: objetto.data.ListData

        :raises ValueError: Value is not present.
        """
        return type(self).__make__(self._state.remove(value))

    @final
    def _reverse(self):
        # type: (_LD) -> _LD
        """
        Reverse values.

        :return: Transformed.
        :rtype: objetto.data.ListData
        """
        return type(self).__make__(self._state.reverse())

    @final
    def _move(self, item, target_index):
        # type: (_LD, Union[slice, int], int) -> _LD
        """
        Move values internally.

        :param item: Index/slice.
        :type item: int or slice

        :param target_index: Target index.
        :type target_index: int

        :return: Transformed.
        :rtype: objetto.data.ListData
        """
        return type(self).__make__(self._state.move(item, target_index))

    @final
    def _delete(self, item):
        # type: (_LD, Union[slice, int]) -> _LD
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :type item: int or slice

        :return: Transformed.
        :rtype: objetto.data.ListData
        """
        return type(self).__make__(self._state.delete(item))

    @final
    def _update(self, index, *values):
        # type: (_LD, int, T) -> _LD
        """
        Update value(s) starting at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :rtype: objetto.data.ListData

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
        :type: serialized: list

        :param kwargs: Keyword arguments to be passed to the deserializers.

        :return: Deserialized.
        :rtype: objetto.data.ListData

        :raises objetto.exceptions.SerializationError: Can't deserialize.
        """
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise SerializationError(error)
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
        :rtype: list

        :raises objetto.exceptions.SerializationError: Can't serialize.
        """
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise SerializationError(error)
        return list(
            self.serialize_value(v, location=None, **kwargs) for v in self._state
        )

    @property
    @final
    def _state(self):
        # type: () -> ListState[T]
        """
        Internal state.

        :rtype: objetto.states.ListState
        """
        return cast("ListState", super(BaseListStructure, self)._state)


class InteractiveListData(
    ListData[T],
    BaseInteractiveListStructure[T],
    BaseInteractiveAuxiliaryData[T],
):
    """
    Interactive list data.

    Inherits from:
      - :class:`objetto.data.ListData`
      - :class:`objetto.bases.BaseInteractiveListStructure`
      - :class:`objetto.bases.BaseInteractiveAuxiliaryData`
    """

    __slots__ = ()
