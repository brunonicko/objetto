from typing import Any, Type, TypeVar

import six
from basicco import mangling
from pyrsistent import pmap
from pyrsistent.typing import PMap
from estruttura import (
    AttributeMap,
    MutableStructure,
    ProxyMutableStructure,
    ProxyStructureMeta,
    ProxyUserMutableStructure,
    StructureMeta,
    UserMutableStructure,
)

from ._attribute import Attribute
from ._bases import (
    require_context,
    objs_only,
    BaseEvent,
    BaseObject,
    BaseObjectMeta,
    BasePrivateObject,
    BaseProxyObject,
    BaseProxyObjectMeta,
    BaseProxyPrivateObject,
)

KT = TypeVar("KT")
VT = TypeVar("VT")


class ObjectUpdated(BaseEvent):
    """Event: object updated."""


class ObjectMeta(StructureMeta, BaseObjectMeta):
    """Metaclass for :class:`PrivateObject`."""


class PrivateObject(six.with_metaclass(ObjectMeta, BasePrivateObject, MutableStructure)):
    """Private object."""

    __slots__ = ()

    __attribute_type__ = Attribute  # type: Type[Attribute[Any]]
    __attribute_map__ = AttributeMap()  # type: AttributeMap[str, Attribute[Any]]

    def __getitem__(self, name):
        return self._state[name]

    def __contains__(self, name):
        return name in self._state

    def _do_init(self, initial_values):
        with require_context() as ctx:
            state = pmap(initial_values)
            adoptions = objs_only(
                v for n, v in six.iteritems(initial_values) if type(self).__attribute_map__[n].relationship.parent
            )
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
        return super(PrivateObject, self)._state


PO = TypeVar("PO", bound=PrivateObject)  # private object self type


class Object(PrivateObject, BaseObject, UserMutableStructure):
    """Object."""

    __slots__ = ()

    def _do_clear(self):
        with require_context() as ctx:
            releases = objs_only(
                v for n, v in six.iteritems(self._state) if type(self).__attribute_map__[n].relationship.parent
            )
            ctx.update(
                obj=self,
                state=pmap(),
                event=ObjectUpdated(),
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
            adoptions = objs_only(
                v for n, v in six.iteritems(updates_and_inserts) if type(self).__attribute_map__[n].relationship.parent
            )
            releases = objs_only(
                v for n, v in six.iteritems(deletes) if type(self).__attribute_map__[n].relationship.parent
            )
            ctx.update(
                obj=self,
                state=state,
                event=ObjectUpdated(),
                adoptions=adoptions,
                releases=releases,
            )
        return self


D = TypeVar("D", bound=Object)  # object self type


class ProxyObjectMeta(BaseProxyObjectMeta, ProxyStructureMeta, ObjectMeta):
    pass


class ProxyPrivateObject(
    six.with_metaclass(
        ProxyObjectMeta,
        BaseProxyPrivateObject[PO],
        ProxyMutableStructure[PO],
        PrivateObject,
    )
):
    """Proxy private object."""

    __slots__ = ()


class ProxyObject(BaseProxyObject[D], ProxyPrivateObject[D], ProxyUserMutableStructure[D], Object):
    """Proxy object."""

    __slots__ = ()
