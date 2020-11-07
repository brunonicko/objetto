# -*- coding: utf-8 -*-
"""Data container."""

from typing import TYPE_CHECKING

from six import with_metaclass, string_types

from .._bases import init_context, final
from .._containers.bases import (
    BaseRelationship,
    BaseContainerMeta,
    BaseSemiInteractiveContainer,
    BaseInteractiveContainer,
    BaseAuxiliaryContainerMeta,
    BaseSemiInteractiveAuxiliaryContainer,
    BaseInteractiveAuxiliaryContainer,
)

if TYPE_CHECKING:
    from typing import (
        Any, Callable, Tuple, Type, Optional, Dict, Mapping, Iterable, Hashable, Union
    )

    from ..utils.type_checking import LazyTypes
    from ..utils.factoring import LazyFactory
    from ..utils.immutable import Immutable

__all__ = [
    "DataRelationship",
    "BaseDataMeta",
    "BaseData",
    "BaseInteractiveData",
    "BaseAuxiliaryDataMeta",
    "BaseAuxiliaryData",
    "BaseInteractiveAuxiliaryData",
]

_NOT_FOUND = object()


@final
class DataRelationship(BaseRelationship):
    """
    Relationship between a data container and its values.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param type_checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Value factory.
    :param serialized: Whether should be serialized.
    :param serializer: Custom serializer.
    :param deserializer: Custom deserializer.
    :param represented: Whether should be represented.
    :param eq: Whether the value should be leverage when comparing for equality.
    """

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

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        """
        dct = super(DataRelationship, self).to_dict()
        dct.update({
            "eq": self.eq,
        })
        return dct


class BaseDataMeta(BaseContainerMeta):
    """Metaclass for :class:`BaseData`."""

    @property
    @final
    def _serializable_container_types(cls):
        # type: () -> Tuple[Type[BaseData]]
        """Serializable container types."""
        return (BaseData,)

    @property
    @final
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """Relationship type."""
        return DataRelationship


class BaseData(with_metaclass(BaseDataMeta, BaseSemiInteractiveContainer)):
    """Base data class."""
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

    @final
    def _transform(
        self,
        locations,  # type: Iterable[Optional[Hashable]]
        transformation,  # type: Union[str, Callable]
        args=(),  # type: Iterable[Any]
        kwargs=None,  # type: Optional[Mapping[str, Any]]
    ):
        # type: (...) -> Any
        """
        Perform transformation at nested location and return new data (or substitute
        value returned by the transformation function).

        :param locations: Locations (path to the data to be transformed).
        :param transformation: Transformation function or method name.
        :param args: Arguments to be passed to transformation function/method.
        :param kwargs: Keyword arguments to be passed to transformation function/method.
        :return: New data or substitute value.
        :raises TypeError: Wrong type provided to 'transformation'/no interactive data.
        """
        locations = list(locations)
        if not locations:
            if isinstance(transformation, string_types):
                return getattr(self, transformation)(*args, **dict(kwargs or {}))
            elif callable(transformation):
                return transformation(self, *args, **dict(kwargs or {}))
            else:
                error = "expected a method name or a callable for 'transformation'"
                raise TypeError(error)
        else:
            location, locations = locations[0], locations[1:]
            data = self.get(location, _NOT_FOUND)
            if data is _NOT_FOUND:
                error = "invalid location {} for {}".format(location, self)
                raise ValueError(error)
            if not isinstance(data, BaseInteractiveData):
                error = "'{}' is not an interactive data, can't transform".format(
                    type(data).__name__
                )
                raise TypeError(error)
            return self._set(
                location,
                data.transform(locations, transformation, args, kwargs),
            )

    @property
    def _state(self):
        # type: () -> Immutable
        """State."""
        return self.__state


class BaseInteractiveData(BaseData, BaseInteractiveContainer):
    """Base data interactive container."""
    __slots__ = ()

    @final
    def transform(
        self,
        locations,  # type: Iterable[Optional[Hashable]]
        transformation,  # type: Union[str, Callable]
        args=(),  # type: Iterable[Any]
        kwargs=None,  # type: Optional[Mapping[str, Any]]
    ):
        # type: (...) -> Any
        """
        Perform transformation at nested location and return new data (or substitute
        value returned by the transformation function).

        :param locations: Locations (path to the data to be transformed).
        :param transformation: Transformation function or method name.
        :param args: Arguments to be passed to transformation function/method.
        :param kwargs: Keyword arguments to be passed to transformation function/method.
        :return: New data or substitute value.
        :raises TypeError: Wrong type provided to 'transformation'/no interactive data.
        """
        return self._transform(locations, transformation, args=args, kwargs=kwargs)


class BaseAuxiliaryDataMeta(BaseDataMeta, BaseAuxiliaryContainerMeta):
    """Metaclass for :class:`BaseAuxiliaryData`."""
    pass


class BaseAuxiliaryData(
    with_metaclass(
        BaseAuxiliaryDataMeta, BaseData, BaseSemiInteractiveAuxiliaryContainer
    )
):
    """Base data auxiliary container with a single relationship."""
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
            if not type(self)._relationship.eq:
                self.__hash = id(self)
            else:
                self.__hash = hash((self._state, type(self)._relationship))
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
        if not type(self)._relationship.eq:
            return False
        if isinstance(other, type(self)._base_auxiliary_type):
            if type(self)._relationship == type(other)._relationship:
                return self._state == other._state
        return False


class BaseInteractiveAuxiliaryData(
    BaseAuxiliaryData, BaseInteractiveData, BaseInteractiveAuxiliaryContainer
):
    """Base data auxiliary interactive container with a single relationship."""

    __slots__ = ()
