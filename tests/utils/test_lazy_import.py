# -*- coding: utf-8 -*-

from pytest import main, raises, mark

from objetto.utils.lazy_import import format_import_path, lazy_import, get_import_path


def test_format_import_path():
    assert format_import_path("itertools|chain") == "itertools|chain"
    assert format_import_path("itertools.module|..chain") == "itertools|chain"
    assert format_import_path("itertools.module.module|...chain") == "itertools|chain"


@mark.parametrize("caller", (format_import_path, lazy_import))
def test_lazy_import_path_validation(caller):
    with raises(ValueError):
        caller("")  # empty path

    with raises(ValueError):
        caller("path.without.module")

    with raises(ValueError):
        caller(".relative.module.path|name.name")

    with raises(ValueError):
        caller("invalid path")


def test_lazy_import_path():
    class _ClassA(object):

        class _ClassB(object):
            __qualname__ = "_ClassA._ClassB"

    globals()[_ClassA.__name__] = _ClassA

    import_path = "{}|{}".format(__name__, _ClassA._ClassB.__qualname__)
    assert lazy_import(import_path)


def test_lazy_import_relative_path():
    class _ClassA(object):

        class _ClassB(object):
            __qualname__ = "_ClassA._ClassB"

    globals()[_ClassA.__name__] = _ClassA

    import_path = "{}.sub_module.sub_module|...{}".format(
        __name__,
        _ClassA._ClassB.__qualname__,
    )
    assert lazy_import(import_path)


def test_get_import_path():
    class _ClassA(object):

        class _ClassB(object):
            __qualname__ = "_ClassA._ClassB"

    globals()[_ClassA.__name__] = _ClassA

    import_path = "{}|{}".format(__name__, _ClassA._ClassB.__qualname__)
    assert import_path == get_import_path(_ClassA._ClassB)


def test_inconsistent_import_path():
    class _ClassA(object):
        pass

    with raises(ValueError):
        get_import_path(_ClassA)


if __name__ == "__main__":
    main()
