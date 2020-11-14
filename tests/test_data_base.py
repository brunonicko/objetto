# -*- coding: utf-8 -*-

from typing import cast

import pytest
from six import with_metaclass

from objetto._containers.bases import (
    BaseAuxiliaryContainerMeta,
    BaseContainerMeta,
    BaseInteractiveAuxiliaryContainer,
    BaseInteractiveContainer,
    BaseRelationship,
    BaseSemiInteractiveAuxiliaryContainer,
    BaseSemiInteractiveContainer,
)
from objetto._data.bases import (
    BaseAuxiliaryData,
    BaseAuxiliaryDataMeta,
    BaseData,
    BaseDataMeta,
    BaseInteractiveAuxiliaryData,
    BaseInteractiveData,
    DataRelationship,
)
from objetto.utils.immutable import ImmutableDict


class MyBaseData(BaseData):

    __slots__ = ()
    _relationship = DataRelationship()

    def __init__(self, initial=()):
        self._init_state(ImmutableDict(initial))

    def __len__(self):
        return len(self._state)

    def __contains__(self, value):
        return value in self._state

    def __iter__(self):
        for value in self._state:
            yield value

    @classmethod
    def _get_relationship(cls, location):
        return cls._relationship

    def _hash(self):
        return hash(self._state)

    def _eq(self, other):
        if self is other:
            return True
        if type(self) is not type(other):
            return False
        if self._state == other._state:
            return True
        return False

    def _set(self, location, value):
        return self.__make__(self._state.set(location, value))

    def get(self, location, fallback=None):
        return self._state[location]

    @classmethod
    def deserialize(cls, serialized, **kwargs):
        return cls(serialized)

    def serialize(self, **kwargs):
        return dict(self._state)

    @property
    def _state(self):
        # type: () -> ImmutableDict
        return cast("ImmutableDict", super(MyBaseData, self)._state)


class MyInteractiveBaseData(MyBaseData, BaseInteractiveData):
    def set(self, location, value):
        return self._set(location, value)


class MyAuxiliaryBaseDataMeta(BaseAuxiliaryDataMeta):
    @property
    def _base_auxiliary_type(cls):
        return _MyAuxiliaryBaseData


class _MyAuxiliaryBaseData(with_metaclass(MyAuxiliaryBaseDataMeta, BaseAuxiliaryData)):
    __slots__ = ()
    _relationship = DataRelationship()

    def __init__(self, initial=()):
        self._init_state(ImmutableDict(initial))

    def __len__(self):
        return len(self._state)

    def __contains__(self, value):
        return value in self._state

    def __iter__(self):
        for value in self._state:
            yield value

    def _set(self, location, value):
        return self.__make__(self._state.set(location, value))

    def get(self, location, fallback=None):
        return self._state[location]

    @classmethod
    def deserialize(cls, serialized, **kwargs):
        return cls(serialized)

    def serialize(self, **kwargs):
        return dict(self._state)

    @property
    def _state(self):
        # type: () -> ImmutableDict
        return cast("ImmutableDict", super(_MyAuxiliaryBaseData, self)._state)


class MyAuxiliaryBaseData(
    with_metaclass(MyAuxiliaryBaseDataMeta, _MyAuxiliaryBaseData)
):
    _relationship = DataRelationship(str, serialized=False)


class MyOtherAuxiliaryBaseData(MyAuxiliaryBaseData):
    _relationship = DataRelationship(str, serialized=False)


class MyDifferentAuxiliaryBaseData(MyOtherAuxiliaryBaseData):
    _relationship = DataRelationship(int, represented=False)


def test_make():
    assert MyBaseData({"a": 1}) == MyBaseData.__make__(ImmutableDict({"a": 1}))


def test_transform():
    my_interactive_base_data = MyInteractiveBaseData(
        {
            "a": 1,
            "b": MyInteractiveBaseData(
                {
                    "c": 2,
                    "d": MyInteractiveBaseData({"e": 3}),
                    "f": MyBaseData({"g": 1}),
                }
            ),
        }
    )
    assert my_interactive_base_data.transform(
        ("b", "d"), "set", ("e", 30)
    ) == MyInteractiveBaseData(
        {
            "a": 1,
            "b": MyInteractiveBaseData(
                {
                    "c": 2,
                    "d": MyInteractiveBaseData({"e": 30}),
                    "f": MyBaseData({"g": 1}),
                }
            ),
        }
    )
    assert my_interactive_base_data.transform(
        ("b", "d"), lambda v: v.set("e", v.get("e") * 2)
    ) == MyInteractiveBaseData(
        {
            "a": 1,
            "b": MyInteractiveBaseData(
                {
                    "c": 2,
                    "d": MyInteractiveBaseData({"e": 6}),
                    "f": MyBaseData({"g": 1}),
                }
            ),
        }
    )

    with pytest.raises(TypeError):
        my_interactive_base_data.transform(("b", "f"), "set", ("g", 10))


def test_data_relationship():
    assert hash(DataRelationship()) == hash(DataRelationship())
    assert DataRelationship() == DataRelationship()
    assert DataRelationship((str, int)) == DataRelationship((int, str))
    assert DataRelationship(int) != DataRelationship(str)
    assert set(
        m for m in DataRelationship.__members__ if not m.startswith("_")
    ).issuperset(DataRelationship().to_dict())


def test_auxiliary_eq():
    auxiliary_a = MyAuxiliaryBaseData()
    auxiliary_b = MyAuxiliaryBaseData()
    other_auxiliary_a = MyOtherAuxiliaryBaseData()
    other_auxiliary_b = MyOtherAuxiliaryBaseData()
    different_auxiliary_a = MyDifferentAuxiliaryBaseData()
    different_auxiliary_b = MyDifferentAuxiliaryBaseData()

    assert auxiliary_a == auxiliary_a
    assert auxiliary_b == auxiliary_b
    assert other_auxiliary_a == other_auxiliary_a
    assert other_auxiliary_b == other_auxiliary_b
    assert different_auxiliary_a == different_auxiliary_a
    assert different_auxiliary_b == different_auxiliary_b

    assert auxiliary_a == auxiliary_b
    assert other_auxiliary_a == other_auxiliary_b
    assert different_auxiliary_a == different_auxiliary_b

    assert auxiliary_a == other_auxiliary_a
    assert auxiliary_b == other_auxiliary_b
    assert different_auxiliary_a != auxiliary_a
    assert different_auxiliary_a != auxiliary_b
    assert different_auxiliary_a != other_auxiliary_a
    assert different_auxiliary_a != other_auxiliary_b


def test_inheritance():
    assert issubclass(DataRelationship, BaseRelationship)

    assert issubclass(BaseDataMeta, BaseContainerMeta)
    assert issubclass(BaseAuxiliaryDataMeta, BaseAuxiliaryContainerMeta)

    assert issubclass(BaseData, BaseSemiInteractiveContainer)
    assert isinstance(BaseData, BaseDataMeta)

    assert issubclass(BaseInteractiveData, BaseData)
    assert issubclass(BaseInteractiveData, BaseInteractiveContainer)

    assert issubclass(BaseAuxiliaryData, BaseData)
    assert issubclass(BaseAuxiliaryData, BaseSemiInteractiveAuxiliaryContainer)
    assert isinstance(BaseAuxiliaryData, BaseAuxiliaryDataMeta)

    assert issubclass(BaseInteractiveAuxiliaryData, BaseAuxiliaryData)
    assert issubclass(BaseInteractiveAuxiliaryData, BaseInteractiveAuxiliaryContainer)


if __name__ == "__main__":
    pytest.main()
