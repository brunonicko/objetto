import copy
import itertools
from typing import Iterable, TypeVar

from estruttura import (
    MutableListStructure,
    ProxyMutableListStructure,
    ProxyUserMutableListStructure,
    UserMutableListStructure,
)
from pyrsistent import pvector
from pyrsistent.typing import PVector

from ._bases import (
    ObjectCollection,
    PrivateObjectCollection,
    ProxyObjectCollection,
    ProxyPrivateObjectCollection,
)

T = TypeVar("T")


class PrivateListObject(PrivateObjectCollection[T], MutableListStructure[T]):
    """Private dictionary object."""

    __slots__ = ("_state",)

    def __iter__(self):
        return iter(self._state)

    def __len__(self):
        return len(self._state)

    def __getitem__(self, item):
        return self._state[item]

    def _hash(self):
        return hash(self._state)

    def _eq(self, other):
        if isinstance(other, dict):
            return self._state == other
        else:
            return isinstance(other, type(self)) and self._state == other._state

    def _do_init(self, initial_values):
        # type: (Iterable[T]) -> None
        self._state = pvector(initial_values)  # type: PVector[T]

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self._state = pvector(values)
        return self

    def count(self, value):
        return self._state.count(value)

    def index(self, value, start=None, stop=None):
        if start is None and stop is None:
            return self._state.count(value)
        elif start is not None and stop is None:
            return self._state.count(value, start)  # noqa
        elif start is not None and stop is not None:
            return self._state.count(value, start, stop)  # noqa
        else:
            error = "provided 'stop' but did not provide 'start'"
            raise TypeError(error)


PLD = TypeVar("PLD", bound=PrivateListObject)  # private dictionary object self type


class ListObject(PrivateListObject[T], ObjectCollection[T], UserMutableListStructure[T]):
    """List object."""

    __slots__ = ()

    def _do_update(self, index, stop, old_values, new_values):
        pairs = itertools.chain.from_iterable(zip(range(index, stop), new_values))
        new_state = self._state.mset(*pairs)  # type: ignore
        new_self = copy.copy(self)
        new_self._state = new_state
        return new_self

    def _do_insert(self, index, new_values):
        if index == len(self._state):
            new_state = self._state.extend(new_values)
        elif index == 0:
            new_state = pvector(new_values) + self._state
        else:
            new_state = self._state[:index] + pvector(new_values) + self._state[index:]
        new_self = copy.copy(self)
        new_self._state = new_state
        return new_self

    def _do_move(self, target_index, index, stop, post_index, post_stop, values):
        state = self._state.delete(index, stop)
        if post_index == len(state):
            new_state = state.extend(values)
        elif post_index == 0:
            new_state = pvector(values) + state
        else:
            new_state = state[:post_index] + pvector(values) + state[post_index:]
        new_self = copy.copy(self)
        new_self._state = new_state
        return new_self

    def _do_delete(self, index, stop, old_values):
        new_state = self._state.delete(index, stop)
        new_self = copy.copy(self)
        new_self._state = new_state
        return new_self


LD = TypeVar("LD", bound=ListObject)  # dictionary object self type


class ProxyPrivateListObject(
    ProxyPrivateObjectCollection[PLD, T],
    ProxyMutableListStructure[PLD, T],
    PrivateListObject[T],
):
    """Proxy private dictionary object."""

    __slots__ = ()


class ProxyListObject(
    ProxyObjectCollection[LD, T],
    ProxyPrivateListObject[LD, T],
    ProxyUserMutableListStructure[LD, T],
    ListObject[T],
):
    """Proxy dictionary object."""

    __slots__ = ()
