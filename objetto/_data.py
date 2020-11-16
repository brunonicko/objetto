# -*- coding: utf-8 -*-
"""Immutable structures."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, cast

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, string_types, with_metaclass

from ._bases import final, init_context
from ._states import DictState, ListState, SetState
from ._structures import (
    BaseAuxiliaryStructure,
    BaseAuxiliaryStructureMeta,
    BaseDictStructure,
    BaseDictStructureMeta,
    BaseInteractiveAuxiliaryStructure,
    BaseInteractiveDictStructure,
    BaseInteractiveListStructure,
    BaseInteractiveSetStructure,
    BaseInteractiveStructure,
    BaseListStructure,
    BaseListStructureMeta,
    BaseAuxiliaryStructure,
    BaseDictStructure,
    BaseListStructure,
    BaseSetStructure,
    BaseStructure,
    BaseRelationship,
    BaseSetStructure,
    BaseSetStructureMeta,
    BaseStructure,
    BaseStructureMeta,
    KeyRelationship,
)
from .utils.custom_repr import custom_iterable_repr, custom_mapping_repr

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Dict,
        Hashable,
        Iterable,
        Iterator,
        Mapping,
        Optional,
        Tuple,
        Type,
        Union,
        ItemsView,
        KeysView,
        ValuesView,
    )

    from ..utils.factoring import LazyFactory
    from ..utils.type_checking import LazyTypes

__all__ = [
    "DataRelationship",
]


_NOT_FOUND = object()


_T = TypeVar("_T")  # Any type.
_KT = TypeVar("_KT")  # Key type.
_VT = TypeVar("_VT")  # Value type.

if TYPE_CHECKING:
    AnyState = Union[DictState[_KT, _VT], ListState[_T], SetState[_T]]


@final
class DataRelationship(BaseRelationship):
    """
    Relationship between a data container and its values.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Value factory.
    :param serialized: Whether should be serialized.
    :param serializer: Custom serializer.
    :param deserializer: Custom deserializer.
    :param represented: Whether should be represented.
    :param compared: Whether the value should be leverage when comparing for equality.
    """

    __slots__ = ("__compared",)

    def __init__(
        self,
        types=(),  # type: LazyTypes
        subtypes=False,  # type: bool
        checked=True,  # type: bool
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
        serialized=True,  # type: bool
        serializer=None,  # type: LazyFactory
        deserializer=None,  # type: LazyFactory
        represented=True,  # type: bool
        compared=True,  # type: bool
    ):
        super(DataRelationship, self).__init__(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
        )
        self.__compared = bool(compared)

    @property
    def compared(self):
        # type: () -> bool
        """Whether the value should be leverage when comparing for equality."""
        return self.__compared

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        """
        dct = super(DataRelationship, self).to_dict()
        dct.update(
            {
                "compared": self.compared,
            }
        )
        return dct


class BaseDataMeta(BaseStructureMeta):
    """Metaclass for :class:`BaseData`."""

    @property  # type: ignore
    @final
    def _serializable_container_types(cls):
        # type: () -> Tuple[Type[BaseData]]
        """Serializable container types."""
        return (BaseData,)

    @property  # type: ignore
    @final
    def _serializable_structure_types(cls):
        # type: () -> Tuple[Type[BaseData]]
        """Serializable structure types."""
        return (BaseData,)

    @property  # type: ignore
    @final
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """Relationship type."""
        return DataRelationship


_BD = TypeVar("_BD", bound="BaseData")


class BaseData(with_metaclass(BaseDataMeta, BaseStructure[_T])):
    """
    Base data.

      - Is an immutable protected structure.
    """

    __slots__ = ("__state",)

    @final
    def __copy__(self):
        # type: (_BD) -> _BD
        """
        Get copy.

        :return: Copy.
        """
        return self

    @classmethod
    def __make__(cls, state):
        # type: (Type[_BD], AnyState) -> _BD
        """
        Make a new data.

        :param state: Internal state.
        :return: New data.
        """
        self = cls.__new__(cls)
        self._init_state(state)
        return self

    @final
    def _init_state(self, state):
        # type: (AnyState) -> None
        """
        Initialize internal state.

        :param state: Internal state.
        :raises RuntimeError: State already initialized.
        """
        try:
            _ = self.__state  # type: ignore
        except AttributeError:
            with init_context(self):
                self.__state = state
        else:
            error = "state already initialized"
            raise RuntimeError(error)

    @property
    def _state(self):
        # type: () -> AnyState
        """State."""
        return self.__state


class BaseInteractiveData(BaseData[_T], BaseInteractiveStructure[_T]):
    """
    Base interactive data.

      - Is an immutable interactive structure.
    """

    __slots__ = ()


class BaseAuxiliaryDataMeta(BaseDataMeta, BaseAuxiliaryStructureMeta):
    """Metaclass for :class:`BaseAuxiliaryData`."""

    @property
    @abstractmethod
    def _base_auxiliary_type(cls):
        # type: () -> Type[BaseAuxiliaryData]
        """Base auxiliary data type."""
        raise NotImplementedError()


class BaseAuxiliaryData(
    with_metaclass(
        BaseAuxiliaryDataMeta,
        BaseData[_T],
        BaseAuxiliaryStructure[_T],
    )
):
    """Base auxiliary data."""

    __slots__ = ("__hash",)

    _relationship = DataRelationship()
    """Relationship for all locations."""

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
            if not type(self)._relationship.compared:
                self.__hash = hash(id(self))
            else:
                self.__hash = hash(self._state)
            return self.__hash

    @final
    def _eq(self, other):
        # type: (Any) -> bool
        """
        Compare with another object for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if self is other:
            return True
        if not isinstance(other, collections_abc.Hashable):
            return self._state == other
        if not isinstance(other, BaseAuxiliaryData):
            return False
        self_compared = type(self)._relationship.compared
        other_compared = type(other)._relationship.compared
        if not self_compared or not other_compared:
            return False
        if isinstance(self, BaseInteractiveAuxiliaryData) != isinstance(
            other, BaseInteractiveAuxiliaryData
        ):
            return False
        self_auxiliary_type = type(self)._base_auxiliary_type  # type: ignore
        other_auxiliary_type = type(other)._base_auxiliary_type  # type: ignore
        if self_auxiliary_type is self_auxiliary_type:
            if type(self)._relationship == type(other)._relationship:
                return self._state == other._state
        return False


class BaseInteractiveAuxiliaryData(
    BaseAuxiliaryData[_T],
    BaseInteractiveData[_T],
    BaseInteractiveAuxiliaryStructure[_T],
):
    """Base interactive auxiliary data."""

    __slots__ = ()


class DictDataMeta(BaseAuxiliaryDataMeta, BaseDictStructureMeta):
    """Metaclass for :class:`DictData`."""

    @property  # type: ignore
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[DictData]
        """Base auxiliary container type."""
        return DictData


_DD = TypeVar("_DD", bound="DictData")


class DictData(
    with_metaclass(
        DictDataMeta,
        BaseDictStructure[_KT, _VT],
        BaseAuxiliaryData[_KT],
    )
):
    """
    Dictionary data.

    :param initial: Initial values.
    """

    __slots__ = ()
    _key_relationship = KeyRelationship()
    """Relationship for dictionary keys."""

    @classmethod
    @final
    def __make__(cls, state=DictState()):
        # type: (Type[_DD], AnyState) -> _DD
        """
        Make a new dictionary data.

        :param state: Internal state.
        :return: New dictionary data.
        """
        return super(DictData, cls).__make__(state)

    @final
    def __init__(self, initial=()):
        # type: (Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> None
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
        if type(self)._relationship.represented:
            return custom_mapping_repr(
                self._state,
                prefix="{}({{".format(type(self).__fullname__),
                suffix="})",
            )
        else:
            return "<{}>".format(type(self).__fullname__)

    @final
    def __reversed__(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        """
        return reversed(list(self.__iter__()))

    @final
    def __getitem__(self, key):
        # type: (_KT) -> _VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Invalid key.
        """
        return self._state[key]

    @final
    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key in self._state:
            yield key

    @final
    def __contains__(self, key):
        # type: (Any) -> bool
        """
        Get whether key is present.

        :param key: Key.
        :return: True if contains.
        """
        return key in self._state

    @classmethod
    @final
    def __get_initial_state(cls, input_values, factory=True):
        # type: (Mapping, bool) -> DictState
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        if not cls._key_relationship.passthrough or not cls._relationship.passthrough:
            state = DictState(
                (
                    cls._key_relationship.fabricate_key(k, factory=factory),
                    cls._relationship.fabricate_value(v, factory=factory),
                )
                for k, v in iteritems(input_values)
            )
        else:
            state = DictState(input_values)
        return state

    @final
    def _clear(self):
        # type: (_DD) -> _DD
        """
        Clear all keys and values.

        :return: New version.
        """
        return type(self).__make__()

    @final
    def _set(self, key, value):
        # type: (_DD, _KT, _VT) -> _DD
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: New version.
        """
        cls = type(self)
        key = cls._key_relationship.fabricate_key(key)
        value = cls._relationship.fabricate_value(value)
        return cls.__make__(self._state.set(key, value))

    @final
    def _discard(self, key):
        # type: (_DD, _KT) -> _DD
        """
        Discard key if it exists.

        :param key: Key.
        :return: New version.
        """
        return type(self).__make__(self._state.discard(key))

    @final
    def _remove(self, key):
        # type: (_DD, _KT) -> _DD
        """
        Delete existing key.

        :param key: Key.
        :return: New version.
        """
        return type(self).__make__(self._state.remove(key))

    @final
    def _update(self, update):
        # type: (_DD, Union[Mapping[_KT, _VT], Iterable[Tuple[_KT, _VT]]]) -> _DD
        """
        Update keys and values.

        :param update: Updates.
        :return: New version.
        """
        cls = type(self)
        if not cls._key_relationship.passthrough or not cls._relationship.passthrough:
            update = (
                (
                    cls._key_relationship.fabricate_key(k),
                    cls._relationship.fabricate_value(v),
                )
                for k, v in (
                    iteritems(update)
                    if isinstance(update, collections_abc.Mapping)
                    else update
                )
            )
        return cls.__make__(self._state.update(update))

    @final
    def get(self, key, fallback=None):
        # type: (_KT, Any) -> Union[_VT, Any]
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._state.get(key, fallback)

    @final
    def iteritems(self):
        # type: () -> Iterator[Tuple[_KT, _VT]]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key, value in self._state.iteritems():
            yield key, value

    @final
    def iterkeys(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in self._state.iterkeys():
            yield key

    @final
    def itervalues(self):
        # type: () -> Iterator[_VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in self._state.itervalues():
            yield value

    @final
    def items(self):
        # type: () -> ItemsView[_KT, _VT]
        """
        Get items.

        :return: Items.
        """
        return collections_abc.ItemsView(self)

    @final
    def keys(self):
        # type: () -> KeysView[_KT]
        """
        Get keys.

        :return: Keys.
        """
        return collections_abc.KeysView(self)

    @final
    def values(self):
        # type: () -> ValuesView[_VT]
        """
        Get values.

        :return: Values.
        """
        return collections_abc.ValuesView(self)

    @final
    def find_with_attributes(self, **attributes):
        # type: (Any) -> _VT
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        if not attributes:
            error = "no attributes provided"
            raise ValueError(error)
        for value in self.itervalues():
            for a_name, a_value in iteritems(attributes):
                if not hasattr(value, a_name) or getattr(value, a_name) != a_value:
                    break
            else:
                return value
        error = "could not find a match for {}".format(
            custom_mapping_repr(
                attributes,
                prefix="(",
                template="{key}={value}",
                suffix=")",
                key_repr=str,
            ),
        )
        raise ValueError(error)

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Type[_DD], Dict, Any) -> _DD
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise RuntimeError(error)
        state = DictState(
            (
                cls._key_relationship.fabricate_key(k, factory=False),
                cls.deserialize_value(v, location=None, **kwargs),
            )
            for k, v in iteritems(serialized)
        )
        return cls.__make__(state)

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> Dict
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized.
        """
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise RuntimeError(error)
        return dict(
            (k, self.serialize_value(v, location=None, **kwargs))
            for k, v in iteritems(self._state)
        )

    @property  # type: ignore
    @final
    def _state(self):
        # type: () -> DictState[_KT, _VT]
        """Internal state."""
        return cast("DictState", super(DictData, self)._state)


class InteractiveDictData(
    DictData[_KT, _VT],
    BaseInteractiveDictStructure[_KT, _VT],
    BaseInteractiveAuxiliaryData[_KT],
):
    """Interactive dictionary data."""
    
    __slots__ = ()
