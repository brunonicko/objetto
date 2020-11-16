# -*- coding: utf-8 -*-
"""Dictionary data."""

from typing import TYPE_CHECKING, Generic, TypeVar, cast

from six import iteritems, iterkeys, itervalues, with_metaclass
from six.moves import collections_abc

from .._bases import final
from .._containers.dict import (
    DictContainerMeta,
    KeyRelationship,
    SemiInteractiveDictContainer,
)
from ..utils.custom_repr import custom_mapping_repr
from ..utils.immutable import ImmutableDict
from .bases import (
    BaseAuxiliaryData,
    BaseAuxiliaryDataMeta,
    BaseInteractiveAuxiliaryData,
)

if TYPE_CHECKING:
    from typing import Any, Dict, Iterable, Iterator, Mapping, Tuple, Type, Union

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
        DictDataMeta,
        BaseAuxiliaryData,
        SemiInteractiveDictContainer,
        Generic[_KT, _VT],
    )
):
    """
    Dictionary data.

    :param initial: Initial values.
    """

    __slots__ = ()
    _key_relationship = KeyRelationship()

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

    @final
    def __getitem__(self, key):
        # type: (_KT) -> _VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Invalid key.
        """
        return self._state[key]

    @final
    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key in self._state:
            yield key

    @classmethod
    @final
    def __get_initial_state(cls, input_values, factory=True):
        # type: (Mapping, bool) -> ImmutableDict
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        if not cls._key_relationship.passthrough or not cls._relationship.passthrough:
            state = ImmutableDict(
                (
                    cls._key_relationship.fabricate_key(k, factory=factory),
                    cls._relationship.fabricate_value(v, factory=factory),
                )
                for k, v in iteritems(input_values)
            )
        else:
            state = ImmutableDict(input_values)
        return state

    @final
    def _clear(self):
        # type: () -> DictData
        """
        Clear all keys and values.

        :return: New version.
        """
        return type(self).__make__()

    @final
    def _set(self, key, value):
        # type: (_KT, _VT) -> DictData
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: New version.
        """
        cls = type(self)
        key = cls._key_relationship.fabricate_key(key)
        value = cls._relationship.fabricate_value(value)
        return cls.__make__(self._state.set(key, value))

    @final
    def _discard(self, key):
        # type: (_KT) -> DictData
        """
        Discard key if it exists.

        :param key: Key.
        :return: New version.
        """
        return type(self).__make__(self._state.discard(key))

    @final
    def _remove(self, key):
        # type: (_KT) -> DictData
        """
        Delete existing key.

        :param key: Key.
        :return: New version.
        """
        return type(self).__make__(self._state.remove(key))

    @final
    def _update(self, update):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> DictData
        """
        Update keys and values.

        :param update: Updates.
        :return: New version.
        """
        cls = type(self)
        if not cls._key_relationship.passthrough or not cls._relationship.passthrough:
            update = (
                (
                    cls._key_relationship.fabricate_key(k),
                    cls._relationship.fabricate_value(v),
                )
                for k, v in (
                    iteritems(update)
                    if isinstance(update, collections_abc.Mapping)
                    else update
                )
            )
        return cls.__make__(self._state.update(update))

    @final
    def iteritems(self):
        # type: () -> Iterator[Tuple[_KT, _VT]]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key, value in iteritems(self._state):
            yield key, value

    @final
    def iterkeys(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in iterkeys(self._state):
            yield key

    @final
    def itervalues(self):
        # type: () -> Iterator[_VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in itervalues(self._state):
            yield value

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Dict, Any) -> DictData
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise RuntimeError(error)
        state = ImmutableDict(
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
        """
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise RuntimeError(error)
        return dict(
            (k, self.serialize_value(v, location=None, **kwargs))
            for k, v in iteritems(self._state)
        )

    @property
    @final
    def _state(self):
        # type: () -> ImmutableDict[_KT, _VT]
        """Internal state."""
        return cast("ImmutableDict", super(DictData, self)._state)


class InteractiveDictData(DictData, BaseInteractiveAuxiliaryData):
    """Interactive dictionary data."""

    @final
    def clear(self):
        # type: () -> InteractiveDictData
        """
        Clear all keys and values.

        :return: New version.
        """
        return self._clear()

    @final
    def discard(self, key):
        # type: (_KT) -> InteractiveDictData
        """
        Discard key if it exists.

        :param key: Key.
        :return: New version.
        """
        return self._discard(key)

    @final
    def remove(self, key):
        # type: (_KT) -> InteractiveDictData
        """
        Delete existing key.

        :param key: Key.
        :return: New version.
        """
        return self._remove(key)

    @final
    def set(self, key, value):
        # type: (_KT, _VT) -> InteractiveDictData
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: New version.
        """
        return self._set(key, value)

    @final
    def update(self, update):
        # type: (Mapping[_KT, _VT]) -> InteractiveDictData
        """
        Update keys and values.

        :param update: Updates.
        :return: New version.
        """
        return self._update(update)
