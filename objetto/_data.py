# -*- coding: utf-8 -*-
"""Immutable structures."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar

from six import string_types, with_metaclass

from .._bases import final, init_context
from ._structures import (
    BaseRelationship,
    BaseStructureMeta,
    BaseStructure,
    BaseProtectedStructure,
    BaseInteractiveStructure,
    BaseAuxiliaryStructureMeta,
    BaseAuxiliaryStructure,
    BaseProtectedAuxiliaryStructure,
    BaseInteractiveAuxiliaryStructure,
    KeyRelationship,
    BaseDictStructureMeta,
    BaseDictStructure,
    BaseProtectedDictStructure,
    BaseInteractiveDictStructure,
    BaseListStructureMeta,
    BaseListStructure,
    BaseProtectedListStructure,
    BaseInteractiveListStructure,
    BaseSetStructureMeta,
    BaseSetStructure,
    BaseProtectedSetStructure,
    BaseInteractiveSetStructure,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Dict,
        Hashable,
        Iterable,
        Mapping,
        Optional,
        Tuple,
        Type,
        Union,
    )

    from ..utils.factoring import LazyFactory
    from ..utils.immutable import Immutable
    from ..utils.type_checking import LazyTypes

__all__ = [
    "DataRelationship",
]


_NOT_FOUND = object()


_T = TypeVar("_T")  # Any type.
_KT = TypeVar("_KT")  # Key type.
_VT = TypeVar("_VT")  # Value type.


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
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """Relationship type."""
        return DataRelationship


class BaseData(with_metaclass(BaseDataMeta, BaseProtectedStructure[_T])):
    """
    Base data.
    
      - Is an immutable protected structure.
    """

    __slots__ = ("__state",)

    @final
    def __copy__(self):
        # type: () -> BaseData
        """
        Get copy.

        :return: Copy.
        """
        return self

    @classmethod
    def __make__(cls, state):
        # type: (Immutable) -> BaseData
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
        # type: (Immutable) -> None
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


class BaseInteractiveData(BaseData[_T], BaseInteractiveStructure[_T]):
    """
    Base interactive data.
    
      - Is an immutable interactive structure.
    """
    __slots__ = ()


class BaseAuxiliaryDataMeta(BaseDataMeta):
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
        BaseInteractiveAuxiliaryStructure[_T],
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
        if not type(self)._relationship.compared:
            return False
        if not isinstance(other, BaseAuxiliaryData):
            return False
        if isinstance(self, BaseInteractiveAuxiliaryData) != isinstance(
            other, BaseInteractiveAuxiliaryData
        ):
            return False
        if type(other)._base_auxiliary_type is type(self)._base_auxiliary_type:
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
