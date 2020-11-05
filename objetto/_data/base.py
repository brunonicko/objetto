# -*- coding: utf-8 -*-
"""Data container."""

from abc import abstractmethod
from typing import TYPE_CHECKING

from six import with_metaclass

from .._bases import final
from .._containers.base import (
    BaseRelationship,
    BaseContainerMeta,
    BaseContainer,
    BaseAuxiliaryContainerMeta,
    BaseAuxiliaryContainer,
)

if TYPE_CHECKING:
    from typing import Any, Tuple, Type, Optional

    from ..utils.type_checking import LazyTypes
    from ..utils.factoring import LazyFactory

__all__ = [
    "DataRelationship",
    "BaseDataMeta",
    "BaseData",
    "BaseAuxiliaryDataMeta",
    "BaseAuxiliaryData",
]


@final
class DataRelationship(BaseRelationship):
    """Relationship between data and its values."""

    __slots__ = ("eq",)

    def __init__(
        self,
        types=(),  # type: LazyTypes
        subtypes=False,  # type: bool
        type_checked=True,  # type: bool
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
        serialized=True,  # type: bool
        serializer=None,  # type: LazyFactory
        deserializer=None,  # type: LazyFactory
        represented=True,  # type: bool
        eq=True,  # type: bool
    ):
        super(DataRelationship, self).__init__(
            types=types,
            subtypes=subtypes,
            type_checked=type_checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
        )
        self.eq = bool(eq)


class BaseDataMeta(BaseContainerMeta):
    """Metaclass for :class:`BaseData`."""

    @property
    @final
    def _serializable_container_types(cls):
        # type: () -> Tuple[Type[BaseData]]
        """Serializable container types."""
        return (BaseData,)


class BaseData(with_metaclass(BaseDataMeta, BaseContainer)):
    """Base data class."""
    __slots__ = ()

    @classmethod
    @abstractmethod
    def __make__(cls, state=None):
        # type: (Any) -> BaseData
        raise NotImplementedError()

    def __copy__(self):
        # type: () -> BaseData
        return self


class BaseAuxiliaryDataMeta(BaseDataMeta, BaseAuxiliaryContainerMeta):
    """Metaclass for :class:`BaseAuxiliaryData`."""

    @property
    @abstractmethod
    def _auxiliary_data_type(cls):
        # type: () -> Type[BaseAuxiliaryData]
        """Base auxiliary data type."""
        raise NotImplementedError()

    @property
    @final
    def _relationship_type(cls):
        # type: () -> Type[DataRelationship]
        """Relationship type."""
        return DataRelationship


class BaseAuxiliaryData(
    with_metaclass(BaseAuxiliaryDataMeta, BaseData, BaseAuxiliaryContainer)
):
    """Data container with a single relationship."""
    __slots__ = ("__hash",)

    _relationship = DataRelationship()
    """Relationship for all locations."""

    @final
    def __hash__(self):
        """Get hash."""
        try:
            return self.__hash  # type: ignore
        except AttributeError:
            if not type(self)._relationship.eq:
                self.__hash = object.__hash__(self)
            else:
                self.__hash = hash(self._state)
            return self.__hash

    @final
    def __eq__(self, other):
        # type: (Any) -> bool
        """Compare with another object for equality."""
        if not type(self)._relationship.eq:
            return self is other
        if isinstance(other, BaseAuxiliaryData):
            if type(other)._auxiliary_data_type is type(self)._auxiliary_data_type:
                return self._state == other._state
        return False
