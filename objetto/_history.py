from six import integer_types

from ._objects import Attribute, Object, Relationship


class HistoryObject(Object):
    __slots__ = ()

    size = Attribute(Relationship(integer_types, checked=False))
