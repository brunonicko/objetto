# -*- coding: utf-8 -*-

import pytest

from objetto.utils.caller_module import get_caller_module


def test_get_caller_module():
    def func():
        return get_caller_module()

    assert func() == __name__


if __name__ == "__main__":
    pytest.main()
