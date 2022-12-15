from typing import TypeVar

import six
from estruttura import (
    BaseMutableCollectionStructure,
    BaseMutableStructure,
    BaseProxyMutableCollectionStructure,
    BaseProxyMutableStructure,
    BaseProxyStructureMeta,
    BaseProxyUserMutableCollectionStructure,
    BaseProxyUserMutableStructure,
    BaseStructureMeta,
    BaseUserMutableCollectionStructure,
    BaseUserMutableStructure,
)

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class BaseObjectMeta(BaseStructureMeta):
    """Metaclass for :class:`BasePrivateObject`."""


# noinspection PyAbstractClass
class BasePrivateObject(six.with_metaclass(BaseObjectMeta, BaseMutableStructure)):
    """Base private object."""

    __slots__ = ()


BPO = TypeVar("BPO", bound=BasePrivateObject)  # base private object self type


# noinspection PyAbstractClass
class BaseObject(BasePrivateObject, BaseUserMutableStructure):
    """Base object."""

    __slots__ = ()


BO = TypeVar("BO", bound=BaseObject)  # base object self type


class BaseProxyObjectMeta(BaseObjectMeta, BaseProxyStructureMeta):
    """Metaclass for :class:`BaseProxyPrivateObject`."""


# noinspection PyAbstractClass
class BaseProxyPrivateObject(
    six.with_metaclass(BaseProxyObjectMeta, BaseProxyMutableStructure[BPO], BasePrivateObject)
):
    """Base proxy private object."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseProxyObject(BaseProxyPrivateObject[BO], BaseProxyUserMutableStructure[BO], BaseObject):
    """Base proxy object."""

    __slots__ = ()


# noinspection PyAbstractClass
class PrivateObjectCollection(BasePrivateObject, BaseMutableCollectionStructure[T_co]):
    """Private object collection."""

    __slots__ = ()


PDC = TypeVar("PDC", bound=PrivateObjectCollection)  # private object collection self type


# noinspection PyAbstractClass
class ObjectCollection(PrivateObjectCollection[T_co], BaseUserMutableCollectionStructure[T_co]):
    """Base object collection."""

    __slots__ = ()


DC = TypeVar("DC", bound=ObjectCollection)  # object collection self type


# noinspection PyAbstractClass
class ProxyPrivateObjectCollection(
    BaseProxyPrivateObject[PDC],
    BaseProxyMutableCollectionStructure[PDC, T_co],
    PrivateObjectCollection[T_co],
):
    """Proxy private object collection."""

    __slots__ = ()


# noinspection PyAbstractClass
class ProxyObjectCollection(
    ProxyPrivateObjectCollection[DC, T_co],
    BaseProxyUserMutableCollectionStructure[DC, T_co],
    ObjectCollection[T_co],
):
    """Proxy object collection."""

    __slots__ = ()
