# -*- coding: utf-8 -*-

from pytest import main

from objetto.utils.unique_iterator import unique_iterator


def test_unique_iterator():
    assert list(unique_iterator(["a", "b", "c", "c", "b", "d", "a", "c", "d"])) == [
        "a", "b", "c", "d"
    ]


if __name__ == "__main__":
    main()
