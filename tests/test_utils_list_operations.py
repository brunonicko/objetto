# -*- coding: utf-8 -*-

import pytest

from objetto.utils.list_operations import (
    resolve_index,
    resolve_continuous_slice,
    pre_move,
)


def test_resolve_index():
    my_list = ["a", "b", "c", "c"]
    length = len(my_list)

    for i in range(-4, 4):
        assert my_list[resolve_index(length, i)] == my_list[i]

    with pytest.raises(IndexError):
        resolve_index(length, 5)

    with pytest.raises(IndexError):
        resolve_index(length, -5)

    assert resolve_index(length, 5, clamp=True) == 4
    assert resolve_index(length, -5, clamp=True) == 0


def test_resolve_continuous_slice():
    my_list = ["a", "b", "c", "c"]
    length = len(my_list)

    assert resolve_continuous_slice(length, slice(0, 4)) == (0, 4)
    assert resolve_continuous_slice(length, slice(-5, 5)) == (0, 4)

    with pytest.raises(IndexError):
        resolve_continuous_slice(length, slice(0, 4, 2))


def test_pre_move():
    my_list = ["a", "b", "c", "c"]
    length = len(my_list)

    assert pre_move(length, 1, 2) is None
    assert pre_move(length, 2, 3) is None
    assert pre_move(length, 3, 0) == (3, 4, 0, 0)
    assert pre_move(length, 1, 3) == (1, 2, 3, 3)
    assert pre_move(length, slice(1, 3), 0) == (1, 3, 0, 0)
    assert pre_move(length, slice(1, 3), 4) == (1, 3, 4, 3)


if __name__ == "__main__":
    pytest.main()
