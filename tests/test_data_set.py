# -*- coding: utf-8 -*-

import pytest
import copy

from six import string_types, integer_types

from objetto._data.bases import DataRelationship
from objetto._data.set import SetData, InteractiveSetData
from objetto.utils.immutable import ImmutableSet


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


class MySetData(SetData):
    _relationship = DataRelationship(
        (HashCollider, str, int, list), factory=_my_factory
    )


class MyInteractiveSetData(MySetData, InteractiveSetData):
    pass


def test_immutable_set():

    # Hash.
    immutable_set = MySetData([1, 2, 3, 3])
    hash(immutable_set)

    with pytest.raises(TypeError):
        MySetData([[1], [2], [3], [3]])

    immutable_set_b = SetData([1, 2, 3, 3])
    assert hash(immutable_set) == hash(immutable_set_b)

    immutable_set_c = MyInteractiveSetData([1, 2, 3, 3])
    assert hash(immutable_set) == hash(immutable_set_c)

    # Equality.
    assert hash(immutable_set) == hash(MySetData([1, 2, 3, 3]))
    assert immutable_set == MySetData([1, 2, 3, 3])

    assert hash(immutable_set) != hash(MySetData([8, 9]))
    assert immutable_set != MySetData([8, 9])

    assert hash(MySetData([HashCollider(), HashCollider()])) == hash(
        MySetData([HashCollider(), HashCollider()])
    )
    assert MySetData([HashCollider(), HashCollider()]) != MySetData(
        [HashCollider(), HashCollider()]
    )

    assert immutable_set != immutable_set_b
    assert immutable_set != immutable_set_c

    # Copy.
    assert copy.copy(immutable_set) is immutable_set
    assert immutable_set.copy() is immutable_set

    # Contains.
    assert 3 in immutable_set

    # Length.
    assert len(immutable_set) == 3

    # Iterate.
    assert set(immutable_set) == {1, 2, 3}

    # Checks.
    assert immutable_set.issubset({0, 1, 2, 3, 4})
    assert not immutable_set.issubset({2, 3})
    assert immutable_set.issuperset({2, 3})
    assert not immutable_set.issuperset({0, 1, 2, 3, 4})

    # Operations.
    assert immutable_set.difference({2, 3}) == ImmutableSet({1})
    assert immutable_set.intersection({2, 3, 4}) == ImmutableSet({2, 3})
    assert immutable_set.symmetric_difference({3, 4, 5}) == ImmutableSet({1, 2, 4, 5})
    assert immutable_set.union({4, 5}) == ImmutableSet({1, 2, 3, 4, 5})


def test_interactive_set_data():
    immutable_set = MyInteractiveSetData([1, 2, 3, 3])

    # Transformations.
    assert immutable_set.add(4) == MyInteractiveSetData([1, 2, 3, 4])
    assert immutable_set.clear() == MyInteractiveSetData()
    assert immutable_set.discard(2) == MyInteractiveSetData({1, 3})
    assert immutable_set.discard(4) == MyInteractiveSetData({1, 2, 3})
    assert immutable_set.remove(2) == MyInteractiveSetData({1, 3})
    with pytest.raises(KeyError):
        immutable_set.remove(4)
    assert immutable_set.replace(1, 10) == MyInteractiveSetData({10, 2, 3})
    assert immutable_set.update({4, 5}) == MyInteractiveSetData({1, 2, 3, 4, 5})


if __name__ == "__main__":
    pytest.main()
