# -*- coding: utf-8 -*-

from itertools import chain
from math import floor

import pytest

from objetto.utils.lazy_import import decorate_path, get_path, import_path


class MyClass(object):
    class MyNestedClass(object):
        pass


def test_import_path():
    assert import_path("math|floor") is floor
    assert import_path("itertools|chain") is chain
    assert import_path(__name__ + "|MyClass") is MyClass
    assert import_path(__name__ + "|MyClass.MyNestedClass") is MyClass.MyNestedClass

    with pytest.raises(ValueError):
        import_path("module.submodule|<locals>.Test")


def test_get_path():
    assert get_path(floor) == "math|floor"
    assert get_path(chain) == "itertools|chain"
    assert get_path(MyClass) == __name__ + "|MyClass"
    assert get_path(MyClass.MyNestedClass) == __name__ + "|MyClass.MyNestedClass"

    class LocalClass(object):
        pass

    with pytest.raises(ValueError):
        get_path(LocalClass)


def test_decorate_path():
    assert decorate_path("abstractmethod", "abc") == "abc|abstractmethod"
    assert decorate_path(".|abstractmethod", "abc") == "abc|abstractmethod"
    assert decorate_path("abc|abstractmethod", "") == "abc|abstractmethod"
    assert decorate_path(".abc|Mapping", "collections") == "collections.abc|Mapping"

    with pytest.raises(ValueError):
        decorate_path("abstract method|a b c", "xyz")

    with pytest.raises(ValueError):
        decorate_path("abstract method", "abc")

    with pytest.raises(ValueError):
        decorate_path("abstractmethod", "a b c")

    assert decorate_path("..|Counter", "collections.abc") == "collections|Counter"
    assert decorate_path("..._objects.base|BaseObject", "objetto.changes.base") == (
        "objetto._objects.base|BaseObject"
    )


if __name__ == "__main__":
    pytest.main()
