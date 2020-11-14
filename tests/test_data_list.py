# -*- coding: utf-8 -*-

import pytest
import copy

from six import string_types, integer_types

from objetto._data.bases import DataRelationship
from objetto._data.list import ListData, InteractiveListData
from objetto.utils.immutable import ImmutableList


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


class MyListData(ListData):
    _relationship = DataRelationship(
        (HashCollider, str, int, list), factory=_my_factory
    )


class MyInteractiveListData(MyListData, InteractiveListData):
    pass


def test_immutable_list():

    # Hash.
    immutable_list = MyListData(["a", "b", "c", "c"])
    hash(immutable_list)

    unhashable_immutable_list = MyListData([["a"], ["b"], ["c"], ["c"]])
    with pytest.raises(TypeError):
        hash(unhashable_immutable_list)

    immutable_list_b = ListData(["a", "b", "c", "c"])
    assert hash(immutable_list) == hash(immutable_list_b)

    immutable_list_c = MyInteractiveListData(["a", "b", "c", "c"])
    assert hash(immutable_list) == hash(immutable_list_c)

    # Equality.
    assert hash(immutable_list) == hash(MyListData(["a", "b", "c", "c"]))
    assert immutable_list == MyListData(["a", "b", "c", "c"])

    assert hash(immutable_list) != hash(MyListData(["x", "y"]))
    assert immutable_list != MyListData(["x", "y"])

    assert hash(MyListData([HashCollider(), HashCollider()])) == hash(
        MyListData([HashCollider(), HashCollider()])
    )
    assert MyListData([HashCollider(), HashCollider()]) != MyListData(
        [HashCollider(), HashCollider()]
    )

    assert immutable_list != immutable_list_b
    assert immutable_list != immutable_list_c

    # Copy.
    assert copy.copy(immutable_list) is immutable_list
    assert immutable_list.copy() is immutable_list

    # Get item.
    assert immutable_list[1] == "b"
    assert immutable_list[1:3] == ImmutableList(["b", "c"])

    # Length.
    assert len(immutable_list) == 4

    # Index/slice resolving.
    for i in range(-4, 4):
        assert immutable_list[immutable_list.resolve_index(i)] == immutable_list[i]

    with pytest.raises(IndexError):
        immutable_list.resolve_index(5)

    with pytest.raises(IndexError):
        immutable_list.resolve_index(-5)

    assert immutable_list.resolve_index(5, clamp=True) == 4
    assert immutable_list.resolve_index(-5, clamp=True) == 0

    assert immutable_list.resolve_continuous_slice(slice(0, 4)) == (0, 4)
    assert immutable_list.resolve_continuous_slice(slice(-5, 5)) == (0, 4)

    with pytest.raises(IndexError):
        immutable_list.resolve_continuous_slice(slice(0, 4, 2))


def test_interactive_list_data():
    immutable_list = MyInteractiveListData(["a", "b", "c", "c"])

    # Transformations.
    assert immutable_list.clear() == MyInteractiveListData()
    assert immutable_list.change(1, "x", "y") == MyInteractiveListData(
        ["a", "x", "y", "c"]
    )
    with pytest.raises(IndexError):
        immutable_list.change(2, "x", "y", "z")
    assert immutable_list.append("d") == MyInteractiveListData(
        ["a", "b", "c", "c", "d"]
    )
    assert immutable_list.extend(["d", "e"]) == MyInteractiveListData(
        ["a", "b", "c", "c", "d", "e"]
    )
    assert immutable_list.insert(2, "x", "y") == MyInteractiveListData(
        ["a", "b", "x", "y", "c", "c"]
    )
    assert immutable_list.remove("a") == MyInteractiveListData(["b", "c", "c"])
    with pytest.raises(ValueError):
        immutable_list.remove("x")
    assert immutable_list.reverse() == MyInteractiveListData(["c", "c", "b", "a"])
    assert immutable_list.move(3, 0) == MyInteractiveListData(["c", "a", "b", "c"])
    assert immutable_list.move(1, 3) == MyInteractiveListData(["a", "c", "c", "b"])
    assert immutable_list.move(slice(1, 3), 0) == MyInteractiveListData(
        ["b", "c", "a", "c"]
    )
    assert immutable_list.move(slice(1, 3), 4) == MyInteractiveListData(
        ["a", "c", "b", "c"]
    )
    assert MyInteractiveListData(["2", "1", "3"]).sort(
        key=lambda v: -int(v), reverse=True
    ) == MyInteractiveListData(["1", "2", "3"])


if __name__ == "__main__":
    pytest.main()
