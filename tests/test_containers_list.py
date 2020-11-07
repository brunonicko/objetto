# -*- coding: utf-8 -*-

import pytest

from six import with_metaclass
from slotted import SlottedSequence, SlottedMutableSequence

from objetto._containers.bases import (
    BaseRelationship,
    BaseAuxiliaryContainer,
    BaseSemiInteractiveAuxiliaryContainer,
    BaseInteractiveAuxiliaryContainer,
    BaseMutableAuxiliaryContainer,
)
from objetto._containers.list import (
    ListContainerMeta,
    ListContainer,
    SemiInteractiveListContainer,
    InteractiveListContainer,
    MutableListContainer,
)
from objetto.utils.immutable import ImmutableList


class MyListContainerMeta(ListContainerMeta):

    @property
    def _serializable_container_types(cls):
        return (MyListContainer,)

    @property
    def _relationship_type(cls):
        return BaseRelationship


class MyListContainer(with_metaclass(MyListContainerMeta, ListContainer)):
    __slots__ = ("__state",)
    _relationship = BaseRelationship()

    def __init__(self, initial=()):
        self.__state = ImmutableList(initial)

    def __getitem__(self, item):
        return self._state[item]

    def __len__(self):
        return len(self._state)

    def _hash(self):
        return hash(self._state)

    def _eq(self, other):
        if self is other:
            return True
        elif isinstance(other, MyListContainer):
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
        # type: () -> ImmutableList
        return self.__state


def test_list_container():
    my_list_container = MyListContainer(["a", "b"])
    assert hash(my_list_container) == hash(my_list_container._state)
    assert my_list_container == MyListContainer(["a", "b"])


def test_inheritance():
    assert issubclass(ListContainer, BaseAuxiliaryContainer)
    assert issubclass(ListContainer, SlottedSequence)

    assert issubclass(SemiInteractiveListContainer, ListContainer)
    assert issubclass(
        SemiInteractiveListContainer, BaseSemiInteractiveAuxiliaryContainer
    )
    assert issubclass(InteractiveListContainer, SemiInteractiveListContainer)
    assert issubclass(InteractiveListContainer, BaseInteractiveAuxiliaryContainer)
    assert issubclass(MutableListContainer, InteractiveListContainer)
    assert issubclass(MutableListContainer, BaseMutableAuxiliaryContainer)
    assert issubclass(MutableListContainer, SlottedMutableSequence)


if __name__ == "__main__":
    pytest.main()
