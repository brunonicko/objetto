# -*- coding: utf-8 -*-
"""Dictionary data."""

from typing import TYPE_CHECKING, Generic, TypeVar, cast

from six import with_metaclass, iteritems, iterkeys, itervalues
from six.moves import collections_abc

from .._bases import final, init_context
from .bases import BaseAuxiliaryDataMeta, BaseAuxiliaryData
from .._containers.dict import DictContainerMeta, SemiInteractiveDictContainer
from ..utils.custom_repr import custom_mapping_repr
from ..utils.immutable import ImmutableDict

if TYPE_CHECKING:
    from typing import Any, Tuple, Type, Union, Mapping, Iterable, Dict, Iterator

__all__ = ["DictDataMeta", "DictData", "InteractiveDictData"]

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class DictDataMeta(BaseAuxiliaryDataMeta, DictContainerMeta):
    """Metaclass for :class:`DictData`."""

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[DictData]
        """Base auxiliary container type."""
        return DictData


class DictData(
    with_metaclass(
        DictDataMeta, BaseAuxiliaryData, SemiInteractiveDictContainer, Generic[_KT, _VT]
    )
):
    """
    Dictionary data.

    :param initial: Initial values.
    """
    __slots__ = ()

    @classmethod
    @final
    def __make__(cls, state=ImmutableDict()):
        # type: (ImmutableDict) -> DictData
        """
        Make a new dictionary data.

        :param state: Internal state.
        :return: New dictionary data.
        """
        return cast("DictData", super(DictData, cls).__make__(state))

    @final
    def __init__(self, initial=()):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> None
        if type(initial) is type(self):
            self._init_state(getattr(initial, "_state"))
        else:
            self._init_state(self.__get_initial_state(dict(initial)))

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        if type(self)._relationship.represented:
            return custom_mapping_repr(
                self._state,
                prefix="{}({{".format(type(self).__fullname__),
                suffix="})",
            )
        else:
            return "<{}>".format(type(self).__fullname__)

    def __getitem__(self, key):
        # type: (_KT) -> _VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Invalid key.
        """
        return self._state[key]

    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self._state)

    def __iter__(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key in self._state:
            yield key

    def iteritems(self):
        # type: () -> Iterator[Tuple[_KT, _VT]]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key, value in iteritems(self.__internal):
            yield key, value

    def iterkeys(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in iterkeys(self.__internal):
            yield key

    def itervalues(self):
        # type: () -> Iterator[_VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in itervalues(self.__internal):
            yield value

    @classmethod
    @final
    def __get_initial_state(cls, input_values, factory=True):
        # type: (Mapping, bool) -> ImmutableDict
        """
        Get initial state.

        :param input_values: Input mapping.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        state = ImmutableDict(
            (
                cls._key_relationship.fabricate_key(k, factory=factory),
                cls._relationship.fabricate_value(v, factory=factory),
            )
            for k, v in iteritems(input_values)
        )
        return state

    @final
    def get(self, key, fallback=None):
        # type: (_KT, Any) -> _VT
        """
        Get value at key, return fallback value if not found.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._state.get(key, fallback)

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Dict, Any) -> DictData
        """Deserialize."""
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise RuntimeError(error)

        input_values = dict(
            (k, cls.deserialize_value(v, None, **kwargs))
            for k, v in iteritems(serialized)
        )
        state = cls.__get_initial_state(input_values, factory=False)
        return cls.__make__(state)

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> Dict
        """Serialize."""
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise RuntimeError(error)

        return dict(
            (k, self.serialize_value(v, None, **kwargs))
            for k, v in iteritems(self._state)
        )

    def copy(self):
        # type: () -> DictData
        return self

    def _clear(self):
        # type: () -> DictData
        return type(self).__make__()

    def _discard(self, key):
        # type: (_KT) -> DictData
        return type(self).__make__(self._state.discard(key))

    def _remove(self, key):
        # type: (_KT) -> DictData
        return type(self).__make__(self._state.remove(key))

    def _set(self, key, value):
        # type: (_KT, _VT) -> DictData
        cls = type(self)
        key = cls._key_relationship.fabricate_key(key)
        value = cls._relationship.fabricate_value(value)
        return cls.__make__(self._state.set(key, value))

    def _update(self, update):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> DictData
        cls = type(self)
        update = (
            (
                cls._key_relationship.fabricate_key(k),
                cls._relationship.fabricate_value(v),
            )
            for k, v in (
                iteritems(update) if isinstance(update, collections_abc.Mapping)
                else update
            )
        )
        return cls.__make__(self._state.update(update))

    @property
    @final
    def _state(self):
        # type: () -> ImmutableDict[_KT, _VT]
        """Internal state."""
        return self.__state


class InteractiveDictData(DictData):
    """Interactive dictionary data."""

    def clear(self):
        # type: () -> InteractiveDictData
        return self._clear()

    def discard(self, key):
        # type: (_KT) -> InteractiveDictData
        return self._discard(key)

    def remove(self, key):
        # type: (_KT) -> InteractiveDictData
        return self._remove(key)

    def set(self, key, value):
        # type: (_KT, _VT) -> InteractiveDictData
        return self._set(key, value)

    def update(self, update):
        # type: (Mapping[_KT, _VT]) -> InteractiveDictData
        return self._update(update)
