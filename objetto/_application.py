# -*- coding: utf-8 -*-
"""Manages multiple objects under different contexts."""

from contextlib import contextmanager
from copy import deepcopy
from threading import RLock
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import string_types

from ._bases import Base, final
from ._data import BaseData, DataAttribute, InteractiveSetData
from ._states import BaseState
from .data import Data, data_attribute, data_dict_attribute, data_set_attribute
from .utils.subject_observer import Subject
from .utils.weak_reference import WeakReference

if TYPE_CHECKING:
    from typing import Any, Counter, Dict, List, Optional, Set, Tuple, Type, Iterator

    from ._history import HistoryObject
    from ._objects import BaseObject

__all__ = ["Application"]


class ApplicationLock(Base):
    """
    Re-entrant threading lock for thread-safe applications.

      - Can be deep copied and pickled.
    """

    __slots__ = ("__lock",)

    def __init__(self):
        # type: () -> None
        self.__lock = RLock()

    def __deepcopy__(self, memo=None):
        # type: (Optional[Dict[int, Any]]) -> ApplicationLock
        """
        Make a deep copy.

        :param memo: Memo dict.
        :return: Deep copy.
        """
        if memo is None:
            memo = {}
        try:
            deep_copy = memo[id(self)]
        except KeyError:
            deep_copy = memo[id(self)] = type(self)()
        return deep_copy

    def __enter__(self):
        """Enter lock context."""
        return self.__lock.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit lock context."""
        return self.__lock.__exit__(exc_type, exc_val, exc_tb)

    def __reduce__(self):
        # type: () -> Tuple[Type[ApplicationLock], Tuple]
        """
        Reduce for pickling.

        :return: Class and init arguments.
        """
        return type(self), ()


class ApplicationStorage(WeakKeyDictionary):
    """
    Application storage.

      - Holds a store for each object in the application.
      - Can be deep copied and pickled.
    """

    def __deepcopy__(self, memo=None):
        # type: (Optional[Dict[int, Any]]) -> ApplicationStorage
        """
        Make a deep copy.

        :param memo: Memo dict.
        :return: Deep copy.
        """
        if memo is None:
            memo = {}
        try:
            deep_copy = memo[id(self)]
        except KeyError:
            deep_copy = memo[id(self)] = type(self)()
            deep_copy_args = dict(self), memo
            deep_copy.update(deepcopy(*deep_copy_args))
        return deep_copy

    def __reduce__(self):
        # type: () -> Tuple[Type[ApplicationStorage], Tuple[Dict[BaseObject, Store]]]
        """
        Reduce for pickling.

        :return: Class and init arguments.
        """
        return type(self), (dict(self),)


class Store(Data):
    """Holds an object's state, data, metadata, hierarchy, and history information."""

    state = data_attribute(BaseState, subtypes=True, checked=False)

    data = data_attribute((BaseData, type(None)), subtypes=True, checked=False)

    metadata = data_dict_attribute(
        key_types=string_types, key_checked=False, checked=False
    )

    parent_ref = data_attribute(
        WeakReference, checked=False, default=WeakReference()
    )  # type: DataAttribute[WeakReference[BaseObject]]

    history_provider_ref = data_attribute(
        WeakReference, checked=False, default=WeakReference()
    )  # type: DataAttribute[WeakReference[BaseObject]]

    last_parent_history_ref = data_attribute(
        WeakReference, checked=False, default=WeakReference()
    )  # type: DataAttribute[WeakReference[HistoryObject]]

    history = data_attribute(
        (".._history|HistoryObject", type(None)), checked=False, default=None
    )  # type: DataAttribute[HistoryObject]

    children = data_set_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False
    )  # type: DataAttribute[InteractiveSetData[HistoryObject]]


class ApplicationInternals(Base):
    """Internals for :class:`Application`."""

    __slots__ = (
        "__app_ref",
        "__history_cls",
        "__lock",
        "__storage",
        "__busy_writing",
        "__busy_hierarchy",
        "__commits",
        "__reading",
        "__writing",
        "__subject",
    )

    def __init__(self, app):
        # type: (Application) -> None
        self.__app_ref = WeakReference(app)
        self.__history_cls = None  # type: Optional[HistoryObject]
        self.__lock = ApplicationLock()
        self.__storage = ApplicationStorage()
        self.__busy_writing = set()  # type: Set[BaseObject]
        self.__busy_hierarchy = collections_abc.Counter()  # type: Counter[BaseObject]
        self.__commits = []  # type: List[Commit]
        self.__reading = []  # type: List[Optional[BaseObject]]
        self.__writing = []  # type: List[Optional[BaseObject]]
        self.__subject = Subject()


class Application(Base):
    """
    Application.

      - Manages multiple objects under the same hierarchy.
      - Offers contexts for reading/writing/batch.
      - Reverts changes when an error occurs.
      - Manages action propagation, internally and externally.
    """

    __slots__ = ("__weakref__", "__")

    @final
    @contextmanager
    def read_context(self):
        # type: () -> Iterator
        """Read context."""
        with self.__.read_context():
            yield

    @final
    @contextmanager
    def write_context(self):
        # type: () -> Iterator
        """Write context."""
        with self.__.write_context():
            yield
