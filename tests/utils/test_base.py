# -*- coding: utf-8 -*-

from pickle import loads, dumps
from typing import TypeVar

from pytest import main, raises
from six import with_metaclass

from objetto.utils.base import (
    _FINAL_CLASS_TAG,
    _FINAL_METHOD_TAG,
    BaseMeta,
    Base,
    GenericBaseMeta,
    GenericBase,
    final,
    _base_reducer,
)


def test_force_declare_hash_when_declared_eq():
    with raises(TypeError):
        class _Base(with_metaclass(BaseMeta, object)):
            __eq__ = None

        assert not _Base

    class _Base(with_metaclass(BaseMeta, object)):
        __hash__ = None
        __eq__ = None

    assert _Base


def test_prevent_class_property_override():

    class _BaseMeta(BaseMeta):

        @property
        def class_property(cls):
            return

    with raises(TypeError):
        class _SubClass(with_metaclass(_BaseMeta, object)):
            __slots__ = ("class_property",)

        assert not _SubClass


def test_final_method():

    def dummy_decorator(func):
        return func

    class PropertyLike(object):

        def __init__(self, fget):
            self.fget = fget

        def __get__(self, instance, owner):
            return 3

    class FinalDescriptor(object):

        def __init__(self, func):
            self.func = func

        def __get__(self, instance, owner):
            return 3

    setattr(FinalDescriptor, _FINAL_METHOD_TAG, True)

    decorators = [
        dummy_decorator,
        PropertyLike,
        FinalDescriptor,
        classmethod,
        staticmethod,
        property,
    ]

    for decorator in decorators:

        class _Base(with_metaclass(BaseMeta, object)):

            @decorator
            @final
            def method(self):
                pass

        with raises(TypeError):
            class _SubClass(_Base):

                @decorator
                def method(self):  # type: ignore
                    pass

            assert not _SubClass


def test_final_class():

    @final
    class _Base(with_metaclass(BaseMeta, object)):
        pass

    assert getattr(_Base, _FINAL_CLASS_TAG) is True

    with raises(TypeError):
        class _SubClass(_Base):  # type: ignore
            pass

        assert not _SubClass


def test_generic_base():
    assert issubclass(GenericBaseMeta, BaseMeta)
    assert issubclass(GenericBase, Base)
    assert type(GenericBase) is GenericBaseMeta

    t = TypeVar("t")

    assert GenericBase[t] is GenericBase

    class CustomGenericBase(GenericBase[t], Base):
        pass

    assert issubclass(CustomGenericBase, Base)
    assert isinstance(CustomGenericBase, BaseMeta)
    assert isinstance(CustomGenericBase, GenericBaseMeta)


def test_prevent_setting_class_members():

    class _Base(with_metaclass(BaseMeta, object)):
        pass

    with raises(AttributeError):
        _Base.__repr__ = None

    with raises(AttributeError):
        _Base._cls_attribute = None


def test_prevent_changing_class_members():

    class _Base(with_metaclass(BaseMeta, object)):
        _cls_attribute = None

    with raises(AttributeError):
        _Base.__repr__ = None

    with raises(AttributeError):
        _Base._cls_attribute = 1


def test_prevent_deleting_class_members():

    class _Base(with_metaclass(BaseMeta, object)):
        _cls_attribute = None

    with raises(AttributeError):
        del _Base.__repr__

    with raises(AttributeError):
        del _Base._cls_attribute


def test_not_equal():

    class _Base(Base):
        __slots__ = ("eq_result",)
        __hash__ = None

        def __init__(self, eq_result):
            self.eq_result = eq_result

        def __eq__(self, other):
            return self.eq_result

    obj = _Base(True)
    assert obj.__eq__(3) is not obj.__ne__(3)

    obj = _Base(False)
    assert obj.__eq__(3) is not obj.__ne__(3)

    obj = _Base(NotImplemented)
    assert obj.__eq__(3) is NotImplemented and obj.__ne__(3) is NotImplemented


def test_reduce():
    class _PickableBase(Base):
        __slots__ = ("number",)
        __module__ = __name__
        __qualname__ = "_PickableBase"

        def __init__(self, number):
            self.number = number

    globals()[_PickableBase.__name__] = _PickableBase

    obj = _PickableBase(3)
    unpickled_obj = loads(dumps(obj))

    assert type(obj) is type(unpickled_obj)
    assert obj.number == unpickled_obj.number


def test_reducer():
    called_set_state = [False]

    class _ImportableBase(object):

        def __setstate__(self, state):
            assert state == {"a": 1, "b": 2}
            called_set_state[0] = True

    globals()[_ImportableBase.__name__] = _ImportableBase

    _base_reducer("{}|{}".format(__name__, _ImportableBase.__name__), {"a": 1, "b": 2})
    assert called_set_state[0]


if __name__ == "__main__":
    main()
