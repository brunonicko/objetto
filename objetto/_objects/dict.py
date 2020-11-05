# -*- coding: utf-8 -*-
"""Dictionary object."""

from typing import TYPE_CHECKING, Generic, TypeVar, cast

from six import with_metaclass, iteritems
from six.moves import collections_abc

from .._bases import final, init_context
from .base import BaseAuxiliaryObjectMeta, BaseAuxiliaryObject
from .._containers.dict import DictContainerMeta, DictContainer, MutableDictContainer
from ..utils.immutable import ImmutableDict

if TYPE_CHECKING:
    from typing import (
        Any, Tuple, Type, Union, Mapping, Iterable, Dict, Iterator
    )

__all__ = ["DictObjectMeta", "DictObject", "InteractiveDictObject"]

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class DictObjectMeta(BaseAuxiliaryObjectMeta, DictContainerMeta):
    """Metaclass for :class:`DictObject`."""

    @property
    @final
    def _auxiliary_obj_type(cls):
        # type: () -> Type[DictObject]
        """Base auxiliary object type."""
        return DictObject


class DictObject(
    with_metaclass(
        DictObjectMeta,
        BaseAuxiliaryObject,
        DictContainer,
        Generic[_KT, _VT],
    )
):
    """Dictionary object."""
    __slots__ = ("__state",)

    @final
    def __init__(self, initial=()):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> None
        pass

    def __getitem__(self, key):
        # type: (_KT) -> _VT
        return self._state[key]

    def __len__(self):
        # type: () -> int
        return len(self._state)

    def __iter__(self):
        # type: () -> Iterator[_KT]
        # TODO: read context?
        for key in self._state:
            yield key

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Dict, Any) -> DictObject
        """Deserialize."""
        # TODO: app
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise RuntimeError(error)

        input_values = dict(
            (k, cls.deserialize_value(v, None, **kwargs))
            for k, v in iteritems(serialized)
        )
        state = cls.__get_initial_state(input_values, factory=False)
        return cls.__make(state)

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> Dict
        """Serialize."""
        # TODO: app
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise RuntimeError(error)

        return dict(
            (k, self.serialize_value(v, None, **kwargs))
            for k, v in iteritems(self._state)
        )

    @property
    @final
    def _state(self):
        # type: () -> ImmutableDict[_KT, _VT]
        """Internal state."""
        return self.__state


class InteractiveDictObject(DictObject, MutableDictContainer):
    """Interactive dictionary object."""
