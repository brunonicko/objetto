import copy
from typing import TypeVar

import six
from basicco import mangling, mapping_proxy, obj_state
from estruttura import (
    MutableStructure,
    ProxyMutableStructure,
    ProxyStructureMeta,
    ProxyUserMutableStructure,
    StructureMeta,
    UserMutableStructure,
)

from ._attribute import Attribute
from ._bases import (
    BaseObject,
    BaseObjectMeta,
    BasePrivateObject,
    BaseProxyObject,
    BaseProxyObjectMeta,
    BaseProxyPrivateObject,
)

KT = TypeVar("KT")
VT = TypeVar("VT")


class ObjectMeta(StructureMeta, BaseObjectMeta):
    @staticmethod
    def __edit_dct__(this_attribute_map, attribute_map, name, bases, dct, **kwargs):  # noqa
        slots = list(dct.get("__slots__", ()))
        for attribute_name, attribute in six.iteritems(this_attribute_map):
            if attribute.constant:
                dct[attribute_name] = attribute.default
            else:
                slots.append(mangling.mangle(attribute_name, name))
                del dct[attribute_name]
        dct["__slots__"] = tuple(slots)
        return dct


class PrivateObject(six.with_metaclass(ObjectMeta, BasePrivateObject, MutableStructure)):
    """Private object."""

    __slots__ = ()

    __attribute_type__ = Attribute

    def __copy__(self):
        cls = type(self)
        new_self = cls.__new__(cls)
        obj_state.update_state(new_self, obj_state.get_state(self))
        return new_self

    def __getitem__(self, name):
        return getattr(self, name)

    def __contains__(self, name):
        return isinstance(name, six.string_types) and name in type(self).__attribute_map__ and hasattr(self, name)

    def __setattr__(self, name, value):
        if name in type(self).__attribute_map__:
            error = "{!r} objects are immutable".format(type(self).__name__)
            raise AttributeError(error)
        super(PrivateObject, self).__setattr__(name, value)

    def _do_init(self, initial_values):
        # type: (mapping_proxy.MappingProxyType) -> None
        for name, value in six.iteritems(initial_values):
            object.__setattr__(self, name, value)

    @classmethod
    def _do_deserialize(cls, values):
        self = cls.__new__(cls)
        self._do_init(values)
        return self


PO = TypeVar("PO", bound=PrivateObject)  # private object self type


class Object(PrivateObject, BaseObject, UserMutableStructure):
    """Object."""

    __slots__ = ()

    def _do_update(self, inserts, deletes, updates_old, updates_new, updates_and_inserts, all_updates):
        new_self = copy.copy(self)
        new_self._do_init(updates_and_inserts)
        return new_self


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
