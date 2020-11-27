# -*- coding: utf-8 -*-
"""Immutable structures."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, cast

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import with_metaclass

from .._bases import final, init_context
from .._states import BaseState
from .._structures import (
    BaseAuxiliaryStructure,
    BaseAuxiliaryStructureMeta,
    BaseInteractiveAuxiliaryStructure,
    BaseInteractiveStructure,
    BaseRelationship,
    BaseStructure,
    BaseStructureMeta,
)

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, Tuple, Type

    from ..utils.factoring import LazyFactory
    from ..utils.type_checking import LazyTypes

__all__ = [
    "DataRelationship",
    "BaseDataMeta",
    "BaseData",
    "BaseInteractiveData",
]


T = TypeVar("T")  # Any type.


@final
class DataRelationship(BaseRelationship):
    """
    Relationship between a data structure and its values.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Value factory.
    :param serialized: Whether should be serialized.
    :param serializer: Custom serializer.
    :param deserializer: Custom deserializer.
    :param represented: Whether should be represented.
    :param compared: Whether the value should be leverage when comparing.
    """

    __slots__ = ("__compared",)

    def __init__(
        self,
        types=(),  # type: LazyTypes
        subtypes=False,  # type: bool
        checked=None,  # type: Optional[bool]
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
        serialized=True,  # type: bool
        serializer=None,  # type: LazyFactory
        deserializer=None,  # type: LazyFactory
        represented=True,  # type: bool
        compared=True,  # type: bool
    ):
        # type: (...) -> None
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

    @property
    def compared(self):
        # type: () -> bool
        """Whether the value should be leverage when comparing."""
        return self.__compared


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


# noinspection PyAbstractClass
class BaseData(with_metaclass(BaseDataMeta, BaseStructure[T])):
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
        # type: (Type[_BD], Any) -> _BD
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
        # type: (BaseState) -> None
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
        # type: () -> BaseState
        """State."""
        return self.__state


# noinspection PyAbstractClass
class BaseInteractiveData(BaseData[T], BaseInteractiveStructure[T]):
    """
    Base interactive data.

      - Is an immutable interactive data structure.
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


# noinspection PyAbstractClass
class BaseAuxiliaryData(
    with_metaclass(
        BaseAuxiliaryDataMeta,
        BaseAuxiliaryStructure[T],
        BaseData[T],
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
        self_compared = type(self)._relationship.compared
        if not self_compared:
            return False
        if not isinstance(other, collections_abc.Hashable):
            return self._state == other
        if not isinstance(other, BaseAuxiliaryData):
            return False
        other_compared = type(other)._relationship.compared
        if not other_compared:
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

    @final
    def find_with_attributes(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        return super(BaseAuxiliaryData, self).find_with_attributes(**attributes)


# noinspection PyAbstractClass
class BaseInteractiveAuxiliaryData(
    BaseAuxiliaryData[T],
    BaseInteractiveData[T],
    BaseInteractiveAuxiliaryStructure[T],
):
    """Base interactive auxiliary data."""

    __slots__ = ()
