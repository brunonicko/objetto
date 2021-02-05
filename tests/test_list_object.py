# -*- coding: utf-8 -*-

import pytest

from objetto import Application, list_cls


def test_list_object():
    app = Application()

    list_obj = list_cls()(app)
    list_obj.extend(range(10))
    list_obj[2:5] = ["a", "b", "c"]

    assert list_obj._state == [0, 1, "a", "b", "c", 5, 6, 7, 8, 9]


if __name__ == "__main__":
    pytest.main()
