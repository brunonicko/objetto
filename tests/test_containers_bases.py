# -*- coding: utf-8 -*-

import pytest

from six import with_metaclass

from slotted import SlottedContainer, SlottedSized, SlottedIterable
from objetto._bases import Base
from objetto._containers.bases import (
    BaseRelationship,
    UniqueDescriptor,
    BaseContainerMeta,
    BaseContainer,
    BaseSemiInteractiveContainer,
    BaseInteractiveContainer,
    BaseMutableContainer,
    BaseAuxiliaryContainerMeta,
    BaseAuxiliaryContainer,
    make_auxiliary_cls,
    BaseSemiInteractiveAuxiliaryContainer,
    BaseInteractiveAuxiliaryContainer,
    BaseMutableAuxiliaryContainer,
)
from objetto.utils.immutable import ImmutableDict


class MyRelationShip(BaseRelationship):
    pass


class MyContainerMeta(BaseContainerMeta):

    @property
    def _relationship_type(cls):
        return MyRelationShip

    @property
    def _serializable_container_types(cls):
        return (MyContainer,)


class MyContainer(with_metaclass(MyContainerMeta, BaseContainer)):
    __slots__ = ("__state",)
    _relationship = MyRelationShip()

    def __init__(self, **kwargs):
        self.__state = ImmutableDict(kwargs)

    def __contains__(self, item):
        raise NotImplementedError()

    def __iter__(self):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()

    def _hash(self):
        return hash(self._state)

    def _eq(self, other):
        if self is other:
            return True
        elif isinstance(other, MyContainer):
            return self.__state == other.__state
        else:
            return False

    @classmethod
    def _get_relationship(cls, location=None):
        return cls._relationship

    def get(self, location, fallback=None):
        raise NotImplementedError()

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

    def __iter__(self):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()

    def get(self, location, fallback=None):
        raise NotImplementedError()


class ComplexContainer(MyContainer):
    _relationship = BaseRelationship(types=(int, MyContainer), subtypes=True)

    def __iter__(self):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()

    def get(self, location, fallback=None):
        raise NotImplementedError()


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

    assert hash(BaseRelationship()) == hash(BaseRelationship())
    assert BaseRelationship() == BaseRelationship()
    assert BaseRelationship((str, int)) == BaseRelationship((int, str))
    assert BaseRelationship(int) != BaseRelationship(str)
    assert set(
        m for m in BaseRelationship.__members__ if not m.startswith("_")
    ).issuperset(
        BaseRelationship().to_dict()
    )


def test_inheritance():
    assert issubclass(BaseContainer, Base)
    assert issubclass(BaseContainer, SlottedContainer)
    assert issubclass(BaseContainer, SlottedSized)
    assert issubclass(BaseContainer, SlottedIterable)

    assert issubclass(BaseSemiInteractiveContainer, BaseContainer)
    assert issubclass(BaseInteractiveContainer, BaseSemiInteractiveContainer)
    assert issubclass(BaseMutableContainer, BaseInteractiveContainer)

    assert issubclass(BaseSemiInteractiveAuxiliaryContainer, BaseAuxiliaryContainer)
    assert issubclass(BaseSemiInteractiveAuxiliaryContainer, BaseSemiInteractiveContainer)
    assert issubclass(
        BaseInteractiveAuxiliaryContainer, BaseSemiInteractiveAuxiliaryContainer
    )
    assert issubclass(BaseInteractiveAuxiliaryContainer, BaseInteractiveContainer)
    assert issubclass(BaseMutableAuxiliaryContainer, BaseInteractiveAuxiliaryContainer)
    assert issubclass(BaseMutableAuxiliaryContainer, BaseMutableContainer)


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


def test_unique_descriptor():
    my_container = MyContainer(a=1, b=2)
    assert hash(my_container) == hash(my_container._state)
    assert my_container == MyContainer(a=1, b=2)
    assert hash(my_container) != hash(MyContainer(a=1, b=2, c=3))
    assert my_container != MyContainer(a=1, b=2, c=3)

    class MyUniqueContainer(MyContainer):
        hash = UniqueDescriptor()

    my_unique_container = MyUniqueContainer(a=1, b=2)
    assert my_unique_container == my_unique_container
    assert hash(my_unique_container) == id(my_unique_container)
    assert hash(my_unique_container) == my_unique_container.hash
    assert my_unique_container != MyUniqueContainer(a=1, b=2)
    assert hash(my_unique_container) != hash(MyUniqueContainer(a=1, b=2))


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
        class MyBadAuxiliaryContainer(MyAuxiliaryContainer):
            _relationship = 1

        raise AssertionError(MyBadAuxiliaryContainer)

    with pytest.raises(TypeError):
        class MyBadAuxiliaryContainer(
            with_metaclass(MyAuxiliaryContainerMeta, MyAuxiliaryContainer)
        ):
            _relationship = BaseRelationship()

        raise AssertionError(MyBadAuxiliaryContainer)

    custom_auxiliary_cls = make_auxiliary_cls(
        MyAuxiliaryContainer, MyRelationship((int, str))
    )

    assert custom_auxiliary_cls.__name__ == "IntStrMyAuxiliaryContainer"


if __name__ == "__main__":
    pytest.main()
