from typing import TypeVar

from estruttura import (
    MutableDictStructure,
    ProxyMutableDictStructure,
    ProxyUserMutableDictStructure,
    UserMutableDictStructure,
)
from pyrsistent import pmap
from pyrsistent.typing import PMap

from ._relationship import Relationship
from ._bases import (
    require_context,
    objs_only,
    BaseEvent,
    CollectionObject,
    PrivateCollectionObject,
    ProxyCollectionObject,
    ProxyPrivateCollectionObject,
)

KT = TypeVar("KT")
VT = TypeVar("VT")


class DictUpdated(BaseEvent):
    """Event: dictionary object updated."""


class PrivateDictObject(PrivateCollectionObject[KT], MutableDictStructure[KT, VT]):
    """Private dictionary object."""

    value_relationship = Relationship()  # type: Relationship[VT]

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
        with require_context() as ctx:
            state = pmap(initial_values)
            adoptions = ()
            if self.relationship.parent:
                adoptions += objs_only(state.keys())
            if self.value_relationship.parent:
                adoptions += objs_only(state.values())
            ctx.initialize(
                obj=self,
                state=state,
                adoptions=adoptions,
            )

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self._do_init(values)
        return self

    @property
    def _state(self):
        # type: () -> PMap[KT, VT]
        return super(PrivateDictObject, self)._state


PDO = TypeVar("PDO", bound=PrivateDictObject)  # private dictionary object self type


class DictObject(PrivateDictObject[KT, VT], CollectionObject[KT], UserMutableDictStructure[KT, VT]):
    """Dictionary object."""

    __slots__ = ()

    def _do_clear(self):
        with require_context() as ctx:
            releases = ()
            if self.relationship.parent:
                releases += objs_only(self._state.keys())
            if self.value_relationship.parent:
                releases += objs_only(self._state.values())
            ctx.update(
                obj=self,
                state=pmap(),
                event=DictUpdated(),
                adoptions=(),
                releases=releases,
            )
        return self

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts, all_updates):
        with require_context() as ctx:
            state = self._state.update(updates_and_inserts)
            if deletes:
                state_evolver = state.evolver()
                for key in deletes:
                    del state_evolver[key]
                state = state_evolver.persistent()
            adoptions = ()
            releases = ()
            if self.relationship.parent:
                adoptions += objs_only(inserts.keys())
                releases += objs_only(deletes.keys())
            if self.value_relationship.parent:
                adoptions += objs_only(updates_new.values()) + objs_only(inserts.values())
                releases += objs_only(updates_old.values()) + objs_only(deletes.values())
            ctx.update(
                obj=self,
                state=state,
                event=DictUpdated(),
                adoptions=adoptions,
                releases=releases,
            )
        return self


DO = TypeVar("DO", bound=DictObject)  # dictionary object self type


class ProxyPrivateDictObject(
    ProxyPrivateCollectionObject[PDO, KT],
    ProxyMutableDictStructure[PDO, KT, VT],
    PrivateDictObject[KT, VT],
):
    """Proxy private dictionary object."""

    __slots__ = ()


class ProxyDictObject(
    ProxyCollectionObject[DO, KT],
    ProxyPrivateDictObject[DO, KT, VT],
    ProxyUserMutableDictStructure[DO, KT, VT],
    DictObject[KT, VT],
):
    """Proxy dictionary object."""

    __slots__ = ()
