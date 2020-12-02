# -*- coding: utf-8 -*-
"""Data with state curated by attribute descriptors."""

from typing import TYPE_CHECKING, TypeVar, cast, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, string_types, with_metaclass

from .._bases import MISSING, final
from .._states import BaseState, DictState
from .._structures import (
    BaseAttribute,
    BaseAttributeMeta,
    BaseAttributeStructure,
    BaseAttributeStructureMeta,
    BaseInteractiveAttributeStructure,
    BaseRelationship,
)
from ..utils.type_checking import assert_is_instance
from .bases import BaseData, BaseDataMeta, BaseInteractiveData, DataRelationship

if TYPE_CHECKING:
    from typing import Any, Dict, Iterable, Mapping, Optional, Set, Tuple, Type

    from ..utils.factoring import LazyFactory

__all__ = ["DataAttribute", "Data", "InteractiveData"]


T = TypeVar("T")  # Any type.


class DataAttributeMeta(BaseAttributeMeta):
    """Metaclass for :class:`DataAttribute`."""

    @property
    @final
    def _relationship_type(cls):
        # type: () -> Type[DataRelationship]
        """Relationship type."""
        return DataRelationship


@final
class DataAttribute(with_metaclass(DataAttributeMeta, BaseAttribute[T])):
    """
    Data attribute descriptor.

    :param relationship: Relationship.
    :param default: Default value.
    :param default_factory: Default value factory.
    :param module: Optional module path to use in case partial paths are provided.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    """

    __slots__ = ()

    def __init__(
        self,
        relationship=BaseRelationship(),  # type: BaseRelationship
        default=MISSING,  # type: Any
        default_factory=None,  # type: LazyFactory
        module=None,  # type: Optional[str]
        required=True,  # type: bool
        changeable=True,  # type: bool
        deletable=False,  # type: bool
        finalized=False,  # type: bool
        abstracted=False,  # type: bool
    ):
        # type: (...) -> None
        super(DataAttribute, self).__init__(
            relationship=relationship,
            default=default,
            default_factory=default_factory,
            module=module,
            required=required,
            changeable=changeable,
            deletable=deletable,
            finalized=finalized,
            abstracted=abstracted,
        )

    @property
    def relationship(self):
        # type: () -> DataRelationship
        """Relationship."""
        return cast("DataRelationship", super(DataAttribute, self).relationship)


class DataMeta(BaseAttributeStructureMeta, BaseDataMeta):
    """Metaclass for :class:`Data`."""

    @property
    @final
    def _attribute_type(cls):
        # type: () -> Type[DataAttribute]
        """Attribute type."""
        return DataAttribute

    @property
    @final
    def _attributes(cls):
        # type: () -> Mapping[str, DataAttribute]
        """Attributes mapped by name."""
        return cast("Mapping[str, DataAttribute]", super(DataMeta, cls)._attributes)

    @property
    @final
    def _attribute_names(cls):
        # type: () -> Mapping[DataAttribute, str]
        """Names mapped by attribute."""
        return cast(
            "Mapping[DataAttribute, str]", super(DataMeta, cls)._attribute_names
        )


# noinspection PyTypeChecker
_D = TypeVar("_D", bound="Data")


class Data(with_metaclass(DataMeta, BaseAttributeStructure, BaseData[str])):
    """
    Data.

    :param initial: Initial values.
    """

    __slots__ = ("__hash",)

    @classmethod
    @final
    def __make__(cls, state=DictState()):
        # type: (Type[_D], BaseState) -> _D
        """
        Make a new data.

        :param state: Internal state.
        :return: New data.
        """
        return super(Data, cls).__make__(state)

    @final
    def __init__(self, **initial):
        # type: (Any) -> None
        state = self.__get_initial_state(initial)
        self._init_state(state)

    @classmethod
    @final
    def __get_initial_state(
        cls,
        input_values,  # type: Mapping[str, Any]
        factory=True,  # type: bool
    ):
        # type: (...) -> DictState[str, Any]
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        initial = {}

        for name, value in iteritems(input_values):
            attribute = cls._get_attribute(name)
            initial[name] = attribute.relationship.fabricate_value(
                value, factory=factory
            )

        missing_attributes = set()  # type: Set[str]
        for name, attribute in iteritems(cls._attributes):
            if name not in initial:
                if attribute.has_default:
                    if not missing_attributes:
                        initial[name] = attribute.fabricate_default_value()
                elif attribute.required:
                    missing_attributes.add(name)

        if missing_attributes:
            error = "missing required attribute{} {}".format(
                "s" if len(missing_attributes) != 1 else "",
                ", ".join("'{}'".format(n) for n in missing_attributes),
            )
            raise TypeError(error)

        return DictState(initial)

    @classmethod
    @final
    def _get_relationship(cls, location):
        # type: (str) -> DataRelationship
        """
        Get relationship at location (attribute name).

        :param location: Location (attribute name).
        :return: Relationship.
        :raises KeyError: Attribute does not exist.
        """
        return cast("DataRelationship", cls._get_attribute(location).relationship)

    @classmethod
    @final
    def _get_attribute(cls, name):
        # type: (str) -> DataAttribute
        """
        Get attribute by name.

        :param name: Attribute name.
        :return: Attribute.
        :raises KeyError: Attribute does not exist.
        """
        return cast("DataAttribute", cls._attributes[name])

    @final
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
            comparable_attributes = set(
                n for n, a in iteritems(cls._attributes) if a.relationship.compared
            )
            if not comparable_attributes:
                return hash(id(self))
            comparable_state = dict(
                (n, v) for n, v in iteritems(self._state) if n in comparable_attributes
            )
            self.__hash = hash(frozenset(iteritems(comparable_state)))
            return self.__hash

    @final
    def _eq(self, other):
        # type: (Any) -> bool
        """
        Compare with another data for equality.

        :param other: Another data.
        :return: True if equal.
        """
        if self is other:
            return True
        cls = type(self)
        comparable_attributes = set(
            n for n, a in iteritems(cls._attributes) if a.relationship.compared
        )
        if not comparable_attributes:
            return False
        comparable_state = dict(
            (n, v)
            for n, v in iteritems(self._state)
            if cls._get_relationship(n).compared
        )
        if not isinstance(other, collections_abc.Hashable):
            return comparable_state == other
        if not isinstance(other, Data):
            return False
        if type(self) is not type(other):
            return False
        other_comparable_state = dict(
            (n, v)
            for n, v in iteritems(other._state)
            if cls._get_relationship(n).compared
        )
        return comparable_state == other_comparable_state

    @final
    def _clear(self):
        # type: (_D) -> _D
        """
        Clear deletable attribute values.

        :return: Transformed.
        :raises AttributeError: No deletable attributes.
        """
        cls = type(self)
        state = self._state
        has_deletable_attributes = False
        for name in self._state:
            attribute = cls._get_attribute(name)
            if attribute.deletable:
                has_deletable_attributes = True
                state = state.remove(name)
        if not has_deletable_attributes:
            error = "'{}' has no deletable attributes".format(type(self).__fullname__)
            raise AttributeError(error)
        if state is self._state:
            return self
        else:
            return type(self).__make__(state)

    @final
    def _set(self, name, value):
        # type: (_D, str, Any) -> _D
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        cls = type(self)
        attribute = cls._get_attribute(name)
        if not attribute.changeable and name in self._state:
            error = "non-changeable attribute '{}' already has a value".format(name)
            raise AttributeError(error)
        fabricated_value = attribute.relationship.fabricate_value(value)
        return type(self).__make__(self._state.set(name, fabricated_value))

    @final
    def _delete(self, name):
        # type: (_D, str) -> _D
        """
        Delete attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises KeyError: Attribute does not exist or has no value.
        :raises AttributeError: Attribute is not deletable.
        """
        cls = type(self)
        attribute = cls._get_attribute(name)
        if not attribute.deletable and name in self._state:
            error = "attribute '{}' is not deletable".format(name)
            raise AttributeError(error)
        return type(self).__make__(self._state.remove(name))

    @overload
    def _update(self, __m, **kwargs):
        # type: (_D, Mapping[str, Any], Any) -> _D
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (_D, Iterable[Tuple[str, Any]], Any) -> _D
        pass

    @overload
    def _update(self, **kwargs):
        # type: (_D, Any) -> _D
        pass

    @final
    def _update(self, *args, **kwargs):
        """
        Update multiple attribute values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        :rtype: objetto.data.ProtectedData

        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        update = dict(*args, **kwargs)
        cls = type(self)
        fabricated_update = {}
        for name, value in iteritems(update):
            assert_is_instance(name, string_types)
            attribute = cls._get_attribute(name)
            if not attribute.changeable and name in self._state:
                error = "non-changeable attribute '{}' already has a value".format(name)
                raise AttributeError(error)
            fabricated_value = attribute.relationship.fabricate_value(value)
            fabricated_update[name] = fabricated_value
        return cls.__make__(self._state.update(fabricated_update))

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Type[_D], Dict, Any) -> _D
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        input_values = dict(
            (n, cls.deserialize_value(v, n, **kwargs)) for n, v in iteritems(serialized)
        )
        state = cls.__get_initial_state(input_values, factory=False)
        return cls.__make__(state)

    @final
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

    @property
    @final
    def _state(self):
        # type: () -> DictState[str, Any]
        """Internal state."""
        return cast("DictState", super(BaseAttributeStructure, self)._state)


class InteractiveData(
    Data, BaseInteractiveAttributeStructure, BaseInteractiveData[str]
):
    """Interactive data."""

    __slots__ = ()
