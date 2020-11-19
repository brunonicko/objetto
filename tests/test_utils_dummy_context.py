# -*- coding: utf-8 -*-

import pytest

from objetto.utils.reraise_context import ReraiseContext


def test_dummy_context():
    def func_a():
        func_b()

    def func_b():
        func_c()

    def func_c():
        raise ValueError("something is wrong")

    with pytest.raises(ValueError, match="oops; something is wrong"):
        with ReraiseContext(ValueError, "oops"):
            func_a()


if __name__ == "__main__":
    pytest.main()
