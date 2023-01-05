from typing import TypeVar

from estruttura import (
    MutableSetStructure,
    ProxyMutableSetStructure,
    ProxyUserMutableSetStructure,
    UserMutableSetStructure,
)
from pyrsistent import pset
from pyrsistent.typing import PSet

from ._bases import (
    require_context,
    objs_only,
    BaseEvent,
    CollectionObject,
    PrivateCollectionObject,
    ProxyCollectionObject,
    ProxyPrivateCollectionObject,
)

T = TypeVar("T")


class SetAdded(BaseEvent):
    """Event: set object added."""


class SetRemoved(BaseEvent):
    """Event: set object removed."""


class PrivateSetObject(PrivateCollectionObject[T], MutableSetStructure[T]):
    """Private set object."""

    __slots__ = ()

    def __iter__(self):
        return iter(self._state)

    def __len__(self):
        return len(self._state)

    def __contains__(self, value):
        return value in self._state

    def _hash(self):
        return hash(self._state)

    def _eq(self, other):
        if isinstance(other, set):
            return self._state == other
        else:
            return isinstance(other, type(self)) and self._state == other._state

    def _do_init(self, initial_values):
        with require_context() as ctx:
            state = pset(initial_values)
            adoptions = ()
            if self.relationship.parent:
                adoptions += objs_only(state)
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

    def isdisjoint(self, iterable):
        return self._state.isdisjoint(iterable)

    def issubset(self, iterable):
        return self._state.issubset(iterable)

    def issuperset(self, iterable):
        return self._state.issuperset(iterable)

    def intersection(self, iterable):
        return self._state.intersection(iterable)

    def symmetric_difference(self, iterable):
        return self._state.symmetric_difference(iterable)

    def union(self, iterable):
        return self._state.union(iterable)

    def difference(self, iterable):
        return self._state.difference(iterable)

    def inverse_difference(self, iterable):
        return pset(iterable).difference(self._state)

    @property
    def _state(self):
        # type: () -> PSet[T]
        return super(PrivateSetObject, self)._state


PSD = TypeVar("PSD", bound=PrivateSetObject)  # private set object self type


class SetObject(PrivateSetObject[T], CollectionObject[T], UserMutableSetStructure[T]):
    """Set object."""

    __slots__ = ()

    def _do_clear(self):
        with require_context() as ctx:
            releases = ()
            if self.relationship.parent:
                releases += objs_only(self._state)
            ctx.update(
                obj=self,
                state=pset(),
                event=SetRemoved(),
                adoptions=(),
                releases=releases,
            )
        return self

    def _do_remove(self, old_values):
        with require_context() as ctx:
            state = self._state.difference(old_values)
            releases = ()
            if self.relationship.parent:
                releases += objs_only(old_values)
            ctx.update(
                obj=self,
                state=state,
                event=SetAdded(),
                adoptions=(),
                releases=releases,
            )
        return self

    def _do_update(self, new_values):
        with require_context() as ctx:
            state = self._state.update(new_values)
            adoptions = ()
            if self.relationship.parent:
                adoptions += objs_only(new_values)
            ctx.update(
                obj=self,
                state=state,
                event=SetAdded(),
                adoptions=adoptions,
                releases=(),
            )
        return self


SD = TypeVar("SD", bound=SetObject)  # set object self type


class ProxyPrivateSetObject(
    ProxyPrivateCollectionObject[PSD, T],
    ProxyMutableSetStructure[PSD, T],
    PrivateSetObject[T],
):
    """Proxy private set object."""

    __slots__ = ()


class ProxySetObject(
    ProxyCollectionObject[SD, T],
    ProxyPrivateSetObject[SD, T],
    ProxyUserMutableSetStructure[SD, T],
    SetObject[T],
):
    """Proxy set object."""

    __slots__ = ()
