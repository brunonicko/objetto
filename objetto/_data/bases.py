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
    "BaseAuxiliaryDataMeta",
    "BaseAuxiliaryData",
    "BaseInteractiveAuxiliaryData",
]


T = TypeVar("T")  # Any type.


@final
class DataRelationship(BaseRelationship):
    """
    Relationship between a data structure and its values.

    Inherits from:
      - :class:`objetto.bases.BaseRelationship`

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
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
        :rtype: dict[str, Any]
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
        """
        Whether the value should be leverage when comparing.

        :rtype: bool
        """
        return self.__compared


class BaseDataMeta(BaseStructureMeta):
    """
    Metaclass for :class:`objetto.bases.BaseData`.

    Inherits from:
      - :class:`objetto.bases.BaseStructureMeta`

    Inherited by:
      - :class:`objetto.bases.BaseAuxiliaryDataMeta`
      - :class:`objetto.data.DataMeta`

    Features:
      - Defines serializable structure type as :class:`objetto.bases.BaseData`.
      - Defines a relationship type as :class:`objetto.data.DataRelationship`.
    """

    @property
    @final
    def _serializable_structure_types(cls):
        # type: () -> Tuple[Type[BaseData]]
        """
        Serializable structure types.

        :rtype: tuple[type[objetto.bases.BaseData]]
        """
        return (BaseData,)

    @property
    @final
    def _relationship_type(cls):
        # type: () -> Type[DataRelationship]
        """
        Relationship type.

        :rtype: type[objetto.data.DataRelationship]
        """
        return DataRelationship


# noinspection PyTypeChecker
_BD = TypeVar("_BD", bound="BaseData")


# noinspection PyAbstractClass
class BaseData(with_metaclass(BaseDataMeta, BaseStructure[T])):
    """
    Base data.

    Metaclass:
      - :class:`objetto.bases.BaseDataMeta`

    Inherits from:
      - :class:`objetto.bases.BaseStructure`

    Inherited by:
      - :class:`objetto.bases.BaseInteractiveData`
      - :class:`objetto.bases.BaseAuxiliaryData`
      - :class:`objetto.data.Data`

    Features:
      - Is an immutable protected structure.
    """

    __slots__ = ("__state",)

    @final
    def __copy__(self):
        # type: (_BD) -> _BD
        """
        Get copy.

        :return: Copy.
        :rtype: objetto.bases.BaseData
        """
        return self

    @classmethod
    def __make__(cls, state):
        # type: (Type[_BD], Any) -> _BD
        """
        Make a new data.

        :param state: Internal state.
        :type state: objetto.bases.BaseState

        :return: New data.
        :rtype: objetto.bases.BaseData
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
        :type state: objetto.bases.BaseState

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
        """
        State.

        :rtype: objetto.bases.BaseState
        """
        return self.__state


# noinspection PyAbstractClass
class BaseInteractiveData(BaseData[T], BaseInteractiveStructure[T]):
    """
    Base interactive data.

    Inherits from:
      - :class:`objetto.bases.BaseData`
      - :class:`objetto.bases.BaseInteractiveStructure`

    Inherited by:
      - :class:`objetto.bases.BaseInteractiveAuxiliaryData`
      - :class:`objetto.data.InteractiveData`

    Features:
      - Is an immutable interactive data structure.
    """

    __slots__ = ()


class BaseAuxiliaryDataMeta(BaseDataMeta, BaseAuxiliaryStructureMeta):
    """
    Metaclass for :class:`objetto.bases.BaseAuxiliaryData`.

    Inherits from:
      - :class:`objetto.bases.BaseDataMeta`
      - :class:`objetto.bases.BaseAuxiliaryStructureMeta`

    Inherited by:
      - :class:`objetto.data.DictDataMeta`
      - :class:`objetto.data.ListDataMeta`
      - :class:`objetto.data.SetDataMeta`

    Features:
      - Defines a base auxiliary type.
    """

    @property
    @abstractmethod
    def _base_auxiliary_type(cls):
        # type: () -> Type[BaseAuxiliaryData]
        """
        Base auxiliary data type.

        :rtype: type[objetto.bases.BaseAuxiliaryData]
        """
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseAuxiliaryData(
    with_metaclass(
        BaseAuxiliaryDataMeta,
        BaseAuxiliaryStructure[T],
        BaseData[T],
    )
):
    """
    Base auxiliary data.

    Metaclass:
      - :class:`objetto.bases.BaseAuxiliaryDataMeta`

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructure`
      - :class:`objetto.bases.BaseData`

    Inherited by:
      - :class:`objetto.bases.BaseInteractiveAuxiliaryData`
      - :class:`objetto.data.InteractiveDictData`
      - :class:`objetto.data.InteractiveListData`
      - :class:`objetto.data.InteractiveSetData`
    """

    __slots__ = ("__hash",)

    _relationship = DataRelationship()
    """
    Relationship for all locations.

    :type: objetto.data.DataRelationship
    """

    @final
    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        :rtype: int
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
        :rtype: bool
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
    """
    Base interactive auxiliary data.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryData`
      - :class:`objetto.bases.BaseInteractiveData`
      - :class:`objetto.bases.BaseInteractiveAuxiliaryStructure`

    Inherited by:
      - :class:`objetto.data.InteractiveDictData`
      - :class:`objetto.data.InteractiveListData`
      - :class:`objetto.data.InteractiveSetData`
    """

    __slots__ = ()
