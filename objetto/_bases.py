from typing import TypeVar

import six
from basicco import SlottedBaseMeta, SlottedBase
from basicco.weak_reference import WeakReference
from basicco.runtime_final import final
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
from tippo import Generic

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class BaseObjectMeta(BaseStructureMeta):
    """Metaclass for :class:`BasePrivateObject`."""


# noinspection PyAbstractClass
class BasePrivateObject(six.with_metaclass(BaseObjectMeta, BaseMutableStructure)):
    """Base private object."""

    __slots__ = ("__node", "__app")

    @property
    def __node__(self):
        # type: (BPO) -> Node[BPO]
        """Node."""
        try:
            return self.__node  # type: ignore
        except AttributeError:
            self.__node = Node.__new__(Node)
            self.__node.__init__(self)  # type: ignore
            return self.__node


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
class PrivateCollectionObject(BasePrivateObject, BaseMutableCollectionStructure[T_co]):
    """Private collection object."""

    __slots__ = ()


PCO = TypeVar("PCO", bound=PrivateCollectionObject)  # private collection object self type


# noinspection PyAbstractClass
class CollectionObject(PrivateCollectionObject[T_co], BaseUserMutableCollectionStructure[T_co]):
    """Base collection object."""

    __slots__ = ()


CO = TypeVar("CO", bound=CollectionObject)  # collection object self type


# noinspection PyAbstractClass
class ProxyPrivateCollectionObject(
    BaseProxyPrivateObject[PCO],
    BaseProxyMutableCollectionStructure[PCO, T_co],
    PrivateCollectionObject[T_co],
):
    """Proxy private collection object."""

    __slots__ = ()


# noinspection PyAbstractClass
class ProxyCollectionObject(
    ProxyPrivateCollectionObject[CO, T_co],
    BaseProxyUserMutableCollectionStructure[CO, T_co],
    CollectionObject[T_co],
):
    """Proxy collection object."""

    __slots__ = ()


class NodeMeta(SlottedBaseMeta):
    """Metaclass for :class:`Node`."""

    def __call__(cls, obj):  # noqa
        """
        Enforce a singleton pattern (one node per object).

        :param obj: Object.
        :return: Node.
        """
        try:
            return obj.__node__
        except AttributeError:
            return super(NodeMeta, cls).__call__(obj)


@final
class Node(six.with_metaclass(NodeMeta, SlottedBase, Generic[BPO])):
    """Represents an object in the hierarchy."""

    __slots__ = ("__obj_ref",)

    def __init__(self, obj):
        # type: (BPO) -> None
        """
        :param obj: Object.
        """
        self.__obj_ref = WeakReference(obj)

    @property
    def obj(self):
        # type: () -> BPO
        """Object."""
        obj = self.__obj_ref()
        if obj is None:
            error = "object is no longer in memory"
            raise ReferenceError(error)
        return obj
