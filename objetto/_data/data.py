# -*- coding: utf-8 -*-
"""Data attribute container."""

from typing import TYPE_CHECKING, cast

from six import with_metaclass, iteritems
from six.moves import collections_abc

from .._containers.container import NOTHING, BaseAttribute, ContainerMeta, Container
from .._bases import init_context
from .._bases import final as final_
from .base import DataRelationship, BaseDataMeta, BaseData
from ..utils.custom_repr import custom_mapping_repr
from ..utils.immutable import ImmutableDict

if TYPE_CHECKING:
    from typing import (
        Any,
        Optional,
        Type,
        Iterator,
        Tuple,
        Mapping,
        Dict,
        Union,
        Iterable,
        Set,
    )

    from ..utils.factoring import LazyFactory

__all__ = ["DataAttribute", "DataMeta", "Data", "InteractiveData"]


class DataAttribute(BaseAttribute):
    __slots__ = ()

    def __init__(
        self,
        relationship=DataRelationship(),  # type: DataRelationship
        default=NOTHING,  # type: Any
        default_factory=None,  # type: LazyFactory
        module=None,  # type: Optional[str]
        required=True,  # type: bool
        final=False,  # type: bool
        abstract=False,  # type: bool
    ):
        super(DataAttribute, self).__init__(
            relationship=relationship,
            default=default,
            default_factory=default_factory,
            module=module,
            required=required,
            final=final,
            abstract=abstract,
        )


class DataMeta(BaseDataMeta, ContainerMeta):
    """Metaclass for :class:`Container`."""

    @property
    @final_
    def _attribute_type(cls):
        # type: () -> Type[DataAttribute]
        """Attribute type."""
        return DataAttribute


class Data(with_metaclass(DataMeta, BaseData, Container)):
    """Data attribute container."""
    __slots__ = ("__state",)

    @classmethod
    @final_
    def __make__(cls, state=ImmutableDict()):
        # type: (Any) -> Data
        self = cast("Data", cls.__new__(cls))
        with init_context(self):
            self.__state = state
        return self

    @final_
    def __init__(self, **initial):
        # type: (Any) -> None
        self.__state = self.__get_initial_state(initial)

    def __repr__(self):
        # type: () -> str
        """Get representation."""
        return custom_mapping_repr(
            dict(
                (n, v)
                for n, v in iteritems(self._state)
                if type(self)._get_relationship(n).represented
            ),
            prefix="{}(".format(type(self).__fullname__),
            template="{key}={value}",
            suffix=")",
            key_repr=str,
        )

    def __getitem__(self, name):
        # type: (str) -> Any
        return self._state[name]

    def __len__(self):
        # type: () -> int
        return len(self._state)

    def __iter__(self):
        # type: () -> Iterator[Tuple[str, Any]]
        for name, value in iteritems(self._state):
            yield name, value

    @classmethod
    @final_
    def __get_initial_state(
        cls,
        input_values,  # type: Mapping[str, Any]
        factory=True,  # type: bool
    ):
        # type: (...) -> ImmutableDict
        """Get initial state."""

        initial = {}
        for name, value in iteritems(input_values):
            attribute = cls._attributes[name]
            initial[name] = attribute.relationship.fabricate_value(
                value, factory=factory
            )

        missing_attributes = set()  # type: Set[str]
        for name, attribute in iteritems(cls._attributes):
            if name not in initial:
                if attribute.has_default:
                    if not missing_attributes:
                        initial[name] = attribute.fabricate_default_value(
                            factory=factory
                        )
                elif attribute.required:
                    missing_attributes.add(name)

        if missing_attributes:
            error = "missing value for required attribute{} {}".format(
                "s" if len(missing_attributes) != 1 else "",
                ", ".join("'{}'".format(n) for n in missing_attributes),
            )
            raise TypeError(error)

        state = ImmutableDict(initial)
        return state

    @classmethod
    @final_
    def _get_relationship(cls, location=None):
        # type: (str) -> DataRelationship
        """Get relationship for attribute name."""
        return cls._attributes[location].relationship

    @classmethod
    @final_
    def deserialize(cls, serialized, **kwargs):
        # type: (Dict[str, Any], Any) -> Data
        """Deserialize."""
        input_values = dict(
            (n, cls.deserialize_value(v, n, **kwargs))
            for n, v in iteritems(serialized)
            if cls._get_relationship(n).serialized
        )
        state = cls.__get_initial_state(input_values, factory=False)
        return cls.__make__(state)

    @final_
    def serialize(self, **kwargs):
        # type: (Any) -> Dict[str, Any]
        """Serialize."""
        return dict(
            (n, self.serialize_value(v, n, **kwargs))
            for n, v in iteritems(self._state)
            if type(self)._get_relationship(n).serialized
        )

    def get(self, name, fallback=None):
        # type: (str, Any) -> Union[Any, Any]
        return self._state.get(name, fallback=fallback)

    def _set(self, name, value):
        # type: (str, Any) -> Data
        cls = type(self)
        value = cls._get_relationship(name).fabricate_value(value)
        return cls.__make__(self._state.set(name, value))

    def _update(self, update):
        # type: (Union[Mapping[str, Any], Iterable[Tuple[str, Any]]]) -> Data
        cls = type(self)
        update = (
            (n, cls._get_relationship(n).fabricate_value(v))
            for n, v in (
                iteritems(update) if isinstance(update, collections_abc.Mapping)
                else update
            )
        )
        return cls.__make__(self._state.update(update))

    @property
    @final_
    def _state(self):
        # type: () -> ImmutableDict[str, Any]
        """Internal state."""
        return self.__state


class InteractiveData(Data):
    """Interactive data attribute container."""
    __slots__ = ()

    def set(self, name, value):
        # type: (str, Any) -> InteractiveData
        return self._set(name, value)

    def update(self, update):
        # type: (Union[Mapping[str, Any], Iterable[Tuple[str, Any]]]) -> InteractiveData
        return self._update(update)
