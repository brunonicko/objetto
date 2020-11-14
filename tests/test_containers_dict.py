# -*- coding: utf-8 -*-

import pytest
from six import with_metaclass
from slotted import SlottedMapping, SlottedMutableMapping

from objetto._containers.bases import (
    BaseAuxiliaryContainer,
    BaseInteractiveAuxiliaryContainer,
    BaseMutableAuxiliaryContainer,
    BaseRelationship,
    BaseSemiInteractiveAuxiliaryContainer,
)
from objetto._containers.dict import (
    DictContainer,
    DictContainerMeta,
    InteractiveDictContainer,
    KeyRelationship,
    MutableDictContainer,
    SemiInteractiveDictContainer,
)
from objetto.utils.immutable import ImmutableDict


class MyDictContainerMeta(DictContainerMeta):
    @property
    def _serializable_container_types(cls):
        return (MyDictContainer,)

    @property
    def _relationship_type(cls):
        return BaseRelationship


class MyDictContainer(with_metaclass(MyDictContainerMeta, DictContainer)):
    __slots__ = ("__state",)
    _relationship = BaseRelationship()
    _key_relationship = KeyRelationship()

    def __init__(self, initial=()):
        self.__state = ImmutableDict(initial)

    def __getitem__(self, key):
        return self._state[key]

    def __len__(self):
        return len(self._state)

    def __iter__(self):
        for key in self._state:
            yield key

    def _hash(self):
        return hash(self._state)

    def _eq(self, other):
        if self is other:
            return True
        elif isinstance(other, MyDictContainer):
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
        # type: () -> ImmutableDict
        return self.__state


class SimpleDictContainer(MyDictContainer):
    _key_relationship = KeyRelationship(types=(int, str))


def test_key_relationship():
    relationship = BaseRelationship()
    assert relationship.passthrough is True

    relationship = BaseRelationship(factory=int)
    assert relationship.passthrough is False

    relationship = BaseRelationship(types=int, checked=False)
    assert relationship.types == (int,)
    assert relationship.passthrough is True

    relationship = BaseRelationship(types=int, checked=False, factory=int)
    assert relationship.types == (int,)
    assert relationship.factory == int
    assert relationship.passthrough is False

    relationship = BaseRelationship(types=int, factory=int)
    assert relationship.types == (int,)
    assert relationship.factory == int
    assert relationship.passthrough is False


def test_dict_container():

    with pytest.raises(TypeError):

        class MyBadDictContainer(DictContainer):
            _key_relationship = 1

        raise AssertionError(MyBadDictContainer)

    my_dict_container = MyDictContainer({"a": 1, 2: "b"})
    assert hash(my_dict_container) == hash(my_dict_container._state)
    assert my_dict_container == MyDictContainer({"a": 1, 2: "b"})


def test_inheritance():
    assert issubclass(DictContainer, BaseAuxiliaryContainer)
    assert issubclass(DictContainer, SlottedMapping)

    assert issubclass(SemiInteractiveDictContainer, DictContainer)
    assert issubclass(
        SemiInteractiveDictContainer, BaseSemiInteractiveAuxiliaryContainer
    )
    assert issubclass(InteractiveDictContainer, SemiInteractiveDictContainer)
    assert issubclass(InteractiveDictContainer, BaseInteractiveAuxiliaryContainer)
    assert issubclass(MutableDictContainer, InteractiveDictContainer)
    assert issubclass(MutableDictContainer, BaseMutableAuxiliaryContainer)
    assert issubclass(MutableDictContainer, SlottedMutableMapping)


if __name__ == "__main__":
    pytest.main()
