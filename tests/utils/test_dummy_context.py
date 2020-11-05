# -*- coding: utf-8 -*-

import pytest

from objetto.utils.dummy_context import DummyContext


def test_dummy_context():
    with DummyContext():
        pass


if __name__ == "__main__":
    pytest.main()
