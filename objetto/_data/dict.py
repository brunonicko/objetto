# -*- coding: utf-8 -*-
"""Dictionary data structures."""

from typing import TYPE_CHECKING, TypeVar, cast, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, with_metaclass

from .._bases import final
from .._states import BaseState, DictState
from .._structures import (
    BaseDictStructure,
    BaseDictStructureMeta,
    BaseInteractiveDictStructure,
    KeyRelationship,
    SerializationError,
)
from .bases import (
    BaseAuxiliaryData,
    BaseAuxiliaryDataMeta,
    BaseInteractiveAuxiliaryData,
)

if TYPE_CHECKING:
    from typing import Any, Dict, Iterable, Mapping, Tuple, Type, Union


__all__ = ["DictDataMeta", "DictData", "InteractiveDictData"]


T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.


class DictDataMeta(BaseAuxiliaryDataMeta, BaseDictStructureMeta):
    """
    Metaclass for :class:`objetto.data.DictData`.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryDataMeta`
      - :class:`objetto.bases.BaseDictStructureMeta`

    Features:
      - Defines a base auxiliary type.
    """

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[DictData]
        """
        Base auxiliary container type.

        :rtype: type[objetto.data.DictData]
        """
        return DictData


# noinspection PyTypeChecker
_DD = TypeVar("_DD", bound="DictData")


class DictData(
    with_metaclass(
        DictDataMeta,
        BaseDictStructure[KT, VT],
        BaseAuxiliaryData[KT],
    )
):
    """
    Dictionary data.

    Metaclass:
      - :class:`objetto.data.DictDataMeta`

    Inherits from:
      - :class:`objetto.bases.BaseDictStructure`
      - :class:`objetto.bases.BaseAuxiliaryData`

    Inherited by:
      - :class:`objetto.data.InteractiveDictData`

    :param initial: Initial values.
    :type initial: collections.abc.Mapping or collections.abc.Iterable[\
tuple[collections.abc.Hashable, Any]]
    """

    __slots__ = ()

    _key_relationship = KeyRelationship()
    """
    Relationship for dictionary keys.

    :type: objetto.data.KeyRelationship
    """

    @classmethod
    @final
    def __make__(cls, state=DictState()):
        # type: (Type[_DD], BaseState) -> _DD
        """
        Make a new dictionary data.

        :param state: Internal state.
        :return: New dictionary data.
        """
        return super(DictData, cls).__make__(state)

    @final
    def __init__(self, initial=()):
        # type: (Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]]) -> None
        self._init_state(self.__get_initial_state(dict(initial)))

    @classmethod
    @final
    def __get_initial_state(cls, input_values, factory=True):
        # type: (Mapping[KT, VT], bool) -> DictState[KT, VT]
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        if not cls._key_relationship.passthrough or not cls._relationship.passthrough:
            state = DictState(
                (
                    cls._key_relationship.fabricate_key(k, factory=factory),
                    cls._relationship.fabricate_value(v, factory=factory),
                )
                for k, v in iteritems(input_values)
            )
        else:
            state = DictState(input_values)
        return state

    @final
    def _clear(self):
        # type: (_DD) -> _DD
        """
        Clear all keys and values.

        :return: Transformed.
        :rtype: objetto.data.DictData
        """
        return type(self).__make__()

    @final
    def _set(self, key, value):
        # type: (_DD, KT, VT) -> _DD
        """
        Set value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.data.DictData
        """
        cls = type(self)
        key = cls._key_relationship.fabricate_key(key)
        value = cls._relationship.fabricate_value(value)
        return cls.__make__(self._state.set(key, value))

    @final
    def _discard(self, key):
        # type: (_DD, KT) -> _DD
        """
        Discard key if it exists.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.data.DictData
        """
        return type(self).__make__(self._state.discard(key))

    @final
    def _remove(self, key):
        # type: (_DD, KT) -> _DD
        """
        Delete existing key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.data.DictData
        """
        return type(self).__make__(self._state.remove(key))

    @overload
    def _update(self, __m, **kwargs):
        # type: (_DD, Mapping[KT, VT], VT) -> _DD
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (_DD, Iterable[Tuple[KT, VT]], VT) -> _DD
        pass

    @overload
    def _update(self, **kwargs):
        # type: (_DD, VT) -> _DD
        pass

    @final
    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        :rtype: objetto.data.DictData
        """
        update = dict(*args, **kwargs)
        cls = type(self)
        if not cls._key_relationship.passthrough or not cls._relationship.passthrough:
            fabricated_update = (
                (
                    cls._key_relationship.fabricate_key(k),
                    cls._relationship.fabricate_value(v),
                )
                for k, v in iteritems(update)
            )
            return cls.__make__(self._state.update(fabricated_update))
        else:
            return cls.__make__(self._state.update(update))

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Type[_DD], Dict, Any) -> _DD
        """
        Deserialize.

        :param serialized: Serialized.
        :type serialized: dict

        :param kwargs: Keyword arguments to be passed to the deserializers.

        :return: Deserialized.
        :rtype: objetto.data.DictData

        :raises objetto.exceptions.SerializationError: Can't deserialize.
        """
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise SerializationError(error)
        state = DictState(
            (
                cls._key_relationship.fabricate_key(k, factory=False),
                cls.deserialize_value(v, location=None, **kwargs),
            )
            for k, v in iteritems(serialized)
        )
        return cls.__make__(state)

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> Dict
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.

        :return: Serialized.
        :rtype: dict

        :raises objetto.exceptions.SerializationError: Can't serialize.
        """
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise SerializationError(error)
        return dict(
            (k, self.serialize_value(v, location=None, **kwargs))
            for k, v in iteritems(self._state)
        )

    @property
    @final
    def _state(self):
        # type: () -> DictState[KT, VT]
        """
        Internal state.

        :rtype: objetto.states.DictState
        """
        return cast("DictState", super(BaseDictStructure, self)._state)


class InteractiveDictData(
    DictData[KT, VT],
    BaseInteractiveDictStructure[KT, VT],
    BaseInteractiveAuxiliaryData[KT],
):
    """
    Interactive dictionary data.

    Inherits from:
      - :class:`objetto.data.DictData`
      - :class:`objetto.bases.BaseInteractiveDictStructure`
      - :class:`objetto.bases.BaseInteractiveAuxiliaryData`
    """

    __slots__ = ()
