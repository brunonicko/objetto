# -*- coding: utf-8 -*-

import pickle

import pytest

from objetto.utils.weak_reference import WeakReference


class Cls(object):
    pass


def test_empty_weak_reference():
    weak = WeakReference()
    assert weak() is None


def test_weak_reference():
    strong = Cls()
    strong_hash = hash(strong)
    weak_a = WeakReference(strong)
    weak_b = WeakReference(strong)
    assert weak_a() is strong
    assert weak_b() is strong
    assert hash(weak_a) == strong_hash
    assert hash(weak_b) == strong_hash
    assert weak_a == weak_b
    del strong
    assert weak_a() is None
    assert weak_b() is None
    assert hash(weak_a) == strong_hash
    assert hash(weak_b) == strong_hash
    assert weak_a == weak_b


def test_pickling():
    strong = Cls()
    weak = WeakReference(strong)
    unpickled_strong, unpickled_weak = pickle.loads(pickle.dumps((strong, weak)))
    assert isinstance(unpickled_strong, Cls)
    assert isinstance(unpickled_weak, WeakReference)
    assert unpickled_weak() is unpickled_strong
    assert type(pickle.loads(pickle.dumps(weak()))) is Cls


if __name__ == "__main__":
    pytest.main()
