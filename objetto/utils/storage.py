from abc import abstractmethod
from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING, Generic, TypeVar, cast
from weakref import WeakSet, ref

from basicco import final
from pyrsistent import pmap

from .slotted_base import SlottedBase

if TYPE_CHECKING:
    from _weakref import ReferenceType
    from typing import Dict, Mapping, MutableSet, Optional

    from pyrsistent.typing import PMap, PMapEvolver

__all__ = ["AbstractStorage", "Storage", "Evolver"]

_T = TypeVar("_T")
_AST = TypeVar("_AST", bound="AbstractStorage")
_ST = TypeVar("_ST", bound="Storage")
_ET = TypeVar("_ET", bound="Evolver")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


# noinspection PyAbstractClass
class AbstractStorage(SlottedBase, Generic[_KT, _VT]):
    """Abstract interface for storages."""

    __slots__ = ()

    @final
    def get(self, key, fallback=None):
        # type: (_KT, Optional[_VT]) -> Optional[_VT]
        """Get value for key, return fallback value if not present."""
        try:
            return self.query(key)
        except KeyError:
            return fallback

    @abstractmethod
    def update(self, updates):
        # type: (_AST, Mapping[_KT, _VT]) -> _AST
        """Update keys and values."""
        raise NotImplementedError()

    @abstractmethod
    def query(self, key):
        # type: (_KT) -> _VT
        """Query value for key."""
        raise NotImplementedError()

    @abstractmethod
    def to_dict(self):
        # type: () -> Dict[_KT, _VT]
        """Convert to dictionary."""
        raise NotImplementedError()


@final
class Storage(AbstractStorage, Generic[_KT, _VT]):
    """Immutable weak key/strong value storage."""

    __slots__ = ("__weakref__", "__parent", "__storages", "__data")

    def __init__(self, initial=None):
        # type: (Optional[Mapping[_KT, _VT]]) -> None
        self.__parent = None  # type: Optional[ReferenceType[Storage[_KT, _VT]]]
        self.__storages = WeakSet({self})  # type: MutableSet[Storage[_KT, _VT]]
        self.__data = cast(
            "PMapEvolver[ReferenceType[_KT], _VT]", pmap().evolver()
        )  # type: PMapEvolver[ReferenceType[_KT], _VT]
        if initial is not None:
            self.__initialize(initial)

    def __reduce__(self):
        return type(self), (self.to_dict(),)

    def __deepcopy__(self, memo=None):
        if memo is None:
            memo = {}
        try:
            deep_copy = memo[id(self)]
        except KeyError:
            deep_copy = memo[id(self)] = Storage()
            args = (self.to_dict(), memo)
            deep_copy.__initialize(deepcopy(*args))
        return deep_copy

    def __copy__(self):
        return self

    @staticmethod
    def __clean(storages, weak_key):
        # type: (MutableSet[Storage[_KT, _VT]], ReferenceType[_KT]) -> None
        for storage in storages:
            del storage.__data[weak_key]

    def __initialize(self, initial):
        # type: (Mapping[_KT, _VT]) -> None
        temp_storage = self.update(initial)
        self.__storages = storages = temp_storage.__storages
        storages.clear()
        storages.add(self)
        self.__data = temp_storage.__data

    def update(self, updates):
        # type: (_ST, Mapping[_KT, _VT]) -> _ST
        """Get new storage with updated keys and values."""
        if not updates:
            return self

        # Make a new storage.
        storage = Storage.__new__(Storage)
        storage.__parent = ref(self)
        storage.__storages = storages = WeakSet({storage})

        # Make weak references to keys.
        weak_updates = {}
        for key, data in updates.items():
            weak_key = ref(key, partial(Storage.__clean, storages))
            weak_updates[weak_key] = data
        if not weak_updates:
            return self

        # Add new storages to all parents.
        parent = self  # type: Optional[Storage[_KT, _VT]]
        while parent is not None:
            parent.__storages.add(storage)
            if parent.__parent is None:
                break
            parent = parent.__parent()

        # Update data.
        storage.__data = self.__data.persistent().update(weak_updates).evolver()

        return storage

    def query(self, key):
        # type: (_KT) -> _VT
        """Query value for key."""
        return self.__data[ref(key)]

    def to_dict(self):
        # type: () -> Dict[_KT, _VT]
        """Convert to dictionary."""
        to_dict = {}
        for weak_key, data in self.__data.persistent().items():
            key = weak_key()
            if key is not None:
                to_dict[key] = data
        return to_dict

    def evolver(self):
        # type: () -> Evolver[_KT, _VT]
        """Get evolver."""
        return Evolver(self)


@final
class Evolver(AbstractStorage, Generic[_KT, _VT]):
    """Mutable data storage evolver."""

    __slots__ = ("__storage", "__updates")

    def __init__(self, storage=None):
        # type: (Optional[Storage[_KT, _VT]]) -> None
        if storage is None:
            storage = cast("Storage[_KT, _VT]", Storage())
        self.__storage = storage  # type: Storage[_KT, _VT]
        self.__updates = pmap()  # type: PMap[_KT, _VT]

    def __reduce__(self):
        return _evolver_reducer, (self.__storage, self.__updates)

    def __deepcopy__(self, memo=None):
        if memo is None:
            memo = {}
        try:
            deep_copy = memo[id(self)]
        except KeyError:
            deep_copy = memo[id(self)] = Evolver.__new__(Evolver)
            args_a = (self.__storage, memo)
            deep_copy.__storage = deepcopy(*args_a)
            args_b = (self.__updates, memo)
            deep_copy.__updates = deepcopy(*args_b)
        return deep_copy

    def __copy__(self):
        return self.fork()

    def update(self, updates):
        # type: (_ET, Mapping[_KT, _VT]) -> _ET
        """Update keys and values in place."""
        self.__updates = self.__updates.update(updates)
        return self

    def query(self, key):
        # type: (_KT) -> _VT
        """Query value for key."""
        try:
            return self.__updates[key]
        except KeyError:
            return self.__storage.query(key)

    def to_dict(self):
        # type: () -> Dict[_KT, _VT]
        """Convert to dictionary."""
        return self.storage().to_dict()

    def storage(self):
        # type: () -> Storage[_KT, _VT]
        """Get immutable storage with current updates."""
        return self.__storage.update(self.__updates)

    def fork(self):
        # type: (_ET) -> _ET
        """Fork into another evolver."""
        evolver = Evolver.__new__(Evolver)
        evolver.__storage = self.__storage
        evolver.__updates = self.__updates
        return evolver

    def is_dirty(self):
        # type: () -> bool
        """Get whether has updates."""
        return bool(self.__updates)

    def reset(self):
        # type: () -> None
        """Reset updates."""
        self.__updates = pmap()

    def commit(self):
        # type: () -> None
        """Commit updates."""
        self.__storage = self.__storage.update(self.__updates)
        self.__updates = pmap()

    @property
    def updates(self):
        # type: () -> PMap[_KT, _VT]
        """Updates."""
        return self.__updates


def _evolver_reducer(storage, updates):
    # type: (Storage[_KT, _VT], Mapping[_KT, _VT]) -> Evolver[_KT, _VT]
    evolver = Evolver(storage)  # type: Evolver[_KT, _VT]
    evolver.update(updates)
    return evolver
