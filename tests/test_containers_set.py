# -*- coding: utf-8 -*-

import pytest

from six import with_metaclass
from slotted import SlottedSet, SlottedMutableSet

from objetto._containers.bases import (
    BaseRelationship,
    BaseAuxiliaryContainer,
    BaseSemiInteractiveAuxiliaryContainer,
    BaseInteractiveAuxiliaryContainer,
    BaseMutableAuxiliaryContainer,
)
from objetto._containers.set import (
    SetContainerMeta,
    SetContainer,
    SemiInteractiveSetContainer,
    InteractiveSetContainer,
    MutableSetContainer,
)
from objetto.utils.immutable import ImmutableSet


class MySetContainerMeta(SetContainerMeta):

    @property
    def _serializable_container_types(cls):
        return (MySetContainer,)

    @property
    def _relationship_type(cls):
        return BaseRelationship


class MySetContainer(with_metaclass(MySetContainerMeta, SetContainer)):
    __slots__ = ("__state",)
    _relationship = BaseRelationship()

    def __init__(self, initial=()):
        self.__state = ImmutableSet(initial)

    def __len__(self):
        return len(self._state)

    def __contains__(self, value):
        return value in self._state

    def __iter__(self):
        for value in self._state:
            yield value

    def _hash(self):
        return hash(self._state)

    def _eq(self, other):
        if self is other:
            return True
        elif isinstance(other, MySetContainer):
            return self.__state == other.__state
        else:
            return False

    def get(self, location, fallback=None):
        raise NotImplementedError()

    @classmethod
    def deserialize(cls, serialized, **kwargs):
        raise NotImplementedError()

    def serialize(self, **kwargs):
        raise NotImplementedError()

    @property
    def _state(self):
        # type: () -> ImmutableSet
        return self.__state


def test_set_container():
    my_set_container = MySetContainer(["a", "b"])
    assert hash(my_set_container) == hash(my_set_container._state)
    assert my_set_container == MySetContainer(["a", "b"])


def test_inheritance():
    assert issubclass(SetContainer, BaseAuxiliaryContainer)
    assert issubclass(SetContainer, SlottedSet)

    assert issubclass(SemiInteractiveSetContainer, SetContainer)
    assert issubclass(
        SemiInteractiveSetContainer, BaseSemiInteractiveAuxiliaryContainer
    )
    assert issubclass(InteractiveSetContainer, SemiInteractiveSetContainer)
    assert issubclass(InteractiveSetContainer, BaseInteractiveAuxiliaryContainer)
    assert issubclass(MutableSetContainer, InteractiveSetContainer)
    assert issubclass(MutableSetContainer, BaseMutableAuxiliaryContainer)
    assert issubclass(MutableSetContainer, SlottedMutableSet)


if __name__ == "__main__":
    pytest.main()
