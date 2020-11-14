# -*- coding: utf-8 -*-
"""Object container."""

from abc import abstractmethod
from contextlib import contextmanager
from inspect import getmro
from typing import TYPE_CHECKING, cast
from weakref import WeakKeyDictionary

from six import iteritems, string_types, with_metaclass

from .._bases import Base, ProtectedBase, final
from .._containers.bases import (
    BaseAuxiliaryContainerMeta,
    BaseContainerMeta,
    BaseMutableAuxiliaryContainer,
    BaseMutableContainer,
    BaseRelationship,
    BaseSemiInteractiveAuxiliaryContainer,
    BaseSemiInteractiveContainer,
)
from .._data.bases import BaseData, DataRelationship
from ..utils.type_checking import assert_is_instance, import_types

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Dict,
        Hashable,
        Iterable,
        Mapping,
        MutableMapping,
        Optional,
        Set,
        Tuple,
        Type,
        Union,
    )

    from .._application import Application
    from ..utils.factoring import LazyFactory
    from ..utils.immutable import Immutable
    from ..utils.type_checking import LazyTypes

__all__ = [
    "ObjectRelationship",
    "BaseObjectMeta",
    "BaseObject",
    "BaseAuxiliaryObjectMeta",
    "BaseAuxiliaryObject",
]

REACTION_TAG = "__isreaction__"
UNIQUE_ATTRIBUTES_METADATA_KEY = "unique_attributes"


@final
class ObjectRelationship(BaseRelationship):
    """
    Relationship between an object container and its values.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Value factory.
    :param serialized: Whether should be serialized.
    :param serializer: Custom serializer.
    :param deserializer: Custom deserializer.
    :param represented: Whether should be represented.
    """

    __slots__ = ("child", "history", "data", "_data_relationship")

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
        child=True,  # type: bool
        history=True,  # type: bool
        data=True,  # type: bool
        data_relationship=None,  # type: Optional[DataRelationship]
    ):
        super(ObjectRelationship, self).__init__(
            types=types,
            subtypes=subtypes,
            checked=checked,
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

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        """
        dct = super(ObjectRelationship, self).to_dict()
        dct.update(
            {
                "child": self.child,
                "history": self.history,
                "data": self.data,
                "data_relationship": self.data_relationship,
            }
        )
        return dct

    @property
    def data_relationship(self):
        # type: () -> Optional[DataRelationship]
        """Data relationship."""
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
                checked=self.checked,
                module=self.module,
                factory=None,
                serialized=self.serialized,
                serializer=None,
                deserializer=None,
                represented=self.represented,
                compared=True,
            )
        return self._data_relationship


@final
class HistoryDescriptor(ProtectedBase):
    """
    Descriptor to be used on :class:`BaseObject` classes.
    When used, a history object will keep track of changes, allowing for undo/redo.
    If accessed through an instance, the descriptor will return the history object.
    """

    __slots__ = ("size",)

    def __init__(self, size=None):
        # type: (Optional[int]) -> None
        if size is not None:
            size = int(size)
            if size < 0:
                size = 0
        self.size = size

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return hash(id(self))

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare with another object for identity.

        :param other: Another object.
        :return: True if the same object.
        """
        return self is other

    def __get__(
        self,
        instance,  # type: Optional[BaseObject]
        owner,  # type: Optional[Type[BaseObject]]
    ):
        # type: (...) -> Union[History, HistoryDescriptor]
        """
        Get history object when accessing from instance or this descriptor otherwise.

        :param instance: Instance.
        :param owner: Owner class.
        :return: History object or this descriptor.
        """
        if instance is not None:
            cls = type(instance)
            if getattr(cls, "_history_descriptor", None) is self:
                history = instance._history
                assert history is not None
                return history
        return self


class BaseObjectFunctions(Base):
    """Internal object static functions."""

    __slots__ = ()

    @staticmethod
    @abstractmethod
    def replace_child_data(data, child_data, location, data_relationship):
        # type: (BaseData, BaseData, Any, DataRelationship) -> BaseData
        """
        Replace child data.

        :param data: Current data.
        :param child_data: New child data.
        :param location: Old child data location.
        :param data_relationship: Data relationship for the location.
        :return: New data.
        """
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
                cls.__fullname__,
                ", ".join("'{}'".format(n) for n in history_descriptors),
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

        # Store reaction method names in a tuple, sort them by priority.
        sorted_reactions = tuple(
            r
            for r, _ in sorted(iteritems(reactions), key=lambda p: (p[1] is None, p[1]))
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


class BaseObject(with_metaclass(BaseObjectMeta, BaseSemiInteractiveContainer)):
    """Base object class."""

    __slots__ = ("__weakref__", "__app")
    __functions__ = BaseObjectFunctions

    def __init__(self, app):
        # type: (Application) -> None
        assert_is_instance(app, Application)
        self.__app = app

    @final
    def _hash(self):
        """
        Get hash based on object id.

        :return: Hash based on object id.
        """
        return hash(id(self))

    @final
    def _eq(self, other):
        """
        Compare with another object for identity.

        :param other: Another object.
        :return: True if the same object.
        """
        return self is other

    @final
    def __copy__(self):
        # type: () -> BaseObject
        """
        Get shallow copy.

        :return: Shallow copy.
        """
        return type(self).deserialize(self.serialize(), app=self.app)

    @abstractmethod
    def _locate(self, child):
        # type: (BaseObject) -> Optional[Hashable]
        """
        Locate child object.

        :param child: Child object.
        :return: Location.
        """
        raise NotImplementedError()

    @abstractmethod
    def _locate_data(self, child):
        # type: (BaseObject) -> Optional[Hashable]
        """
        Locate child object's data.

        :param child: Child object.
        :return: Data location.
        """
        raise NotImplementedError()

    @final
    @contextmanager
    def _batch_context(self, name="Batch", **metadata):
        # type: (str, Any) -> Iterator[Batch]
        """
        Batch change context manager.

        :return: Batch change.
        """
        change = Batch(name=str(name), obj=self, metadata=metadata)
        with self.app.__.batch_context(self, change):
            yield change

    @property
    def _state(self):
        # type: () -> Immutable
        """State."""
        with self.app.__.read_context(self) as read:
            return read().state

    @property
    @final
    def _parent(self):
        # type: () -> Optional[BaseObject]
        """Parent object or None."""
        with self.app.__.read_context(self) as read:
            return read().parent_ref()

    @property
    @final
    def _children(self):
        # type: () -> Set[BaseObject]
        """Children objects."""
        with self.app.__.read_context(self) as read:
            return read().children

    @property
    @final
    def _history(self):
        # type: () -> Optional[History]
        """History or None."""
        with self.app.__.read_context(self) as read:
            store = read()
            if store.history is not None:
                return store.history
            provider = store.history_provider_ref()
            if provider is not None:
                assert isinstance(provider, BaseObject)
                return provider._history
        return None

    @property
    @final
    def app(self):
        # type: () -> Application
        """Application."""
        return self.__app

    @property
    def data(self):
        # type: () -> Optional[BaseData]
        """Data."""
        with self.app.__.read_context(self) as read:
            return read().data


class BaseMutableObject(BaseObject, BaseMutableContainer):
    """Base mutable object container."""


class BaseAuxiliaryObjectMeta(BaseObjectMeta, BaseAuxiliaryContainerMeta):
    """Metaclass for :class:`BaseAuxiliaryObject`."""

    @property
    @final
    def _relationship_type(cls):
        # type: () -> Type[ObjectRelationship]
        """Relationship type."""
        return ObjectRelationship


class BaseAuxiliaryObject(
    with_metaclass(
        BaseAuxiliaryObjectMeta,
        BaseObject,
        BaseSemiInteractiveAuxiliaryContainer,
    )
):
    """Base auxiliary object container with a single relationship."""

    __slots__ = ()

    _relationship = ObjectRelationship()
    """Relationship for all locations."""

    @final
    def find(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        """
        with self.app.__.read_context(self) as read:
            metadata = read().metadata

            # The 'UniqueAttributes' reaction caches children with unique attributes.
            if UNIQUE_ATTRIBUTES_METADATA_KEY in metadata:
                if not attributes:
                    error = "no attributes provided"
                    raise ValueError(error)
                cache = metadata[UNIQUE_ATTRIBUTES_METADATA_KEY]
                if set(cache).issuperset(attributes):
                    match = None
                    for name, value in iteritems(attributes):
                        if value not in cache[name]:
                            break
                        this_match = cache[name][value]
                        if match is not None and this_match is not match:
                            break
                        match = this_match
                    else:
                        return match

            # Fallback to iterating over the state (slower).
            return self._state.find(**attributes)


class BaseMutableAuxiliaryObject(
    BaseAuxiliaryObject, BaseMutableObject, BaseMutableAuxiliaryContainer
):
    """Base auxiliary object mutable container with a single relationship."""

    __slots__ = ()


class BaseProxy(Base):
    """
    Base auxiliary proxy.

    :param obj: Auxiliary object.
    """

    __slots__ = ("__obj",)

    def __init__(self, obj):
        # type: (BaseAuxiliaryObject) -> None
        self.__obj = obj

    @final
    def __hash__(self):
        """
        Get hash based on object id.

        :return: Hash based on object id.
        """
        return hash(self.__obj)

    @final
    def __eq__(self, other):
        """
        Compare with another object for identity.

        :param other: Another object.
        :return: True if the same object.
        """
        return self is other

    @final
    def find(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        """
        return self._obj.find(**attributes)

    @property
    def _obj(self):
        # type: () -> BaseAuxiliaryObject
        """Auxiliary object."""
        return self.__obj

    @property
    @final
    def app(self):
        # type: () -> Application
        """Application."""
        return self._obj.app

    @property
    def data(self):
        # type: () -> Optional[BaseData]
        """Data."""
        return self._obj.data
