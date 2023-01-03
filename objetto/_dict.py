import copy
from typing import TypeVar

from basicco import mapping_proxy
from estruttura import (
    MutableDictStructure,
    ProxyMutableDictStructure,
    ProxyUserMutableDictStructure,
    UserMutableDictStructure,
)
from pyrsistent import pmap
from pyrsistent.typing import PMap

from ._bases import (
    CollectionObject,
    PrivateCollectionObject,
    ProxyCollectionObject,
    ProxyPrivateCollectionObject,
)

KT = TypeVar("KT")
VT = TypeVar("VT")


class PrivateDictObject(PrivateCollectionObject[KT], MutableDictStructure[KT, VT]):
    """Private dictionary object."""

    __slots__ = ("_state",)

    def __iter__(self):
        return iter(self._state)

    def __len__(self):
        return len(self._state)

    def __getitem__(self, key):
        return self._state[key]

    def _hash(self):
        return hash(self._state)

    def _eq(self, other):
        if isinstance(other, dict):
            return self._state == other
        else:
            return isinstance(other, type(self)) and self._state == other._state

    def _do_init(self, initial_values):
        # type: (mapping_proxy.MappingProxyType[KT, VT]) -> None
        self._state = pmap(initial_values)  # type: PMap[KT, VT]

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self._state = pmap(values)
        return self


PDD = TypeVar("PDD", bound=PrivateDictObject)  # private dictionary object self type


class DictObject(PrivateDictObject[KT, VT], CollectionObject[KT], UserMutableDictStructure[KT, VT]):
    """Dictionary object."""

    __slots__ = ()

    def _do_clear(self):  # FIXME
        return self

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts, all_updates):
        new_state = self._state.update(updates_and_inserts)
        if deletes:
            new_state_evolver = new_state.evolver()
            for key in deletes:
                del new_state_evolver[key]
            new_state = new_state_evolver.persistent()
        new_self = copy.copy(self)
        new_self._state = new_state
        return new_self


DD = TypeVar("DD", bound=DictObject)  # dictionary object self type


class ProxyPrivateDictObject(
    ProxyPrivateCollectionObject[PDD, KT],
    ProxyMutableDictStructure[PDD, KT, VT],
    PrivateDictObject[KT, VT],
):
    """Proxy private dictionary object."""

    __slots__ = ()


class ProxyDictObject(
    ProxyCollectionObject[DD, KT],
    ProxyPrivateDictObject[DD, KT, VT],
    ProxyUserMutableDictStructure[DD, KT, VT],
    DictObject[KT, VT],
):
    """Proxy dictionary object."""

    __slots__ = ()
