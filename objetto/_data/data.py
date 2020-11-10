# -*- coding: utf-8 -*-
"""Data attribute container."""

from typing import TYPE_CHECKING, cast

from six import with_metaclass, iteritems
from six.moves import collections_abc

from .._containers.container import NOTHING, BaseAttribute, ContainerMeta, Container
from .._bases import final as final_
from .bases import DataRelationship, BaseDataMeta, BaseData, BaseInteractiveData
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
    """
    Attribute descriptor for data containers.

    :param relationship: Relationship.
    :param default: Default value.
    :param default_factory: Default value factory.
    :param module: Module path for lazy types/factories.
    :param required: Whether attribute is required to have a value.
    :param final: Whether attribute is final (can't be overridden).
    :param abstract: Whether attribute is abstract (needs to be overridden).
    """

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
    """
    Data attribute container.

    :param initial: Initial values.
    """
    __slots__ = ("__hash",)

    @classmethod
    @final_
    def __make__(cls, state=ImmutableDict()):
        # type: (ImmutableDict) -> Data
        """
        Make a new data.

        :param state: Internal state.
        :return: New data.
        """
        return cast("Data", super(Data, cls).__make__(state))

    @final_
    def __init__(self, **initial):
        # type: (Any) -> None
        if type(initial) is type(self):
            self._init_state(getattr(initial, "_state"))
        else:
            self._init_state(self.__get_initial_state(dict(initial)))

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
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
            sorting=True,
            sort_key=lambda p: p[0]
        )

    @final_
    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param name: Name.
        :return: Value.
        """
        return self._state[name]

    @final_
    def __len__(self):
        # type: () -> int
        """
        Get count of attributes with values.

        :return: How many attributes with values.
        """
        return len(self._state)

    @final_
    def __iter__(self):
        # type: () -> Iterator[Tuple[str, Any]]
        """
        Iterate over name-value pairs.

        :return: Name-value pairs iterator.
        """
        for name, value in iteritems(self._state):
            yield name, value

    @final_
    def __contains__(self, pair):
        # type: (Tuple[str, Any]) -> bool
        """
        Get whether contains name-value pair.

        :param pair: Name-value pair.
        :return: True if contains.
        """
        name, value = pair
        return name in self._state and self._state[name] == value

    @classmethod
    @final_
    def __get_initial_state(
        cls,
        input_values,  # type: Mapping[str, Any]
        factory=True,  # type: bool
    ):
        # type: (...) -> ImmutableDict
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        :raises ValueError: Raised when required attributes are missing.
        """

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
                        value = attribute.fabricate_default_value()
                        initial[name] = value
                elif attribute.required:
                    missing_attributes.add(name)

        if missing_attributes:
            error = "missing value for required attribute{} {}".format(
                "s" if len(missing_attributes) != 1 else "",
                ", ".join("'{}'".format(n) for n in missing_attributes),
            )
            raise ValueError(error)

        state = ImmutableDict(initial)
        return state

    @final_
    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        try:
            return self.__hash  # type: ignore
        except AttributeError:
            cls = type(self)
            eq_state = dict(
                (n, v) for n, v in iteritems(self._state)
                if cast("DataRelationship", cls._get_relationship(n)).compared
            )
            self.__hash = hash(frozenset(iteritems(eq_state)))
            return self.__hash

    @final_
    def _eq(self, other):
        # type: (Any) -> bool
        """
        Compare with another object for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if self is other:
            return True
        cls = type(self)
        if cls is not type(other):
            return False
        eq_state = dict(
            (n, v) for n, v in iteritems(self._state)
            if cast("DataRelationship", cls._get_relationship(n)).compared
        )
        other_eq_state = dict(
            (n, v) for n, v in iteritems(other._state)
            if cast("DataRelationship", cls._get_relationship(n)).compared
        )
        return eq_state == other_eq_state

    @final_
    def _set(self, name, value):
        # type: (str, Any) -> Data
        """
        Set attribute value.

        :param name: Name.
        :param value: Value.
        :return: New version.
        """
        cls = type(self)
        value = cls._get_relationship(name).fabricate_value(value)
        return cls.__make__(self._state.set(name, value))

    @final_
    def _delete(self, name):
        # type: (str) -> Data
        """
        Delete attribute value.

        :param name: Attribute name.
        :return: New version.
        :raises AttributeError: Attribute can't be deleted or has no value.
        """
        cls = type(self)
        attribute = cls._attributes[name]
        if attribute.required:
            error = "'{}' attribute '{}' is required and cannot be deleted".format(
                cls.__fullname__, name
            )
            raise AttributeError(error)
        if name not in self._state:
            error = "'{}' attribute '{}' has no value".format(cls.__fullname__, name)
            raise AttributeError(error)
        return cls.__make__(self._state.remove(name))

    @final_
    def _update(self, update):
        # type: (Union[Mapping[str, Any], Iterable[Tuple[str, Any]]]) -> Data
        """
        Update attribute values.

        :param update: Updates.
        :return: New version.
        """
        cls = type(self)
        update = (
            (n, cls._get_relationship(n).fabricate_value(v))
            for n, v in (
                iteritems(update) if isinstance(update, collections_abc.Mapping)
                else update
            )
        )
        return cls.__make__(self._state.update(update))

    @classmethod
    @final_
    def deserialize(cls, serialized, **kwargs):
        # type: (Dict[str, Any], Any) -> Data
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
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
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized.
        """
        return dict(
            (n, self.serialize_value(v, n, **kwargs))
            for n, v in iteritems(self._state)
            if type(self)._get_relationship(n).serialized
        )

    @final_
    def get(self, name, fallback=None):
        # type: (str, Any) -> Union[Any, Any]
        """
        Get value for attribute, return fallback value if not set.

        :param name: Name.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._state.get(name, fallback)

    @property
    @final_
    def _state(self):
        # type: () -> ImmutableDict[str, Any]
        """Internal state."""
        return cast("ImmutableDict", super(Data, self)._state)


class InteractiveData(Data, BaseInteractiveData):
    """Interactive data attribute container."""
    __slots__ = ()

    @final_
    def set(self, name, value):
        # type: (str, Any) -> InteractiveData
        """
        Set attribute value.

        :param name: Name.
        :param value: Value.
        :return: New version.
        """
        return self._set(name, value)

    @final_
    def delete(self, name):
        # type: (str) -> InteractiveData
        """
        Delete attribute value.

        :param name: Attribute name.
        :return: New version.
        :raises AttributeError: Attribute can't be deleted or has no value.
        """
        return self._delete(name)

    @final_
    def update(self, update):
        # type: (Union[Mapping[str, Any], Iterable[Tuple[str, Any]]]) -> InteractiveData
        """
        Update attribute values.

        :param update: Updates.
        :return: New version.
        """
        return self._update(update)
