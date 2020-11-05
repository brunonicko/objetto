# -*- coding: utf-8 -*-
"""Dictionary data."""

from typing import TYPE_CHECKING, Generic, TypeVar, cast

from six import with_metaclass, iteritems
from six.moves import collections_abc

from .._bases import final, init_context
from .base import BaseAuxiliaryDataMeta, BaseAuxiliaryData
from .._containers.dict import DictContainerMeta, DictContainer
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
    def _auxiliary_data_type(cls):
        # type: () -> Type[DictData]
        """Base auxiliary data type."""
        return DictData


class DictData(
    with_metaclass(DictDataMeta, BaseAuxiliaryData, DictContainer, Generic[_KT, _VT])
):
    """Dictionary data."""
    __slots__ = ("__state",)

    @classmethod
    @final
    def __make__(cls, state=ImmutableDict()):
        # type: (Any) -> DictData
        self = cast("DictData", cls.__new__(cls))
        with init_context(self):
            self.__state = state
        return self

    @final
    def __init__(self, initial=()):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> None
        if type(initial) is type(self):
            self.__state = cast("DictData", initial).__state
        else:
            self.__state = self.__get_initial_state(dict(initial))

    def __repr__(self):
        # type: () -> str
        """Get representation."""
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
        return self._state[key]

    def __len__(self):
        # type: () -> int
        return len(self._state)

    def __iter__(self):
        # type: () -> Iterator[_KT]
        for key in self._state:
            yield key

    @classmethod
    @final
    def __get_initial_state(
        cls,
        input_values,  # type: Mapping
        factory=True,  # type: bool
    ):
        # type: (...) -> ImmutableDict
        """Get initial state."""
        state = ImmutableDict(
            (
                cls._key_relationship.fabricate_key(k, factory=factory),
                cls._relationship.fabricate_value(v, factory=factory),
            )
            for k, v in iteritems(input_values)
        )
        return state

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
