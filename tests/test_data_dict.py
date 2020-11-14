# -*- coding: utf-8 -*-

import pytest
import copy

from six import string_types, integer_types

from objetto._data.bases import DataRelationship
from objetto._data.dict import DictData, InteractiveDictData


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


class MyDictData(DictData):
    _relationship = DataRelationship(
        (HashCollider, str, int, list), factory=_my_factory
    )


class MyInteractiveDictData(MyDictData, InteractiveDictData):
    pass


def test_dict_data():

    # Hash.
    immutable_dict = MyDictData({"a": 1, "b": 2, "c": 3})
    hash(immutable_dict)

    unhashable_immutable_dict = MyDictData({"a": [1], "b": [2], "c": [3]})
    with pytest.raises(TypeError):
        hash(unhashable_immutable_dict)

    immutable_dict_b = DictData({"a": 1, "b": 2, "c": 3})
    assert hash(immutable_dict) == hash(immutable_dict_b)

    immutable_dict_c = MyInteractiveDictData({"a": 1, "b": 2, "c": 3})
    assert hash(immutable_dict) == hash(immutable_dict_c)

    # Equality.
    assert hash(immutable_dict) == hash(MyDictData({"a": 1, "b": 2, "c": 3}))
    assert immutable_dict == MyDictData({"a": 1, "b": 2, "c": 3})

    assert hash(immutable_dict) != hash(MyDictData({"x": 1, "y": 2}))
    assert immutable_dict != MyDictData({"x": 1, "y": 2})

    assert hash(MyDictData({"a": HashCollider(), HashCollider(): "b"})) == hash(
        MyDictData({"a": HashCollider(), HashCollider(): "b"})
    )
    assert MyDictData({"a": HashCollider(), HashCollider(): "b"}) != MyDictData(
        {"a": HashCollider(), HashCollider(): "b"}
    )

    assert immutable_dict != immutable_dict_b
    assert immutable_dict != immutable_dict_c

    # Copy.
    assert copy.copy(immutable_dict) is immutable_dict
    assert immutable_dict.copy() is immutable_dict

    # Iterate.
    assert set(immutable_dict) == {"a", "b", "c"}
    assert set(immutable_dict.iteritems()) == {("a", 1), ("b", 2), ("c", 3)}
    assert set(immutable_dict.iterkeys()) == {"a", "b", "c"}
    assert set(immutable_dict.itervalues()) == {1, 2, 3}

    # Length.
    assert len(immutable_dict) == 3


def test_interactive_dict_data():
    immutable_dict = MyInteractiveDictData({"a": 1, "b": 2, "c": 3})

    # Transformations.
    assert immutable_dict.clear() == MyInteractiveDictData()
    assert immutable_dict.discard("a") == MyInteractiveDictData({"b": 2, "c": 3})
    assert immutable_dict.discard("z") == immutable_dict
    assert immutable_dict.remove("a") == MyInteractiveDictData({"b": 2, "c": 3})
    with pytest.raises(KeyError):
        immutable_dict.remove("z")
    assert immutable_dict.set("d", 4) == MyInteractiveDictData(
        {"a": 1, "b": 2, "c": 3, "d": 4}
    )
    assert immutable_dict.update({"a": 10, "b": 20, "x": 1}) == MyInteractiveDictData(
        {"a": 10, "b": 20, "c": 3, "x": 1}
    )


if __name__ == "__main__":
    pytest.main()
