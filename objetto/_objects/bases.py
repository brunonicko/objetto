# -*- coding: utf-8 -*-
"""Object container."""

from abc import abstractmethod
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary
from inspect import getmro

from six import with_metaclass, string_types, iteritems

from .._bases import Base, ProtectedBase, final
from .._containers.bases import (
    BaseRelationship,
    BaseContainerMeta,
    BaseContainer,
    BaseAuxiliaryContainerMeta,
    BaseAuxiliaryContainer,
)
from .._data.bases import DataRelationship, BaseData
from ..utils.type_checking import import_types

if TYPE_CHECKING:
    from typing import (
        Dict, Callable, Any, Tuple, Type, Optional, Set, Union, MutableMapping
    )

    from .._application import Application
    from ..utils.type_checking import LazyTypes
    from ..utils.factoring import LazyFactory

__all__ = [
    "ObjectRelationship",
    "BaseObjectMeta",
    "BaseObject",
    "BaseAuxiliaryObjectMeta",
    "BaseAuxiliaryObject",
]

REACTION_TAG = "__isreaction__"


@final
class ObjectRelationship(BaseRelationship):
    """Relationship between an object and its values."""

    __slots__ = ("child", "history", "data", "_data_relationship")

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
        child=True,  # type: bool
        history=True,  # type: bool
        data=True,  # type: bool
        data_relationship=None,  # type: Optional[DataRelationship]
    ):
        super(ObjectRelationship, self).__init__(
            types=types,
            subtypes=subtypes,
            type_checked=type_checked,
            module=module,
            factory=factory,
            serialized=bool(serialized) if child else False,
            serializer=serializer if child else None,
            deserializer=deserializer if child else None,
            represented=represented,
        )
        self.child = bool(child)
        self.history = self.child and bool(history)
        self.data = self.child and bool(data)
        self._data_relationship = data_relationship if self.data else None

    @property
    def data_relationship(self):
        if self._data_relationship is None and self.data:
            types = set()  # type: Set[Union[Type, str]]
            for lazy, typ in zip(self.types, import_types(self.types)):
                if isinstance(typ, BaseObjectMeta):
                    if isinstance(lazy, string_types):
                        types.add(lazy + ".Data")
                    else:
                        types.add(typ.Data)
                else:
                    types.add(typ)
            self._data_relationship = DataRelationship(
                types=types,
                subtypes=self.subtypes,
                type_checked=self.type_checked,
                module=self.module,
                factory=self.factory,
                serialized=self.serialized,
                serializer=None,
                deserializer=None,
                represented=self.represented,
                eq=True,
            )
        return self._data_relationship


@final
class HistoryDescriptor(ProtectedBase):
    __slots__ = ("size",)

    def __init__(self, size=None):
        # type: (Optional[int]) -> None
        if size is not None:
            size = int(size)
            if size < 0:
                size = 0
        self.size = size
    #
    # def __get__(
    #     self,
    #     instance,  # type: Optional[BaseObject]
    #     owner,  # type: Optional[Type[BaseObject]]
    # ):
    #     # type: (...) -> Union[History, HistoryDescriptor]
    #     if instance is not None:
    #         cls = type(instance)
    #         if getattr(cls, "_history_descriptor", None) is self:
    #             history = instance._history
    #             assert history is not None
    #             return history
    #     return self


class BaseObjectFunctions(Base):
    __slots__ = ()

    @staticmethod
    def replace_child_data(data, child_data, location, data_relationship):
        # type: (BaseData, BaseData, Any, DataRelationship) -> BaseData
        raise NotImplementedError()


class BaseObjectMeta(BaseContainerMeta):
    """Metaclass for :class:`BaseObject`."""

    __history_descriptor_name = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseObjectMeta, Optional[str]]
    __history_descriptor = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseObjectMeta, Optional[HistoryDescriptor]]
    __reactions = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseObjectMeta, Tuple[str, ...]]

    def __init__(cls, name, bases, dct):
        super(BaseObjectMeta, cls).__init__(name, bases, dct)

        # Find history descriptor and reactions.
        history_descriptors = {}  # type: Dict[str, HistoryDescriptor]
        reactions = {}  # type: Dict[str, Optional[int]]
        for base in reversed(getmro(cls)):
            for member_name, member in iteritems(base.__dict__):
                history_descriptors.pop(member_name, None)
                reactions.pop(member_name, None)
                if isinstance(member, HistoryDescriptor):
                    history_descriptors[member_name] = member
                elif hasattr(member, REACTION_TAG):
                    reactions[member_name] = getattr(member, REACTION_TAG)

        # Can't have more than one history descriptor.
        if len(history_descriptors) > 1:
            error = "class '{}' has multiple history descriptors at {}".format(
                cls.__name__, ", ".join("'{}'".format(n) for n in history_descriptors)
            )
            raise TypeError(error)

        # Store history descriptor and its name.
        history_descriptor_name = None  # type: Optional[str]
        history_descriptor = None  # type: Optional[HistoryDescriptor]
        if len(history_descriptors) == 1:
            history_descriptor_name, history_descriptor = next(
                iteritems(history_descriptors)
            )

        type(cls).__history_descriptor_name[cls] = history_descriptor_name
        type(cls).__history_descriptor[cls] = history_descriptor

        # Store reactions in a tuple, sort them by priority.
        sorted_reactions = tuple(
            r for r, _ in sorted(
                iteritems(reactions), key=lambda p: (p[1] is None, p[1])
            )
        )
        type(cls).__reactions[cls] = sorted_reactions

    @property
    @abstractmethod
    def _state_factory(cls):
        # type: () -> Callable[..., Any]
        """State factory."""
        raise NotImplementedError()

    @property
    @final
    def _history_descriptor_name(cls):
        # type: () -> Optional[str]
        """History descriptor name or None."""
        return type(cls).__history_descriptor_name[cls]

    @property
    @final
    def _history_descriptor(cls):
        # type: () -> Optional[HistoryDescriptor]
        """History descriptor or None."""
        return type(cls).__history_descriptor[cls]

    @property
    @final
    def _reactions(cls):
        # type: () -> Tuple[str, ...]
        """Names of reaction methods ordered by priority."""
        return type(cls).__reactions[cls]

    @property
    @final
    def _serializable_container_types(cls):
        # type: () -> Tuple[Type[BaseObject], Type[BaseData]]
        """Serializable container types."""
        return BaseObject, BaseData

    @property
    @abstractmethod
    def Data(cls):
        # type: () -> Optional[Type[BaseData]]
        """Data type."""
        raise NotImplementedError()


class BaseObject(with_metaclass(BaseObjectMeta, BaseContainer)):
    """Base obj class."""
    __slots__ = ("__weakref__", "__app")
    __functions__ = BaseObjectFunctions

    def __init__(self, app):
        # type: (Application) -> None
        self.__app = app

    @final
    def __hash__(self):
        """Get hash."""
        return object.__hash__(self)

    @final
    def __eq__(self, other):
        # type: (Any) -> bool
        """Compare with another object for identity."""
        return other is self

    @final
    def __copy__(self):
        # type: () -> BaseObject
        return type(self).deserialize(self.serialize(), app=self.app)

    @abstractmethod
    def _locate(self, child):
        # type: (BaseObject) -> Any
        """Locate child object."""
        raise NotImplementedError()

    @property
    @final
    def app(self):
        # type: () -> Application
        return self.__app


class BaseAuxiliaryObjectMeta(BaseObjectMeta, BaseAuxiliaryContainerMeta):
    """Metaclass for :class:`BaseAuxiliaryObject`."""

    @property
    @abstractmethod
    def _auxiliary_obj_type(cls):
        # type: () -> Type[BaseAuxiliaryObject]
        """Base auxiliary obj type."""
        raise NotImplementedError()

    @property
    @final
    def _relationship_type(cls):
        # type: () -> Type[ObjectRelationship]
        """Relationship type."""
        return ObjectRelationship


class BaseAuxiliaryObject(
    with_metaclass(BaseAuxiliaryObjectMeta, BaseObject, BaseAuxiliaryContainer)
):
    """Object container with a single relationship."""
    __slots__ = ()

    _relationship = ObjectRelationship()
    """Relationship for all locations."""
