# -*- coding: utf-8 -*-

import copy
import pickle

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

import pytest
import six
import slotted

from objetto._bases import (
    FINAL_CLASS_TAG,
    FINAL_METHOD_TAG,
    INITIALIZING_TAG,
    Base,
    BaseCollection,
    BaseContainer,
    BaseDict,
    BaseHashable,
    BaseInteractiveCollection,
    BaseInteractiveDict,
    BaseInteractiveList,
    BaseInteractiveSet,
    BaseIterable,
    BaseList,
    BaseMeta,
    BaseMutableCollection,
    BaseMutableDict,
    BaseMutableList,
    BaseMutableSet,
    BaseProtectedCollection,
    BaseProtectedDict,
    BaseProtectedList,
    BaseProtectedSet,
    BaseSet,
    BaseSized,
    abstract_member,
    final,
    init,
    init_context,
    make_base_cls,
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


class GeneratedBaseParent(object):
    GeneratedBase = None


def test_make_base_cls():
    default_base_cls = make_base_cls()
    assert default_base_cls.__name__ == Base.__name__
    assert default_base_cls.__qualname__ == Base.__fullname__
    assert default_base_cls.__module__ == Base.__module__

    base_cls = make_base_cls(
        Base, "GeneratedBaseParent.GeneratedBase", __name__, {"class_var": 10}
    )
    assert issubclass(base_cls, Base)
    assert base_cls.__name__ == "GeneratedBase"
    assert base_cls.__qualname__ == "GeneratedBaseParent.GeneratedBase"
    assert base_cls.__module__ == __name__
    assert hasattr(base_cls, "__reduce__")

    GeneratedBaseParent.GeneratedBase = base_cls

    instance = base_cls()
    assert isinstance(instance, base_cls)
    assert type(instance) is base_cls

    pickled_instance = pickle.loads(pickle.dumps(instance))
    assert pickled_instance is not instance
    assert isinstance(pickled_instance, base_cls)
    assert type(pickled_instance) is base_cls


MyGeneratedBase = make_base_cls(Base, "MyGeneratedBase", __name__, {})


class MySubBase(MyGeneratedBase):
    pass


def test_generated_base_subclass():
    assert MySubBase.__name__ != MyGeneratedBase.__name__
    try:
        my_sub_base_qual_name = MySubBase.__qualname__
    except AttributeError:  # for python 2.7
        assert MyGeneratedBase.__qualname__ == MyGeneratedBase.__name__
        assert not hasattr(object, "__qualname__")
        assert not hasattr(MySubBase, "__qualname__")
    else:
        assert my_sub_base_qual_name != MyGeneratedBase.__qualname__


def test_generated_base_subclass_instance():
    instance = MySubBase()
    assert isinstance(instance, MySubBase)
    assert type(instance) is MySubBase
    pickled_instance = pickle.loads(pickle.dumps(instance))
    assert pickled_instance is not instance
    assert isinstance(pickled_instance, MyGeneratedBase)
    assert isinstance(pickled_instance, MySubBase)
    assert type(pickled_instance) is MySubBase


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


def test_abstract_member():
    class AbstractClass(Base):
        some_attribute = abstract_member()

    with pytest.raises(TypeError):
        AbstractClass()

    class ConcreteClass(AbstractClass):
        some_attribute = (1, 2, 3)

    obj = ConcreteClass()
    assert obj


def test_required_overrides():
    def check_base(base, slotted_base):
        assert issubclass(slotted_base, slotted.SlottedABC)
        exclude = {
            "__weakref__",
            "__metaclass__",
            "__setstate__",
            "__getstate__",
            "__slots__",
            "_MutableMapping__marker",
            "_abc_negative_cache_version",
        }
        assert issubclass(base, Base)
        assert issubclass(base, slotted_base)
        for open_attribute in getattr(base, "_BaseMeta__open_attributes")[base]:
            if open_attribute in exclude:
                continue
            member = getattr(base, open_attribute)
            try:
                original = getattr(slotted_base, open_attribute)
            except AttributeError:
                continue
            object_original = getattr(object, open_attribute, None)
            if member is None and original is None:
                continue
            if member is original and member is not object_original:
                raise AssertionError(
                    "'{}' does not override '{}.{}'".format(
                        base.__name__, slotted_base.__name__, open_attribute
                    )
                )

    bases = (
        (BaseHashable, slotted.SlottedHashable),
        (BaseSized, slotted.SlottedSized),
        (BaseIterable, slotted.SlottedIterable),
        (BaseContainer, slotted.SlottedContainer),
        (BaseDict, slotted.SlottedMapping),
        (BaseMutableDict, slotted.SlottedMutableMapping),
        (BaseList, slotted.SlottedSequence),
        (BaseMutableList, slotted.SlottedMutableSequence),
        (BaseSet, slotted.SlottedSet),
        (BaseMutableSet, slotted.SlottedMutableSet),
    )

    for b, s in bases:
        check_base(b, s)


def test_inheritance():

    assert issubclass(BaseMeta, slotted.SlottedABCMeta)
    assert issubclass(Base, slotted.SlottedABC)
    assert isinstance(Base, BaseMeta)

    assert issubclass(BaseHashable, Base)
    assert issubclass(BaseHashable, slotted.SlottedHashable)

    assert issubclass(BaseSized, Base)
    assert issubclass(BaseSized, slotted.SlottedSized)

    assert issubclass(BaseIterable, Base)
    assert issubclass(BaseIterable, slotted.SlottedIterable)

    assert issubclass(BaseContainer, Base)
    assert issubclass(BaseContainer, slotted.SlottedContainer)

    assert issubclass(BaseCollection, BaseContainer)
    assert issubclass(BaseCollection, BaseSized)
    assert issubclass(BaseCollection, BaseIterable)
    if slotted.SlottedCollection is not None:
        assert issubclass(BaseCollection, slotted.SlottedCollection)

    assert issubclass(BaseProtectedCollection, BaseCollection)
    assert issubclass(BaseInteractiveCollection, BaseProtectedCollection)
    assert issubclass(BaseMutableCollection, BaseProtectedCollection)
    assert not issubclass(BaseMutableCollection, BaseInteractiveCollection)
    assert not issubclass(BaseInteractiveCollection, BaseMutableCollection)

    assert issubclass(BaseDict, BaseCollection)
    assert not issubclass(BaseDict, collections_abc.Hashable)
    assert issubclass(BaseDict, slotted.SlottedMapping)
    assert issubclass(BaseProtectedDict, BaseProtectedCollection)
    assert issubclass(BaseInteractiveDict, BaseInteractiveCollection)
    assert issubclass(BaseMutableDict, BaseMutableCollection)
    assert issubclass(BaseMutableDict, slotted.SlottedMutableMapping)

    assert issubclass(BaseProtectedDict, BaseDict)
    assert issubclass(BaseInteractiveDict, BaseProtectedDict)
    assert issubclass(BaseMutableDict, BaseProtectedDict)
    assert not issubclass(BaseMutableDict, BaseInteractiveDict)
    assert not issubclass(BaseInteractiveDict, BaseMutableDict)

    assert issubclass(BaseList, BaseCollection)
    assert not issubclass(BaseList, collections_abc.Hashable)
    assert issubclass(BaseList, slotted.SlottedSequence)
    assert issubclass(BaseProtectedList, BaseProtectedCollection)
    assert issubclass(BaseInteractiveList, BaseInteractiveCollection)
    assert issubclass(BaseMutableList, BaseMutableCollection)
    assert issubclass(BaseMutableList, slotted.SlottedMutableSequence)

    assert issubclass(BaseProtectedList, BaseList)
    assert issubclass(BaseInteractiveList, BaseProtectedList)
    assert issubclass(BaseMutableList, BaseProtectedList)
    assert not issubclass(BaseMutableList, BaseInteractiveList)
    assert not issubclass(BaseInteractiveList, BaseMutableList)

    assert issubclass(BaseSet, BaseCollection)
    assert not issubclass(BaseSet, collections_abc.Hashable)
    assert issubclass(BaseSet, slotted.SlottedSet)
    assert issubclass(BaseProtectedSet, BaseProtectedCollection)
    assert issubclass(BaseInteractiveSet, BaseInteractiveCollection)
    assert issubclass(BaseMutableSet, BaseMutableCollection)
    assert issubclass(BaseMutableSet, slotted.SlottedMutableSet)

    assert issubclass(BaseProtectedSet, BaseSet)
    assert issubclass(BaseInteractiveSet, BaseProtectedSet)
    assert issubclass(BaseMutableSet, BaseProtectedSet)
    assert not issubclass(BaseMutableSet, BaseInteractiveSet)
    assert not issubclass(BaseInteractiveSet, BaseMutableSet)


if __name__ == "__main__":
    pytest.main()
