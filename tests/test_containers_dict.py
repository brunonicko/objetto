# -*- coding: utf-8 -*-

import pytest

from six import with_metaclass

from objetto._containers.bases import BaseRelationship
from objetto._containers.dict import (
    KeyRelationship,
    DictContainer,
    MutableDictContainer,
)
from objetto.utils.immutable import ImmutableDict


class MyDictContainer(DictContainer):
    __slots__ = ("__state",)
    _relationship = BaseRelationship()
    _key_relationship = KeyRelationship()

    def __init__(self, **kwargs):
        self.__state = ImmutableDict(kwargs)

    def __getitem__(self, key):
        return self._state[key]

    def __len__(self):
        return len(self._state)

    def __iter__(self):
        for key in self._state:
            yield key

    @classmethod
    def deserialize(cls, serialized, **kwargs):
        return cls(
            **dict((k, cls.deserialize_value(v)) for k, v in serialized.items())
        )

    def serialize(self, **kwargs):
        return dict((k, self.serialize_value(v)) for k, v in self._state.items())

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

    relationship = BaseRelationship(types=int, type_checked=False)
    assert relationship.types == (int,)
    assert relationship.passthrough is True

    relationship = BaseRelationship(types=int, type_checked=False, factory=int)
    assert relationship.types == (int,)
    assert relationship.factory == int
    assert relationship.passthrough is False

    relationship = BaseRelationship(types=int, factory=int)
    assert relationship.types == (int,)
    assert relationship.factory == int
    assert relationship.passthrough is False

    assert BaseRelationship(SimpleContainer).get_single_exact_type(
        (SimpleContainer,)
    ) is SimpleContainer
    assert BaseRelationship((SimpleContainer, int)).get_single_exact_type(
        (SimpleContainer,)
    ) is SimpleContainer
    assert BaseRelationship(SimpleContainer, subtypes=True).get_single_exact_type(
        (SimpleContainer,)
    ) is None


def test_dict_container():

    with pytest.raises(TypeError):
        class MyBadDictContainer(DictContainer):
            _key_relationship = 1

        raise AssertionError(MyBadDictContainer)


if __name__ == "__main__":
    pytest.main()
