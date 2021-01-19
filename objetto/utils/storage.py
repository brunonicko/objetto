# -*- coding: utf-8 -*-
"""Immutable weak key/strong value storage and mutable evolver."""

from abc import abstractmethod
from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING, Generic, TypeVar, cast
from weakref import WeakSet, ref

try:
    from typing import final
except ImportError:
    final = lambda f: f  # type: ignore

from pyrsistent import pmap
from six import iteritems

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Mapping, MutableSet, Optional, Tuple, Type

    from pyrsistent.typing import PMap, PMapEvolver

    # Typevars.
    T = TypeVar("T")  # Any type.
    _AS = TypeVar("_AS", bound="AbstractStorage")  # AbstractStorage self type.
    _SE = TypeVar("_SE", bound="StorageEvolver")  # StorageEvolver self type.

    # Type aliases.
    WeakReference = Callable[[], Optional[T]]  # Weak reference-like callable type.

__all__ = ["AbstractStorage", "Storage", "StorageEvolver"]

# Runtime typevars.
KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.


class AbstractStorage(Generic[KT, VT]):
    """Abstract interface for storages."""

    __slots__ = ()

    @abstractmethod
    def update(self, updates):
        # type: (_AS, Mapping[KT, VT]) -> _AS
        """
        Update keys and values.

        :param updates: Updates.
        :type updates: collections.abc.Mapping[collections.abc.Hashable, Any]

        :return: Updated abstract storage.
        :rtype: AbstractStorage
        """
        raise NotImplementedError()

    @abstractmethod
    def query(self, key):
        # type: (KT) -> VT
        """
        Query value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Value.

        :raises KeyError: Key is not in storage.
        """
        raise NotImplementedError()

    @abstractmethod
    def to_dict(self):
        # type: () -> Dict[KT, VT]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[collections.abc.Hashable, Any]
        """
        raise NotImplementedError()


@final
class Storage(AbstractStorage[KT, VT]):
    """
    Immutable weak key/strong value storage.

    :param initial: Initial values.
    :type initial: collections.abc.Mapping[collections.abc.Hashable, Any]
    """

    __slots__ = ("__weakref__", "__parent", "__storages", "__data")

    def __init__(self, initial=None):
        # type: (Optional[Mapping[KT, VT]]) -> None
        self.__parent = None  # type: Optional[WeakReference[Storage[KT, VT]]]
        self.__storages = WeakSet({self})  # type: MutableSet[Storage[KT, VT]]
        self.__data = cast(
            "PMapEvolver[WeakReference[KT], VT]", pmap().evolver()
        )  # type: PMapEvolver[WeakReference[KT], VT]
        if initial is not None:
            self.__initialize(initial)

    def __reduce__(self):
        # type: () -> Tuple[Type[Storage], Tuple[Dict[KT, VT]]]
        return Storage, (self.to_dict(),)

    def __deepcopy__(self, memo=None):
        # type: (Optional[Dict[int, Any]]) -> Storage[KT, VT]
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
        # type: (MutableSet[Storage[KT, VT]], WeakReference[KT]) -> None
        for storage in storages:
            del storage.__data[weak_key]

    def __initialize(self, initial):
        # type: (Mapping[KT, VT]) -> None
        temp_storage = self.update(initial)
        self.__storages = storages = temp_storage.__storages
        storages.clear()
        storages.add(self)
        self.__data = temp_storage.__data

    def to_dict(self):
        # type: () -> Dict[KT, VT]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[collections.abc.Hashable, Any]
        """
        update = {}
        for weak_key, data in iteritems(self.__data.persistent()):
            key = weak_key()
            if key is not None:
                update[key] = data
        return update

    def update(self, updates):
        # type: (Mapping[KT, VT]) -> Storage[KT, VT]
        """
        Get new storage with update keys and values.

        :param updates: Updates.
        :type updates: collections.abc.Mapping[collections.abc.Hashable, Any]

        :return: Updated storage.
        :rtype: Storage
        """
        if not updates:
            return self

        # Make a new storage.
        storage = Storage.__new__(Storage)
        storage.__parent = ref(self)
        storage.__storages = storages = WeakSet({storage})

        # Make weak references to keys.
        weak_updates = {}
        for key, data in iteritems(updates):
            weak_key = ref(key, partial(Storage.__clean, storages))
            weak_updates[weak_key] = data
        if not weak_updates:
            return self

        # Add new storages to all parents.
        parent = self  # type: Optional[Storage[KT, VT]]
        while parent is not None:
            parent.__storages.add(storage)
            if parent.__parent is None:
                break
            parent = parent.__parent()

        # Update data.
        storage.__data = self.__data.persistent().update(weak_updates).evolver()

        return storage

    def query(self, key):
        # type: (KT) -> VT
        """
        Query value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Value.

        :raises KeyError: Key is not in storage.
        """
        return self.__data[ref(key)]

    def evolver(self):
        # type: () -> StorageEvolver[KT, VT]
        """
        Get evolver.

        :return: Evolver.
        :rtype: StorageEvolver
        """
        return StorageEvolver(self)


def _unpickle_storage_evolver(storage, updates):
    # type: (Storage[KT, VT], Mapping[KT, VT]) -> StorageEvolver[KT, VT]
    evolver = StorageEvolver(storage)  # type: StorageEvolver[KT, VT]
    evolver.update(updates)
    return evolver


@final
class StorageEvolver(AbstractStorage[KT, VT]):
    """Mutable data storage evolver."""

    __slots__ = ("__storage", "__updates")

    def __init__(self, storage):
        self.__storage = storage  # type: Storage[KT, VT]
        self.__updates = pmap()  # type: PMap[KT, VT]

    def __reduce__(self):
        return _unpickle_storage_evolver, (self.__storage, self.__updates)

    def __deepcopy__(self, memo=None):
        # type: (Optional[Dict[int, Any]]) -> Storage[KT, VT]
        if memo is None:
            memo = {}
        try:
            deep_copy = memo[id(self)]
        except KeyError:
            deep_copy = memo[id(self)] = StorageEvolver.__new__(StorageEvolver)
            args_a = (self.__storage, memo)
            deep_copy.__storage = deepcopy(*args_a)
            args_b = (self.__updates, memo)
            deep_copy.__updates = deepcopy(*args_b)
        return deep_copy

    def __copy__(self):
        return self.fork()

    def to_dict(self):
        # type: () -> Dict[KT, VT]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[collections.abc.Hashable, Any]
        """
        return self.persistent().to_dict()

    def update(self, updates):
        # type: (_SE, Mapping[KT, VT]) -> _SE
        """
        Update keys and values in place.

        :param updates: Updates.
        :type updates: collections.abc.Mapping[collections.abc.Hashable, Any]

        :return: Itself.
        :rtype: StorageEvolver
        """
        self.__updates = self.__updates.update(updates)
        return self

    def query(self, key):
        # type: (KT) -> VT
        """
        Query value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Value.

        :raises KeyError: Key is not in storage.
        """
        try:
            return self.__updates[key]
        except KeyError:
            return self.__storage.query(key)

    def persistent(self):
        # type: () -> Storage[KT, VT]
        """
        Get immutable storage with current updates.

        :return: Storage.
        :rtype: Storage
        """
        return self.__storage.update(self.__updates)

    def fork(self):
        # type: () -> StorageEvolver[KT, VT]
        """
        Fork into another evolver.

        :return: Forked evolver.
        :rtype: StorageEvolver
        """
        evolver = StorageEvolver.__new__(StorageEvolver)
        evolver.__storage = self.__storage
        evolver.__updates = self.__updates
        return evolver

    def is_dirty(self):
        # type: () -> bool
        """
        Get whether has updates.

        :return: True if has updates.
        :rtype: bool
        """
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
        # type: () -> PMap[KT, VT]
        """
        Updates.

        :rtype: pyrsistent.PMap[collections.abc.Hashable, Any]
        """
        return self.__updates
