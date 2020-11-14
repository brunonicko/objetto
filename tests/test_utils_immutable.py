# -*- coding: utf-8 -*-

import pytest
import copy

from six.moves import collections_abc

from objetto.utils.immutable import (
    Immutable,
    ImmutableDict,
    ImmutableList,
    ImmutableSet,
)


class HashCollider(object):
    def __hash__(self):
        return 1

    def __eq__(self, other):
        return self is other


def test_immutable_container():
    assert issubclass(Immutable, collections_abc.Container)

    # Can't instantiate abstract class.
    with pytest.raises(TypeError):
        Immutable()


def test_immutable_dict():
    assert issubclass(ImmutableDict, Immutable)
    assert issubclass(ImmutableDict, collections_abc.Mapping)

    # Hash.
    immutable_dict = ImmutableDict({"a": 1, "b": 2, "c": 3})
    hash(immutable_dict)

    unhashable_immutable_dict = ImmutableDict({"a": [1], "b": [2], "c": [3]})
    with pytest.raises(TypeError):
        hash(unhashable_immutable_dict)

    # Equality.
    assert hash(immutable_dict) == hash(ImmutableDict({"a": 1, "b": 2, "c": 3}))
    assert immutable_dict == ImmutableDict({"a": 1, "b": 2, "c": 3})

    assert hash(immutable_dict) != hash(ImmutableDict({"x": 1, "y": 2}))
    assert immutable_dict != ImmutableDict({"x": 1, "y": 2})

    assert hash(ImmutableDict({"a": HashCollider(), HashCollider(): "b"})) == hash(
        ImmutableDict({"a": HashCollider(), HashCollider(): "b"})
    )
    assert ImmutableDict({"a": HashCollider(), HashCollider(): "b"}) != ImmutableDict(
        {"a": HashCollider(), HashCollider(): "b"}
    )

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

    # Transformations.
    assert immutable_dict.clear() == ImmutableDict()
    assert immutable_dict.discard("a") == ImmutableDict({"b": 2, "c": 3})
    assert immutable_dict.discard("z") == immutable_dict
    assert immutable_dict.remove("a") == ImmutableDict({"b": 2, "c": 3})
    with pytest.raises(KeyError):
        immutable_dict.remove("z")
    assert immutable_dict.set("d", 4) == ImmutableDict({"a": 1, "b": 2, "c": 3, "d": 4})
    assert immutable_dict.update({"a": 10, "b": 20, "x": 1}) == ImmutableDict(
        {"a": 10, "b": 20, "c": 3, "x": 1}
    )


def test_immutable_list():
    assert issubclass(ImmutableList, Immutable)
    assert issubclass(ImmutableList, collections_abc.Sequence)

    # Hash.
    immutable_list = ImmutableList(["a", "b", "c", "c"])
    hash(immutable_list)

    unhashable_immutable_list = ImmutableList([["a"], ["b"], ["c"], ["c"]])
    with pytest.raises(TypeError):
        hash(unhashable_immutable_list)

    # Equality.
    assert hash(immutable_list) == hash(ImmutableList(["a", "b", "c", "c"]))
    assert immutable_list == ImmutableList(["a", "b", "c", "c"])

    assert hash(immutable_list) != hash(ImmutableList(["x", "y"]))
    assert immutable_list != ImmutableList(["x", "y"])

    assert hash(ImmutableList([HashCollider(), HashCollider()])) == hash(
        ImmutableList([HashCollider(), HashCollider()])
    )
    assert ImmutableList([HashCollider(), HashCollider()]) != ImmutableList(
        [HashCollider(), HashCollider()]
    )

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

    # Transformations.
    assert immutable_list.clear() == ImmutableList()
    assert immutable_list.change(1, "x", "y") == ImmutableList(["a", "x", "y", "c"])
    with pytest.raises(IndexError):
        immutable_list.change(2, "x", "y", "z")
    assert immutable_list.append("d") == ImmutableList(["a", "b", "c", "c", "d"])
    assert immutable_list.extend(["d", "e"]) == ImmutableList(
        ["a", "b", "c", "c", "d", "e"]
    )
    assert immutable_list.insert(2, "x", "y") == ImmutableList(
        ["a", "b", "x", "y", "c", "c"]
    )
    assert immutable_list.remove("a") == ImmutableList(["b", "c", "c"])
    with pytest.raises(ValueError):
        immutable_list.remove("x")
    assert immutable_list.reverse() == ImmutableList(["c", "c", "b", "a"])
    assert immutable_list.move(3, 0) == ImmutableList(["c", "a", "b", "c"])
    assert immutable_list.move(1, 3) == ImmutableList(["a", "c", "c", "b"])
    assert immutable_list.move(slice(1, 3), 0) == ImmutableList(["b", "c", "a", "c"])
    assert immutable_list.move(slice(1, 3), 4) == ImmutableList(["a", "c", "b", "c"])
    assert ImmutableList(["2", "1", "3"]).sort(
        key=lambda v: -int(v), reverse=True
    ) == ImmutableList(["1", "2", "3"])


def test_immutable_set():
    assert issubclass(ImmutableSet, Immutable)
    assert issubclass(ImmutableSet, collections_abc.Set)

    # Hash.
    immutable_set = ImmutableSet([1, 2, 3, 3])
    hash(immutable_set)

    with pytest.raises(TypeError):
        ImmutableSet([[1], [2], [3], [3]])

    # Equality.
    assert hash(immutable_set) == hash(ImmutableSet([1, 2, 3, 3]))
    assert immutable_set == ImmutableSet([1, 2, 3, 3])

    assert hash(immutable_set) != hash(ImmutableSet([8, 9]))
    assert immutable_set != ImmutableSet([8, 9])

    assert hash(ImmutableSet([HashCollider(), HashCollider()])) == hash(
        ImmutableSet([HashCollider(), HashCollider()])
    )
    assert ImmutableSet([HashCollider(), HashCollider()]) != ImmutableSet(
        [HashCollider(), HashCollider()]
    )

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

    # Transformations.
    assert immutable_set.add(4) == ImmutableSet([1, 2, 3, 4])
    assert immutable_set.clear() == ImmutableSet()
    assert immutable_set.difference({2, 3}) == ImmutableSet({1})
    assert immutable_set.discard(2) == ImmutableSet({1, 3})
    assert immutable_set.discard(4) == ImmutableSet({1, 2, 3})
    assert immutable_set.remove(2) == ImmutableSet({1, 3})
    with pytest.raises(KeyError):
        immutable_set.remove(4)
    assert immutable_set.replace(1, 10) == ImmutableSet({10, 2, 3})
    assert immutable_set.intersection({2, 3, 4}) == ImmutableSet({2, 3})
    assert immutable_set.symmetric_difference({3, 4, 5}) == ImmutableSet({1, 2, 4, 5})
    assert immutable_set.union({4, 5}) == ImmutableSet({1, 2, 3, 4, 5})
    assert immutable_set.update({4, 5}) == ImmutableSet({1, 2, 3, 4, 5})


if __name__ == "__main__":
    pytest.main()
