# -*- coding: utf-8 -*-

import copy

import pytest
from six import integer_types, string_types

from objetto._data.bases import DataRelationship
from objetto._data.data import Data, DataAttribute, InteractiveData


class HashCollider(object):
    def __hash__(self):
        return 1

    def __eq__(self, other):
        return self is other


def _my_factory(value):
    if isinstance(value, (HashCollider, string_types, integer_types, list)):
        return value
    else:
        try:
            return int(value)
        except ValueError:
            return str(value)


class MyData(Data):
    a = DataAttribute(
        relationship=DataRelationship(
            (HashCollider, str, int, list), factory=_my_factory
        ),
        required=False,
    )
    b = DataAttribute()
    c = DataAttribute()


class MyInteractiveData(MyData, InteractiveData):
    d = DataAttribute(required=False)


class OtherData(Data):
    a = DataAttribute()
    b = DataAttribute()
    c = DataAttribute()


def test_data():

    # Hash.
    immutable_dict = MyData(a=1, b=2, c=3)
    hash(immutable_dict)

    unhashable_immutable_dict = MyData(a=[1], b=[2], c=[3])
    with pytest.raises(TypeError):
        hash(unhashable_immutable_dict)

    immutable_dict_b = OtherData(a=1, b=2, c=3)
    assert hash(immutable_dict) == hash(immutable_dict_b)

    immutable_dict_c = MyInteractiveData(a=1, b=2, c=3)
    assert hash(immutable_dict) == hash(immutable_dict_c)

    # Equality.
    assert hash(immutable_dict) == hash(MyData(a=1, b=2, c=3))
    assert immutable_dict == MyData(a=1, b=2, c=3)

    assert hash(immutable_dict) != hash(MyData(a=10, b=20, c=30))
    assert immutable_dict != MyData(a=10, b=20, c=30)

    assert hash(MyData(a=HashCollider(), b=HashCollider(), c=HashCollider())) == hash(
        MyData(a=HashCollider(), b=HashCollider(), c=HashCollider())
    )

    assert immutable_dict != immutable_dict_b
    assert immutable_dict != immutable_dict_c

    # Copy.
    assert copy.copy(immutable_dict) is immutable_dict

    # Iterate.
    assert set(immutable_dict) == {("a", 1), ("b", 2), ("c", 3)}

    # Length.
    assert len(immutable_dict) == 3


def test_interactive_dict_data():
    immutable_dict = MyInteractiveData(a=1, b=2, c=3)

    # Transformations.
    assert immutable_dict.delete("a") == MyInteractiveData(b=2, c=3)
    assert immutable_dict.delete("a") == MyInteractiveData(b=2, c=3)
    with pytest.raises(KeyError):
        immutable_dict.delete("z")
    assert immutable_dict.set("d", 4) == MyInteractiveData(a=1, b=2, c=3, d=4)
    assert immutable_dict.update({"a": 10, "b": 20, "d": 1}) == MyInteractiveData(
        a=10, b=20, c=3, d=1
    )


if __name__ == "__main__":
    pytest.main()
