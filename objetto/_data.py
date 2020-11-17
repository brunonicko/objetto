# -*- coding: utf-8 -*-
"""Immutable structures."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, cast, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import (
    iteritems, iterkeys, itervalues, with_metaclass, string_types
)

from ._bases import final, init_context
from ._states import DictState, ListState, SetState
from ._structures import (
    MISSING,
    BaseAuxiliaryStructure,
    BaseAuxiliaryStructureMeta,
    BaseDictStructure,
    BaseDictStructureMeta,
    BaseAttributeMeta,
    BaseAttribute,
    BaseAttributeStructureMeta,
    BaseAttributeStructure,
    BaseInteractiveAttributeStructure,
    BaseInteractiveAuxiliaryStructure,
    BaseInteractiveDictStructure,
    BaseInteractiveListStructure,
    BaseInteractiveSetStructure,
    BaseInteractiveStructure,
    BaseListStructure,
    BaseListStructureMeta,
    BaseRelationship,
    BaseSetStructure,
    BaseSetStructureMeta,
    BaseStructure,
    BaseStructureMeta,
    KeyRelationship,
)
from .utils.custom_repr import custom_iterable_repr, custom_mapping_repr
from .utils.type_checking import assert_is_instance

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        Hashable,
        ItemsView,
        Iterable,
        Iterator,
        KeysView,
        List,
        Mapping,
        Optional,
        Tuple,
        Type,
        Set,
        Union,
        ValuesView,
    )

    from .utils.factoring import LazyFactory
    from .utils.type_checking import LazyTypes

__all__ = [
    "DataRelationship",
    "BaseDataMeta",
    "BaseData",
    "BaseInteractiveData",
    "DataAttributeMeta",
    "DataAttribute",
    "DataMeta",
    "Data",
    "InteractiveData",
    "BaseAuxiliaryDataMeta",
    "BaseAuxiliaryData",
    "BaseInteractiveAuxiliaryData",
    "DictDataMeta",
    "DictData",
    "InteractiveDictData",
    "ListDataMeta",
    "ListData",
    "InteractiveListData",
    "SetDataMeta",
    "SetData",
    "InteractiveSetData",
]


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

    @property
    @final
    def _serializable_container_types(cls):
        # type: () -> Tuple[Type[BaseData]]
        """Serializable container types."""
        return (BaseData,)

    @property
    @final
    def _serializable_structure_types(cls):
        # type: () -> Tuple[Type[BaseData]]
        """Serializable structure types."""
        return (BaseData,)

    @property
    @final
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """Relationship type."""
        return DataRelationship


# noinspection PyTypeChecker
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
        self = cast("_BD", cls.__new__(cls))
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
    @abstractmethod
    def _state(self):
        # type: () -> AnyState
        """State."""
        return self.__state


# noinspection PyAbstractClass
class BaseInteractiveData(BaseData[_T], BaseInteractiveStructure[_T]):
    """
    Base interactive data.

      - Is an immutable interactive structure.
    """

    __slots__ = ()


class DataAttributeMeta(BaseAttributeMeta):
    """Metaclass for :class:`DataAttribute`."""

    @property
    @final
    def _relationship_type(cls):
        # type: () -> Type[DataRelationship]
        """Relationship type."""
        return DataRelationship


@final
class DataAttribute(with_metaclass(DataAttributeMeta, BaseAttribute)):
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
    :raises ValueError: Specified both `default` and `default_factory`.
    :raises ValueError: Both `required` and `deletable` are True.
    :raises ValueError: Both `finalized` and `abstracted` are True.
    """

    __slots__ = ()

    def __init__(
        self,
        relationship=DataRelationship(),  # type: DataRelationship
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
        return cast(DataRelationship, super(DataAttribute, self).relationship)


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
        # type: (Type[_D], AnyState) -> _D
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
        )

    @final
    def __reversed__(self):
        # type: () -> Iterator[str]
        """
        Iterate over reversed attribute names.

        :return: Reversed attribute names iterator.
        """
        return reversed(list(self.__iter__()))

    @final
    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get value for attribute name.

        :param name: Attribute name.
        :return: Value.
        :raises KeyError: Attribute does not exist or has no value.
        """
        return self._state[name]

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
        # type: () -> Iterator[str]
        """
        Iterate over names of attributes with value.

        :return: Names of attributes with value.
        """
        for name in self._state:
            yield name

    @final
    def __contains__(self, name):
        # type: (Any) -> bool
        """
        Get whether attribute name is valid and has a value.

        :param name: Attribute name.
        :return: True if attribute name is valid and has a value.
        """
        return name in self._state

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
        if type(self) is not type(other):
            return False
        cls = type(self)
        comparable_attributes = set(
            n for n, a in iteritems(cls._attributes) if a.relationship.compared
        )
        if not comparable_attributes:
            return False
        comparable_state = dict(
            (n, v) for n, v in iteritems(self._state)
            if cls._get_relationship(n).compared
        )
        other_comparable_state = dict(
            (n, v) for n, v in iteritems(other._state)
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

    @final
    def keys(self):
        # type: () -> SetState[str]
        """
        Get names of the attributes with values.

        :return: Attribute names.
        """
        return SetState(self._state.keys())

    @final
    def find_with_attributes(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        return self._state.find_with_attributes(**attributes)

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
        return cast("DictState", super(Data, self)._state)


class InteractiveData(
    Data, BaseInteractiveAttributeStructure, BaseInteractiveData[str]
):
    """Interactive data."""
    __slots__ = ()


class BaseAuxiliaryDataMeta(BaseDataMeta, BaseAuxiliaryStructureMeta):
    """Metaclass for :class:`BaseAuxiliaryData`."""

    @property
    @abstractmethod
    def _base_auxiliary_type(cls):
        # type: () -> Type[BaseAuxiliaryData]
        """Base auxiliary data type."""
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseAuxiliaryData(
    with_metaclass(
        BaseAuxiliaryDataMeta,
        BaseAuxiliaryStructure[_T],
        BaseData[_T],
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
        self_auxiliary_type = type(self)._base_auxiliary_type
        other_auxiliary_type = type(other)._base_auxiliary_type
        if self_auxiliary_type is other_auxiliary_type:
            if type(self)._relationship == type(other)._relationship:
                return self._state == other._state
        return False


# noinspection PyAbstractClass
class BaseInteractiveAuxiliaryData(
    BaseAuxiliaryData[_T],
    BaseInteractiveData[_T],
    BaseInteractiveAuxiliaryStructure[_T],
):
    """Base interactive auxiliary data."""

    __slots__ = ()


class DictDataMeta(BaseAuxiliaryDataMeta, BaseDictStructureMeta):
    """Metaclass for :class:`DictData`."""

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[DictData]
        """Base auxiliary container type."""
        return DictData


# noinspection PyTypeChecker
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
        # type: (Mapping[_KT, _VT], bool) -> DictState[_KT, _VT]
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

        :return: Transformed.
        """
        return type(self).__make__()

    @final
    def _set(self, key, value):
        # type: (_DD, _KT, _VT) -> _DD
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
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
        :return: Transformed.
        """
        return type(self).__make__(self._state.discard(key))

    @final
    def _remove(self, key):
        # type: (_DD, _KT) -> _DD
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        """
        return type(self).__make__(self._state.remove(key))

    @overload
    def _update(self, __m, **kwargs):
        # type: (_DD, Mapping[_KT, _VT], _VT) -> _DD
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (_DD, Iterable[Tuple[_KT, _VT]], _VT) -> _DD
        pass

    @overload
    def _update(self, **kwargs):
        # type: (_DD, _VT) -> _DD
        pass

    @final
    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.
        """
        update = dict(*args, **kwargs)
        cls = type(self)
        if not cls._key_relationship.passthrough or not cls._relationship.passthrough:
            fabricated_update = (
                (
                    cls._key_relationship.fabricate_key(k),
                    cls._relationship.fabricate_value(v),
                )
                for k, v in iteritems(update)
            )
            return cls.__make__(self._state.update(fabricated_update))
        else:
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
        for key, value in iteritems(self._state):
            yield key, value

    @final
    def iterkeys(self):
        # type: () -> Iterator[_KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in iterkeys(self._state):
            yield key

    @final
    def itervalues(self):
        # type: () -> Iterator[_VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in itervalues(self._state):
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
        return self._state.find_with_attributes(**attributes)

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Type[_DD], Dict, Any) -> _DD
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        :raises RuntimeError: Not deserializable.
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
        :raises RuntimeError: Not serializable.
        """
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise RuntimeError(error)
        return dict(
            (k, self.serialize_value(v, location=None, **kwargs))
            for k, v in iteritems(self._state)
        )

    @property
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


class ListDataMeta(BaseAuxiliaryDataMeta, BaseListStructureMeta):
    """Metaclass for :class:`ListData`."""

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[ListData]
        """Base auxiliary container type."""
        return ListData


# noinspection PyTypeChecker
_LD = TypeVar("_LD", bound="ListData")


class ListData(
    with_metaclass(
        ListDataMeta,
        BaseListStructure[_T],
        BaseAuxiliaryData[_T],
    )
):
    """
    List data.

    :param initial: Initial values.
    """

    __slots__ = ()

    @classmethod
    @final
    def __make__(cls, state=ListState()):
        # type: (Type[_LD], AnyState) -> _LD
        """
        Make a new list data.

        :param state: Internal state.
        :return: New dictionary data.
        """
        return super(ListData, cls).__make__(state)

    @final
    def __init__(self, initial=()):
        # type: (Iterable[_T]) -> None
        if type(initial) is type(self):
            self._init_state(getattr(initial, "_state"))
        else:
            self._init_state(self.__get_initial_state(initial))

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        if type(self)._relationship.represented:
            return custom_iterable_repr(
                self._state,
                prefix="{}([".format(type(self).__fullname__),
                suffix="])",
            )
        else:
            return "<{}>".format(type(self).__fullname__)

    @final
    def __reversed__(self):
        # type: () -> Iterator[_T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._state)

    @overload
    def __getitem__(self, index):
        # type: (int) -> _T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> ListState[_T]
        pass

    @final
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        return self._state[index]

    @final
    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[_T]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in self._state:
            yield value

    @final
    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :return: True if contains.
        """
        return value in self._state

    @classmethod
    @final
    def __get_initial_state(cls, input_values, factory=True):
        # type: (Iterable[_T], bool) -> ListState[_T]
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        if not cls._relationship.passthrough:
            state = ListState(
                cls._relationship.fabricate_value(v, factory=factory)
                for v in input_values
            )
        else:
            state = ListState(input_values)
        return state

    @final
    def _clear(self):
        # type: (_LD) -> _LD
        """
        Clear all values.

        :return: Transformed.
        """
        return type(self).__make__()

    @final
    def _insert(self, index, *values):
        # type: (_LD, int, _T) -> _LD
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            fabricated_values = (cls._relationship.fabricate_value(v) for v in values)
            return type(self).__make__(self._state.insert(index, *fabricated_values))
        else:
            return type(self).__make__(self._state.insert(index, *values))

    @final
    def _append(self, value):
        # type: (_LD, _T) -> _LD
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        cls = type(self)
        fabricated_value = cls._relationship.fabricate_value(value)
        return type(self).__make__(self._state.append(fabricated_value))

    @final
    def _extend(self, iterable):
        # type: (_LD, Iterable[_T]) -> _LD
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            fabricated_iterable = (
                cls._relationship.fabricate_value(v) for v in iterable
            )
            return type(self).__make__(self._state.extend(fabricated_iterable))
        else:
            return type(self).__make__(self._state.extend(iterable))

    @final
    def _remove(self, value):
        # type: (_LD, _T) -> _LD
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return type(self).__make__(self._state.remove(value))

    @final
    def _reverse(self):
        # type: (_LD) -> _LD
        """
        Reverse values.

        :return: Transformed.
        """
        return type(self).__make__(self._state.reverse())

    @final
    def _move(self, item, target_index):
        # type: (_LD, Union[slice, int], int) -> _LD
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        return type(self).__make__(self._state.move(item, target_index))

    @final
    def _change(self, index, *values):
        # type: (_LD, int, _T) -> _LD
        """
        Change value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            fabricated_values = (cls._relationship.fabricate_value(v) for v in values)
            return type(self).__make__(self._state.change(index, *fabricated_values))
        else:
            return type(self).__make__(self._state.change(index, *values))

    @final
    def count(self, value):
        # type: (Any) -> int
        """
        Count number of occurrences of a value.

        :return: Number of occurrences.
        """
        return self._state.count(value)

    @final
    def index(self, value, start=None, stop=None):
        # type: (Any, Optional[int], Optional[int]) -> int
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :return: Index of value.
        :raises ValueError: Provided stop but did not provide start.
        """
        return self._state.index(value, start=start, stop=stop)

    @final
    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return self._state.resolve_index(index, clamp=clamp)

    @final
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return self._state.resolve_continuous_slice(slc)

    @final
    def find_with_attributes(self, **attributes):
        # type: (Any) -> _T
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        return self._state.find_with_attributes(**attributes)

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Type[_LD], List, Any) -> _LD
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        :raises RuntimeError: Not deserializable.
        """
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise RuntimeError(error)
        state = ListState(
            cls.deserialize_value(v, location=None, **kwargs) for v in serialized
        )
        return cls.__make__(state)

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> List
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized.
        :raises RuntimeError: Not serializable.
        """
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise RuntimeError(error)
        return list(
            self.serialize_value(v, location=None, **kwargs) for v in self._state
        )

    @property
    @final
    def _state(self):
        # type: () -> ListState[_T]
        """Internal state."""
        return cast("ListState", super(ListData, self)._state)


class InteractiveListData(
    ListData[_T],
    BaseInteractiveListStructure[_T],
    BaseInteractiveAuxiliaryData[_T],
):
    """Interactive list data."""

    __slots__ = ()


class SetDataMeta(BaseAuxiliaryDataMeta, BaseSetStructureMeta):
    """Metaclass for :class:`SetData`."""

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[SetData]
        """Base auxiliary container type."""
        return SetData


# noinspection PyTypeChecker
_SD = TypeVar("_SD", bound="SetData")


class SetData(
    with_metaclass(
        SetDataMeta,
        BaseSetStructure[_T],
        BaseAuxiliaryData[_T],
    )
):
    """
    Set data.

    :param initial: Initial values.
    """

    __slots__ = ()

    @classmethod
    @final
    def __make__(cls, state=SetState()):
        # type: (Type[_SD], AnyState) -> _SD
        """
        Make a new set data.

        :param state: Internal state.
        :return: New dictionary data.
        """
        return super(SetData, cls).__make__(state)

    @final
    def __init__(self, initial=()):
        # type: (Iterable[_T]) -> None
        if type(initial) is type(self):
            self._init_state(getattr(initial, "_state"))
        else:
            self._init_state(self.__get_initial_state(initial))

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        if type(self)._relationship.represented:
            return custom_iterable_repr(
                self._state,
                prefix="{}([".format(type(self).__fullname__),
                suffix="])",
                sorting=True,
                sort_key=lambda v: hash(v),
            )
        else:
            return "<{}>".format(type(self).__fullname__)

    @final
    def __reversed__(self):
        # type: () -> Iterator[_T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(list(self._state))

    @final
    def __len__(self):
        # type: () -> int
        """
        Get value count.

        :return: Value count.
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[_T]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in self._state:
            yield value

    @final
    def __contains__(self, value):
        # type: (Any) -> bool
        """
        Get whether value is present.

        :param value: Value.
        :return: True if contains.
        """
        return value in self._state

    @classmethod
    @final
    def __get_initial_state(cls, input_values, factory=True):
        # type: (Iterable[_T], bool) -> SetState[_T]
        """
        Get initial state.

        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial state.
        """
        if not cls._relationship.passthrough:
            state = SetState(
                cls._relationship.fabricate_value(v, factory=factory)
                for v in input_values
            )
        else:
            state = SetState(input_values)
        return state

    @final
    def _clear(self):
        # type: (_SD) -> _SD
        """
        Clear all values.

        :return: Transformed.
        """
        return type(self).__make__()

    @final
    def _add(self, value):
        # type: (_SD, _T) -> _SD
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        cls = type(self)
        fabricated_value = cls._relationship.fabricate_value(value)
        return type(self).__make__(self._state.add(fabricated_value))

    @final
    def _discard(self, value):
        # type: (_SD, _T) -> _SD
        """
        Discard value if it exists.

        :param value: Value.
        :return: Transformed.
        """
        return type(self).__make__(self._state.discard(value))

    @final
    def _remove(self, *values):
        # type: (_SD, _T) -> _SD
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        return type(self).__make__(self._state.remove(*values))

    @final
    def _replace(self, value, new_value):
        # type: (_SD, _T, _T) -> _SD
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :param new_value: New value.
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        cls = type(self)
        fabricated_new_value = cls._relationship.fabricate_value(new_value)
        return type(self).__make__(self._state.remove(value).add(fabricated_new_value))

    @final
    def _update(self, iterable):
        # type: (_SD, Iterable[_T]) -> _SD
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        cls = type(self)
        if not cls._relationship.passthrough:
            fabricated_iterable = (
                cls._relationship.fabricate_value(v) for v in iterable
            )
            return type(self).__make__(self._state.update(fabricated_iterable))
        else:
            return type(self).__make__(self._state.update(iterable))

    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return self._state.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._state.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._state.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return self._state.intersection(iterable)

    def difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return self._state.difference(iterable)

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return self._state.symmetric_difference(iterable)

    def union(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return self._state.union(iterable)

    @final
    def find_with_attributes(self, **attributes):
        # type: (Any) -> _T
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        return self._state.find_with_attributes(**attributes)

    @classmethod
    @final
    def deserialize(cls, serialized, **kwargs):
        # type: (Type[_SD], List, Any) -> _SD
        """
        Deserialize.

        :param serialized: Serialized.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        :raises RuntimeError: Not deserializable.
        """
        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise RuntimeError(error)
        state = SetState(
            cls.deserialize_value(v, location=None, **kwargs) for v in serialized
        )
        return cls.__make__(state)

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> List
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized.
        :raises RuntimeError: Not serializable.
        """
        if not type(self)._relationship.serialized:
            error = "'{}' is not serializable".format(type(self).__fullname__)
            raise RuntimeError(error)
        return sorted(
            (self.serialize_value(v, location=None, **kwargs) for v in self._state),
            key=lambda v: hash(v),
        )

    @property
    @final
    def _state(self):
        # type: () -> SetState[_T]
        """Internal state."""
        return cast("SetState", super(SetData, self)._state)


class InteractiveSetData(
    SetData[_T],
    BaseInteractiveSetStructure[_T],
    BaseInteractiveAuxiliaryData[_T],
):
    """Interactive set data."""

    __slots__ = ()
