# -*- coding: utf-8 -*-

import pytest

from six import with_metaclass

from objetto._bases import ABSTRACT_TAG, FINAL_METHOD_TAG
from objetto._containers.bases import (
    BaseRelationship,
    BaseContainer,
    BaseSemiInteractiveContainer,
    BaseInteractiveContainer,
    BaseMutableContainer,
)
from objetto._containers.container import (
    BaseAttribute,
    ContainerMeta,
    Container,
    SemiInteractiveContainer,
    InteractiveContainer,
    MutableContainer,
)
from objetto.utils.immutable import ImmutableDict


class MyRelationship(BaseRelationship):
    pass


class MyAttribute(BaseAttribute):
    def __init__(self, relationship=MyRelationship(), **kwargs):
        super(MyAttribute, self).__init__(relationship=relationship, **kwargs)


class MyContainerMeta(ContainerMeta):
    @property
    def _attribute_type(cls):
        return MyAttribute

    @property
    def _serializable_container_types(cls):
        return (MyContainer,)

    @property
    def _relationship_type(cls):
        return MyRelationship


class MyContainer(with_metaclass(MyContainerMeta, Container)):
    __slots__ = ("__state",)

    def __init__(self, **kwargs):
        self.__state = ImmutableDict(kwargs)

    def __getitem__(self, name):
        return self._state[name]

    def __contains__(self, pair):
        name, value = pair
        return name in self._state and self._state[name] == value

    def __iter__(self):
        for name, value in self._state.items():
            yield name, value

    def __len__(self):
        return len(self._state)

    def _hash(self):
        raise NotImplementedError()

    def _eq(self, other):
        raise NotImplementedError()

    def get(self, location, fallback=None):
        raise NotImplementedError()

    @classmethod
    def deserialize(cls, serialized, **kwargs):
        raise NotImplementedError()

    def serialize(self, **kwargs):
        raise NotImplementedError()

    @property
    def _state(self):
        # type: () -> ImmutableDict
        return self.__state


def test_base_attribute():
    assert (
        BaseAttribute(module="mod", default_factory="fac").default_factory == "mod|fac"
    )
    assert (
        BaseAttribute(
            relationship=BaseRelationship(module="mod"), default_factory="fac"
        ).default_factory
        == "mod|fac"
    )

    with pytest.raises(ValueError):
        BaseAttribute(default=0, default_factory=int)

    with pytest.raises(ValueError):
        BaseAttribute(final=True, abstract=True)

    assert getattr(BaseAttribute(final=True), FINAL_METHOD_TAG)
    assert getattr(BaseAttribute(abstract=True), ABSTRACT_TAG)
    assert not hasattr(BaseAttribute(), FINAL_METHOD_TAG)
    assert not hasattr(BaseAttribute(), ABSTRACT_TAG)


def test_stored_attributes():
    class BadMixin(object):
        __slots__ = ()
        foo_bar = MyAttribute()
        bar_foo = MyAttribute()

    class FooBar(MyContainer, BadMixin):
        foo = MyAttribute()
        bar = MyAttribute()
        foobar = BaseAttribute()

    assert dict(FooBar._attributes) == {"foo": FooBar.foo, "bar": FooBar.bar}
    assert dict(FooBar._attribute_names) == {FooBar.foo: "foo", FooBar.bar: "bar"}

    class FooBarBar(FooBar):
        foo = 10

    assert dict(FooBarBar._attributes) == {"bar": FooBar.bar}
    assert dict(FooBarBar._attribute_names) == {FooBar.bar: "bar"}

    instance = FooBar(foo=1, bar=2)
    assert instance.foo == 1
    assert instance.bar == 2
    assert instance.foobar is FooBar.foobar
    assert instance.foo_bar is FooBar.foo_bar
    assert instance.bar_foo is FooBar.bar_foo

    with pytest.raises(TypeError):

        class Foo(MyContainer):
            bad_foo = MyAttribute(BaseRelationship())

        raise AssertionError(Foo)


def test_reserved_member_names():
    with pytest.raises(TypeError):

        class MyBadContainer(Container):
            keys = 1

        raise AssertionError(MyBadContainer)

    with pytest.raises(TypeError):

        class BadBase(object):
            __slots__ = ()
            keys = 1

        class MyBadContainer(Container, BadBase):
            pass

        raise AssertionError(MyBadContainer)


def test_inheritance():
    assert issubclass(Container, BaseContainer)

    assert issubclass(SemiInteractiveContainer, Container)
    assert issubclass(SemiInteractiveContainer, BaseSemiInteractiveContainer)
    assert issubclass(InteractiveContainer, SemiInteractiveContainer)
    assert issubclass(InteractiveContainer, BaseInteractiveContainer)
    assert issubclass(MutableContainer, InteractiveContainer)
    assert issubclass(MutableContainer, BaseMutableContainer)


if __name__ == "__main__":
    pytest.main()
