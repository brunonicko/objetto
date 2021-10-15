

from pytest import main, raises

from objetto.utils.type_checking import (
    format_types,
    get_type_names,
    import_types,
    is_instance,
    is_subclass,
    assert_is_instance,
    assert_is_subclass,
)


class Cls(object):
    pass


class SubCls(Cls):
    pass


cls_path = __name__ + "|" + Cls.__name__
subcls_path = __name__ + "|" + SubCls.__name__


def test_format_types():
    assert format_types(None) == (type(None),)
    assert format_types((None,)) == (type(None),)
    assert format_types((int, "chain"), default_module="itertools") == (
        int, "itertools|chain"
    )
    assert format_types(float) == (float,)
    assert format_types("itertools|chain") == ("itertools|chain",)
    assert format_types((int, ("chain", float)), default_module="itertools") == (
        int,
        "itertools|chain",
        float,
    )
    with raises(ValueError):
        format_types("abstract method|a b c")
    with raises(TypeError):
        params = (3,)
        format_types(*params)


def test_get_type_names():
    from abc import ABCMeta
    from itertools import chain

    assert get_type_names(None) == (type(None).__name__,)
    assert get_type_names((None,)) == (type(None).__name__,)
    assert get_type_names(
        ("module.module|Cls", "abc|abstractmethod", ABCMeta, chain)
    ) == ("Cls", "abstractmethod", "ABCMeta", "chain")


def test_import_types():
    from abc import ABCMeta, abstractmethod
    from itertools import chain

    assert import_types(None) == (type(None),)
    assert import_types((None,)) == (type(None),)
    assert import_types(("abc|abstractmethod", ABCMeta, chain)) == (
        abstractmethod,
        ABCMeta,
        chain,
    )


def test_is_instance():
    assert is_instance(None, None)
    assert is_instance(None, (None,))
    assert not is_instance(0, None)
    assert not is_instance(0, (None,))

    assert is_instance(Cls(), cls_path) is True
    assert is_instance(Cls(), cls_path, accept_subtypes=False) is True
    assert is_instance(SubCls(), cls_path) is True
    assert is_instance(SubCls(), cls_path, accept_subtypes=False) is False
    assert is_instance(SubCls(), subcls_path, accept_subtypes=False) is True

    assert is_instance(Cls(), (cls_path, Cls, int)) is True
    assert is_instance(Cls(), (cls_path, Cls, int), accept_subtypes=False) is True
    assert is_instance(SubCls(), (cls_path, Cls, int)) is True
    assert is_instance(SubCls(), (cls_path, Cls, int), accept_subtypes=False) is False
    assert is_instance(
        SubCls(), (subcls_path, SubCls, int), accept_subtypes=False
    ) is True

    assert is_instance(Cls(), (int, float)) is False
    assert is_instance(Cls(), (int, float), accept_subtypes=False) is False
    assert is_instance(SubCls(), (int, float)) is False
    assert is_instance(SubCls(), (int, float), accept_subtypes=False) is False
    assert is_instance(SubCls(), (int, float), accept_subtypes=False) is False

    assert is_instance(Cls(), ()) is False
    assert is_instance(SubCls(), ()) is False


def test_is_subclass():
    assert is_subclass(type(None), None)
    assert is_subclass(type(None), (None,))
    assert not is_subclass(int, None)
    assert not is_subclass(int, (None,))

    assert is_subclass(Cls, cls_path) is True
    assert is_subclass(Cls, cls_path, accept_subtypes=False) is True
    assert is_subclass(SubCls, cls_path) is True
    assert is_subclass(SubCls, cls_path, accept_subtypes=False) is False
    assert is_subclass(SubCls, subcls_path, accept_subtypes=False) is True

    assert is_subclass(Cls, (cls_path, Cls, int)) is True
    assert is_subclass(Cls, (cls_path, Cls, int), accept_subtypes=False) is True
    assert is_subclass(SubCls, (cls_path, Cls, int)) is True
    assert is_subclass(SubCls, (cls_path, Cls, int), accept_subtypes=False) is False
    assert is_subclass(
        SubCls, (subcls_path, SubCls, int), accept_subtypes=False
    ) is True

    assert is_subclass(Cls, (int, float)) is False
    assert is_subclass(Cls, (int, float), accept_subtypes=False) is False
    assert is_subclass(SubCls, (int, float)) is False
    assert is_subclass(SubCls, (int, float), accept_subtypes=False) is False
    assert is_subclass(SubCls, (int, float), accept_subtypes=False) is False

    assert is_subclass(Cls, ()) is False
    assert is_subclass(SubCls, ()) is False


def test_assert_is_instance():
    assert_is_instance(None, None)
    assert_is_instance(None, (None,))
    with raises(TypeError):
        assert_is_instance(0, None)
        assert_is_instance(0, (None,))

    assert_is_instance(Cls(), cls_path)
    assert_is_instance(Cls(), cls_path, accept_subtypes=False)
    assert_is_instance(SubCls(), cls_path)

    with raises(TypeError):
        assert_is_instance(SubCls(), cls_path, accept_subtypes=False)

    assert_is_instance(SubCls(), subcls_path, accept_subtypes=False)

    assert_is_instance(Cls(), (cls_path, Cls, int))
    assert_is_instance(Cls(), (cls_path, Cls, int), accept_subtypes=False)
    assert_is_instance(SubCls(), (cls_path, Cls, int))

    with raises(TypeError):
        assert_is_instance(SubCls(), (cls_path, Cls, int), accept_subtypes=False)

    assert_is_instance(SubCls(), (subcls_path, SubCls, int), accept_subtypes=False)

    with raises(TypeError):
        assert_is_instance(Cls(), (int, float))

    with raises(TypeError):
        assert_is_instance(Cls(), (int, float), accept_subtypes=False)

    with raises(TypeError):
        assert_is_instance(SubCls(), (int, float))

    with raises(TypeError):
        assert_is_instance(SubCls(), (int, float), accept_subtypes=False)

    with raises(TypeError):
        assert_is_instance(SubCls(), (int, float), accept_subtypes=False)

    with raises(TypeError):
        assert_is_instance(Cls(), ())

    with raises(TypeError):
        assert_is_instance(SubCls(), ())


def test_assert_is_subclass():
    assert_is_subclass(type(None), None)
    assert_is_subclass(type(None), (None,))
    with raises(TypeError):
        assert_is_subclass(int, None)
        assert_is_subclass(int, (None,))

    assert_is_subclass(Cls, cls_path)
    assert_is_subclass(Cls, cls_path, accept_subtypes=False)
    assert_is_subclass(SubCls, cls_path)

    with raises(TypeError):
        assert_is_subclass(SubCls, cls_path, accept_subtypes=False)

    assert_is_subclass(SubCls, subcls_path, accept_subtypes=False)

    assert_is_subclass(Cls, (cls_path, Cls, int))
    assert_is_subclass(Cls, (cls_path, Cls, int), accept_subtypes=False)
    assert_is_subclass(SubCls, (cls_path, Cls, int))

    with raises(TypeError):
        assert_is_subclass(SubCls, (cls_path, Cls, int), accept_subtypes=False)

    assert_is_subclass(SubCls, (subcls_path, SubCls, int), accept_subtypes=False)

    with raises(TypeError):
        assert_is_subclass(Cls, (int, float))

    with raises(TypeError):
        assert_is_subclass(Cls, (int, float), accept_subtypes=False)

    with raises(TypeError):
        assert_is_subclass(SubCls, (int, float))

    with raises(TypeError):
        assert_is_subclass(SubCls, (int, float), accept_subtypes=False)

    with raises(TypeError):
        assert_is_subclass(SubCls, (int, float), accept_subtypes=False)

    with raises(TypeError):
        assert_is_subclass(Cls, ())

    with raises(TypeError):
        assert_is_subclass(SubCls, ())


if __name__ == "__main__":
    main()
