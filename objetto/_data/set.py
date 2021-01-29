# -*- coding: utf-8 -*-
"""Set data structures."""

from typing import TYPE_CHECKING, TypeVar, cast

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import with_metaclass

from .._bases import final
from .._states import BaseState, SetState
from .._structures import (
    BaseInteractiveSetStructure,
    BaseSetStructure,
    BaseSetStructureMeta,
    SerializationError,
)
from .bases import (
    BaseAuxiliaryData,
    BaseAuxiliaryDataMeta,
    BaseInteractiveAuxiliaryData,
)

if TYPE_CHECKING:
    from typing import Any, Iterable, List, Type


__all__ = ["SetDataMeta", "SetData", "InteractiveSetData"]


T = TypeVar("T")  # Any type.


class SetDataMeta(BaseAuxiliaryDataMeta, BaseSetStructureMeta):
    """
    Metaclass for :class:`objetto.data.SetData`.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryDataMeta`
      - :class:`objetto.bases.BaseSetStructureMeta`

    Features:
      - Defines a base auxiliary type.
    """

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[SetData]
        """
        Base auxiliary container type.

        :rtype: type[objetto.data.SetData]
        """
        return SetData


# noinspection PyTypeChecker
_SD = TypeVar("_SD", bound="SetData")


class SetData(
    with_metaclass(
        SetDataMeta,
        BaseSetStructure[T],
        BaseAuxiliaryData[T],
    )
):
    """
    Set data.

    Metaclass:
      - :class:`objetto.data.SetDataMeta`

    Inherits from:
      - :class:`objetto.bases.BaseSetStructure`
      - :class:`objetto.bases.BaseAuxiliaryData`

    Inherited by:
      - :class:`objetto.data.InteractiveSetData`

    :param initial: Initial values.
    :type initial: collections.abc.Iterable
    """

    __slots__ = ()

    @classmethod
    @final
    def __make__(cls, state=SetState()):
        # type: (Type[_SD], BaseState) -> _SD
        """
        Make a new set data.

        :param state: Internal state.
        :return: New set data.
        """
        return super(SetData, cls).__make__(state)

    @classmethod
    @final
    def _from_iterable(cls, iterable):
        # type: (Iterable) -> SetState
        """
        Make set state from iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Set state.
        :rtype: objetto.states.SetState
        """
        return SetState(iterable)

    @final
    def __init__(self, initial=()):
        # type: (Iterable[T]) -> None
        self._init_state(self.__get_initial_state(initial))

    @classmethod
    @final
    def __get_initial_state(cls, input_values, factory=True):
        # type: (Iterable[T], bool) -> SetState[T]
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        if not cls._relationship.passthrough:
            state = SetState(
                cls._relationship.fabricate_value(v, factory=factory)
                for v in input_values
            )
        else:
            state = SetState(input_values)
        return state

    @final
    def _clear(self):
        # type: (_SD) -> _SD
        """
        Clear all values.

        :return: Transformed.
        :rtype: objetto.data.SetData
        """
        return type(self).__make__()

    @final
    def _add(self, value):
        # type: (_SD, T) -> _SD
        """
        Add value.

        :param value: Value.
        :type value: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.data.SetData
        """
        cls = type(self)
        fabricated_value = cls._relationship.fabricate_value(value)
        return type(self).__make__(self._state.add(fabricated_value))

    @final
    def _discard(self, *values):
        # type: (_SD, T) -> _SD
        """
        Discard value(s).

        :param values: Value(s).
        :type values: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.data.SetData

        :raises ValueError: No values provided.
        """
        return type(self).__make__(self._state.discard(*values))

    @final
    def _remove(self, *values):
        # type: (_SD, T) -> _SD
        """
        Remove existing value(s).

        :param values: Value(s).
        :type value: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.data.SetData

        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        return type(self).__make__(self._state.remove(*values))

    @final
    def _replace(self, value, new_value):
        # type: (_SD, T, T) -> _SD
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :type value: collections.abc.Hashable

        :param new_value: New value.
        :type value: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.data.SetData

        :raises KeyError: Value is not present.
        """
        cls = type(self)
        fabricated_new_value = cls._relationship.fabricate_value(new_value)
        return type(self).__make__(self._state.remove(value).add(fabricated_new_value))

    @final
    def _update(self, iterable):
        # type: (_SD, Iterable[T]) -> _SD
        """
        Update with iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable[collections.abc.Hashable]

        :return: Transformed.
        :rtype: objetto.data.SetData
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            fabricated_iterable = (
                cls._relationship.fabricate_value(v) for v in iterable
            )
            return type(self).__make__(self._state.update(fabricated_iterable))
        else:
            return type(self).__make__(self._state.update(iterable))

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Type[_SD], List, Any) -> _SD
        """
        Deserialize.

        :param serialized: Serialized.
        :type serialized: list

        :param kwargs: Keyword arguments to be passed to the deserializers.

        :return: Deserialized.
        :rtype: objetto.data.SetData

        :raises objetto.exceptions.SerializationError: Can't deserialize.
        """
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise SerializationError(error)
        state = SetState(
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
        return sorted(
            (self.serialize_value(v, location=None, **kwargs) for v in self._state),
            key=lambda v: hash(v),
        )

    @property
    @final
    def _state(self):
        # type: () -> SetState[T]
        """
        Internal state.

        :rtype: objetto.states.SetState
        """
        return cast("SetState", super(BaseSetStructure, self)._state)


class InteractiveSetData(
    SetData[T],
    BaseInteractiveSetStructure[T],
    BaseInteractiveAuxiliaryData[T],
):
    """
    Interactive set data.

    Inherits from:
      - :class:`objetto.data.SetData`
      - :class:`objetto.bases.BaseInteractiveSetStructure`
      - :class:`objetto.bases.BaseInteractiveAuxiliaryData`
    """

    __slots__ = ()
