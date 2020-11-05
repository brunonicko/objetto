# -*- coding: utf-8 -*-

import pytest

from objetto.utils.factoring import (
    format_factory,
    get_factory_name,
    import_factory,
    run_factory,
)


def test_format_factory():
    assert format_factory(None) is None
    assert format_factory("Class.method", module="module.submodule") == (
        "module.submodule|Class.method"
    )
    assert format_factory("function", module="module.submodule") == (
        "module.submodule|function"
    )
    assert format_factory("module.submodule|Class.method", module="") == (
        "module.submodule|Class.method"
    )
    assert format_factory("module.submodule|function", module="") == (
        "module.submodule|function"
    )
    assert format_factory(int) is int
    with pytest.raises(TypeError):
        params = (3,)
        format_factory(*params)


def test_get_factory_name():
    assert get_factory_name("Class.method") == "method"
    assert get_factory_name("function") == "function"
    assert get_factory_name("module.submodule|Class.method") == "method"
    assert get_factory_name("module.submodule|function") == "function"
    assert get_factory_name(None) == "None"
    assert get_factory_name(int) == "int"
    assert get_factory_name(float) == "float"


def test_import_factory():
    from abc import abstractmethod
    from re import match

    assert import_factory("abc|abstractmethod") is abstractmethod
    assert import_factory(None) is None
    assert import_factory(match) is match


def test_run_factory():
    def my_factory(*args, **kwargs):
        assert args == (1, 2, 3)
        assert kwargs == {"a": 1, "b": 2, "c": 3}

    assert bool(run_factory("re|match", (r"^[a-z]+$", "abc"))) is True
    run_factory(my_factory, (1, 2, 3), dict(a=1, b=2, c=3))


if __name__ == "__main__":
    pytest.main()
