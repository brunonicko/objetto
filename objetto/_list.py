import itertools
from typing import TypeVar

from estruttura import (
    MutableListStructure,
    ProxyMutableListStructure,
    ProxyUserMutableListStructure,
    UserMutableListStructure,
)
from pyrsistent import pvector
from pyrsistent.typing import PVector

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


class ListUpdated(BaseEvent):
    """Event: list object updated."""


class ListInserted(BaseEvent):
    """Event: list object inserted."""


class ListMoved(BaseEvent):
    """Event: list object moved."""


class ListDeleted(BaseEvent):
    """Event: list object deleted."""


class PrivateListObject(PrivateCollectionObject[T], MutableListStructure[T]):
    """Private list object."""

    __slots__ = ()

    def __iter__(self):
        return iter(self._state)

    def __len__(self):
        return len(self._state)

    def __getitem__(self, item):
        return self._state[item]

    def _hash(self):
        return hash(self._state)

    def _eq(self, other):
        if isinstance(other, list):
            return self._state == other
        else:
            return isinstance(other, type(self)) and self._state == other._state

    def _do_init(self, initial_values):
        with require_context() as ctx:
            state = pvector(initial_values)
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

    @property
    def _state(self):
        # type: () -> PVector[T]
        return super(PrivateListObject, self)._state


PLO = TypeVar("PLO", bound=PrivateListObject)  # private list object self type


class ListObject(PrivateListObject[T], CollectionObject[T], UserMutableListStructure[T]):
    """List object."""

    __slots__ = ()

    def _do_clear(self):
        with require_context() as ctx:
            releases = ()
            if self.relationship.parent:
                releases += objs_only(self._state)
            ctx.update(
                obj=self,
                state=pvector(),
                event=ListUpdated(),
                adoptions=(),
                releases=releases,
            )
        return self

    def _do_update(self, index, stop, old_values, new_values):
        with require_context() as ctx:
            pairs = itertools.chain.from_iterable(zip(range(index, stop), new_values))
            state = self._state.mset(*pairs)  # type: ignore
            adoptions = ()
            releases = ()
            if self.relationship.parent:
                adoptions += objs_only(new_values)
                releases += objs_only(old_values)
            ctx.update(
                obj=self,
                state=state,
                event=ListUpdated(),
                adoptions=adoptions,
                releases=releases,
            )
        return self

    def _do_insert(self, index, new_values):
        with require_context() as ctx:
            if index == len(self._state):
                state = self._state.extend(new_values)
            elif index == 0:
                state = pvector(new_values) + self._state
            else:
                state = self._state[:index] + pvector(new_values) + self._state[index:]
            adoptions = ()
            if self.relationship.parent:
                adoptions += objs_only(new_values)
            ctx.update(
                obj=self,
                state=state,
                event=ListInserted(),
                adoptions=adoptions,
                releases=(),
            )
        return self

    def _do_move(self, target_index, index, stop, post_index, post_stop, values):
        with require_context() as ctx:
            state = self._state.delete(index, stop)
            if post_index == len(state):
                state = state.extend(values)
            elif post_index == 0:
                state = pvector(values) + state
            else:
                state = state[:post_index] + pvector(values) + state[post_index:]
            ctx.update(
                obj=self,
                state=state,
                event=ListMoved(),
                adoptions=(),
                releases=(),
            )
        return self

    def _do_delete(self, index, stop, old_values):
        with require_context() as ctx:
            state = self._state.delete(index, stop)
            releases = ()
            if self.relationship.parent:
                releases += objs_only(old_values)
            ctx.update(
                obj=self,
                state=state,
                event=ListDeleted(),
                adoptions=(),
                releases=releases,
            )
        return self


LO = TypeVar("LO", bound=ListObject)  # list object self type


class ProxyPrivateListObject(
    ProxyPrivateCollectionObject[PLO, T],
    ProxyMutableListStructure[PLO, T],
    PrivateListObject[T],
):
    """Proxy private list object."""

    __slots__ = ()


class ProxyListObject(
    ProxyCollectionObject[LO, T],
    ProxyPrivateListObject[LO, T],
    ProxyUserMutableListStructure[LO, T],
    ListObject[T],
):
    """Proxy list object."""

    __slots__ = ()
