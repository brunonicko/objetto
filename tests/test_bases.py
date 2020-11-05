# -*- coding: utf-8 -*-

import copy

import pytest
import six

from objetto._bases import (
    FINAL_CLASS_TAG,
    FINAL_METHOD_TAG,
    INITIALIZING_TAG,
    Base,
    BaseMeta,
    final,
    init,
    init_context,
    simplify_member_names,
)


def test_initializing():
    class MyBase(Base):
        def __init__(self):
            assert getattr(self, INITIALIZING_TAG) is True
            self._method()

        def _method(self):
            assert getattr(self, INITIALIZING_TAG) is True

        def method(self):
            assert getattr(self, INITIALIZING_TAG) is False

        @init
        def init_method(self):
            assert getattr(self, INITIALIZING_TAG) is True

        def init_method_context(self):
            with init_context(self):
                assert getattr(self, INITIALIZING_TAG) is True
            assert getattr(self, INITIALIZING_TAG) is False

    class MySubBase(MyBase):
        def __init__(self):
            super(MySubBase, self).__init__()
            assert getattr(self, INITIALIZING_TAG) is True
            self._method()

        def init_method(self):
            assert getattr(self, INITIALIZING_TAG) is False

    my_obj = MyBase()
    my_obj.method()
    my_obj.init_method()
    my_obj.init_method_context()
    assert getattr(my_obj, INITIALIZING_TAG) is False

    my_sub_obj = MySubBase()
    my_sub_obj.method()
    my_sub_obj.init_method()
    my_sub_obj.init_method_context()
    assert getattr(my_sub_obj, INITIALIZING_TAG) is False


def test_force_hash_declaration():

    with pytest.raises(TypeError):

        class MyBase(Base):
            def __eq__(self, other):
                return False

        raise AssertionError(MyBase)


def test_final_decorator():
    class MyBase(Base):

        @final
        def my_final_method(self):
            return

    assert hasattr(MyBase.__dict__["my_final_method"], FINAL_METHOD_TAG)
    assert getattr(MyBase.__dict__["my_final_method"], FINAL_METHOD_TAG) is True


def test_final_method():
    class MyBase(Base):

        @final
        def my_final_method(self):
            return

    with pytest.raises(TypeError):
        # noinspection PyFinal
        class MySubBase(MyBase):
            def my_final_method(self):
                return

        raise AssertionError(MySubBase)


def test_final_classmethod():
    class MyBase(Base):

        @classmethod
        @final
        def my_final_method(cls):
            return

    with pytest.raises(TypeError):
        # noinspection PyFinal
        class MySubBase(MyBase):
            @classmethod
            def my_final_method(cls):
                return

        raise AssertionError(MySubBase)


def test_final_staticmethod():
    class MyBase(Base):

        @staticmethod
        @final
        def my_final_method():
            return

    with pytest.raises(TypeError):
        # noinspection PyFinal
        class MySubBase(MyBase):
            @staticmethod
            def my_final_method():
                return

        raise AssertionError(MySubBase)


def test_final_property():
    class MyBase(Base):

        @property
        @final
        def my_final_property(self):
            return

    with pytest.raises(TypeError):
        # noinspection PyFinal
        class MySubBase(MyBase):
            @property
            def my_final_property(self):
                return

        raise AssertionError(MySubBase)


def test_final_class():
    @final
    class MyBase(Base):
        pass

    with pytest.raises(TypeError):
        # noinspection PyFinal
        class MySubBase(MyBase):  # type: ignore
            pass

        raise AssertionError(MySubBase)

    class MyOtherSubBase(type(Base)("MyOtherBase", (Base,), {FINAL_CLASS_TAG: 1})):
        pass

    assert MyOtherSubBase


def test_ne():
    class MyBase(Base):
        __slots__ = ("value",)

        def __init__(self, value):
            self.value = value

        __hash__ = None

        def __eq__(self, other):
            return self.value is other.value

    assert MyBase(True) == MyBase(True)
    assert MyBase(True) != MyBase(False)

    class MyOtherBase(MyBase):

        __hash__ = None

        def __eq__(self, other):
            return NotImplemented

    assert MyOtherBase(True) == MyBase(True)
    assert MyOtherBase(True) != MyBase(False)
    assert MyOtherBase(True).__ne__(MyBase(True)) is NotImplemented


def test_copy():
    base = Base()

    with pytest.raises(RuntimeError):
        _ = copy.copy(base)


def test_dir():
    def get_var():
        return None

    def get_method():
        return lambda *args: None

    def get_class_method():
        return classmethod(get_method())

    def get_static_method():
        return staticmethod(get_method())

    def get_property_method():
        return property(get_method())

    class MyBaseMeta(BaseMeta):
        (
            meta_var,
            _meta_var,
            __meta_var,
            __meta_var__,
        ) = (get_var(),) * 4
        meta_method, _meta_method, __meta_method, __meta_method__ = (get_method(),) * 4
        (
            meta_class_method,
            _meta_class_method,
            __meta_class_method,
            __meta_class_method__,
        ) = (get_class_method(),) * 4
        (
            meta_static_method,
            _meta_static_method,
            __meta_static_method,
            __meta_static_method__,
        ) = (get_static_method(),) * 4
        (
            meta_property_method,
            _meta_property_method,
            __meta_property_method,
            __meta_property_method__,
        ) = (get_property_method(),) * 4

    class MyBase(six.with_metaclass(MyBaseMeta, Base)):
        __slots__ = ("var", "_var", "__var", "__var__")

        (
            class_var,
            _class_var,
            __class_var,
            __class_var__,
        ) = (get_var(),) * 4
        method, _method, __method, __method__ = (get_method(),) * 4
        class_method, _class_method, __class_method, __class_method__ = (
            get_class_method(),
        ) * 4
        static_method, _static_method, __static_method, __static_method__ = (
            get_static_method(),
        ) * 4
        property_method, _property_method, __property_method, __property_method__ = (
            get_property_method(),
        ) * 4

        def __init__(self):
            self.var = None
            self._var = None
            self.__var = None
            self.__var__ = None

    class MySubBase(MyBase):
        pass

    for obj in (MyBase, MyBase(), MySubBase, MySubBase()):
        assert dir(obj) == list(simplify_member_names(dir(obj)))
        for member_name in dir(obj):
            getattr(obj, member_name)


if __name__ == "__main__":
    pytest.main()
