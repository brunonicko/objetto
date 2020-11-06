# -*- coding: utf-8 -*-

import pytest

from six import with_metaclass

from objetto._containers.bases import (
    BaseRelationship,
    BaseContainerMeta,
    BaseContainer,
    BaseAuxiliaryContainerMeta,
    BaseAuxiliaryContainer,
    make_auxiliary_cls,
)
from objetto.utils.immutable import ImmutableDict


class MyContainerMeta(BaseContainerMeta):

    @property
    def _serializable_container_types(cls):
        return (MyContainer,)


class MyContainer(with_metaclass(MyContainerMeta, BaseContainer)):
    __slots__ = ("__state",)
    _relationship = BaseRelationship()

    def __init__(self, **kwargs):
        self.__state = ImmutableDict(kwargs)

    @classmethod
    def _get_relationship(cls, location=None):
        return cls._relationship

    @classmethod
    def deserialize(cls, serialized, **kwargs):
        return cls(
            **dict((k, cls.deserialize_value(v)) for k, v in serialized.items())
        )

    def serialize(self, **kwargs):
        return dict((k, self.serialize_value(v)) for k, v in self._state.items())

    @property
    def _state(self):
        # type: () -> ImmutableDict
        return self.__state


class SimpleContainer(MyContainer):
    _relationship = BaseRelationship(types=(int, __name__ + "|SimpleContainer"))


class ComplexContainer(MyContainer):
    _relationship = BaseRelationship(types=(int, MyContainer), subtypes=True)


def test_base_relationship():
    relationship = BaseRelationship()
    assert relationship.passthrough is True

    relationship = BaseRelationship(factory=int)
    assert relationship.passthrough is False

    relationship = BaseRelationship(types=int, type_checked=False)
    assert relationship.types == (int,)
    assert relationship.passthrough is True

    relationship = BaseRelationship(types=int, type_checked=False, factory=int)
    assert relationship.types == (int,)
    assert relationship.factory == int
    assert relationship.passthrough is False

    relationship = BaseRelationship(types=int, factory=int)
    assert relationship.types == (int,)
    assert relationship.factory == int
    assert relationship.passthrough is False

    assert BaseRelationship(SimpleContainer).get_single_exact_type(
        (SimpleContainer,)
    ) is SimpleContainer
    assert BaseRelationship((SimpleContainer, int)).get_single_exact_type(
        (SimpleContainer,)
    ) is SimpleContainer
    assert BaseRelationship(SimpleContainer, subtypes=True).get_single_exact_type(
        (SimpleContainer,)
    ) is None


def test_value_serialization():
    assert SimpleContainer.deserialize_value(1) == 1
    container = SimpleContainer()
    assert container.serialize_value(1) == 1
    assert container.serialize_value(SimpleContainer(a=1, b=2, __class__=3)) == (
        {"a": 1, "b": 2, "\\__class__": 3}
    )
    deserialized = SimpleContainer.deserialize_value({"a": 1, "b": 2, "\\__class__": 3})
    assert type(deserialized) is SimpleContainer
    assert dict(deserialized._state) == {"a": 1, "b": 2, "__class__": 3}
    with pytest.raises(TypeError):
        SimpleContainer.deserialize_value("a")

    assert ComplexContainer.deserialize_value(1) == 1
    container = ComplexContainer()
    assert container.serialize_value(1) == 1
    assert container.serialize_value(ComplexContainer(a=1, b=2, __class__=3)) == (
        {
            "__class__": __name__ + "|ComplexContainer",
            "value": {"a": 1, "b": 2, "\\__class__": 3}
        }
    )
    deserialized = ComplexContainer.deserialize_value(
        {
            "__class__": __name__ + "|ComplexContainer",
            "value": {"a": 1, "b": 2, "\\__class__": 3}
        }
    )
    assert type(deserialized) is ComplexContainer
    assert dict(deserialized._state) == {"a": 1, "b": 2, "__class__": 3}
    with pytest.raises(TypeError):
        ComplexContainer.deserialize_value("a")


def test_auxiliary_container():

    class MyRelationship(BaseRelationship):
        pass

    class MyAuxiliaryContainerMeta(BaseAuxiliaryContainerMeta):

        @property
        def _relationship_type(cls):
            return MyRelationship

        @property
        def _serializable_container_types(cls):
            return ()

    class MyAuxiliaryContainer(
        with_metaclass(MyAuxiliaryContainerMeta, BaseAuxiliaryContainer)
    ):
        _relationship = MyRelationship()

    assert MyAuxiliaryContainer

    with pytest.raises(TypeError):
        class MyBadAuxiliaryContainer(
            with_metaclass(MyAuxiliaryContainerMeta, BaseAuxiliaryContainer)
        ):
            _relationship = BaseRelationship()

        raise AssertionError(MyBadAuxiliaryContainer)

    custom_auxiliary_cls = make_auxiliary_cls(
        MyAuxiliaryContainer, MyRelationship((int, str))
    )

    assert custom_auxiliary_cls.__name__ == "IntStrMyAuxiliaryContainer"


if __name__ == "__main__":
    pytest.main()
