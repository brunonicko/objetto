import abc
import collections
import weakref
import contextvars
import contextlib
from typing import Any, Optional, Generic, Iterator, List, Iterable, TypeVar, Tuple, NamedTuple, final

import slotted
from pyrsistent.typing import PSet

from .exceptions import ContextError, NotInitializedError


_ST = TypeVar("_ST")
"""State type."""


@final
class _Entry(NamedTuple):
    """Holds an object's state, children, and weak reference to parent node."""
    state: Any
    children: PSet["_Node"]
    parent_ref: Optional[weakref.ref["_Node"]]


@final
class _Store:
    """Represents a snapshot of the states for multiple objects."""

    __slots__ = ("__event",)

    def __init__(self, event: Optional[NamedTuple] = None):
        self.__event = event

    def get_entry(self, obj: "AbstractObject") -> _Entry:
        try:
            return obj.__entries__[self]
        except KeyError:
            raise NotInitializedError(f"{obj} not initialized") from None


@final
class _Context:
    """Keeps track of store changes."""

    __slots__ = ("__stores", "__frozen", "__pinned", "__acting")

    def __init__(self, initial_store: _Store):
        self.__stores: List[_Store] = [initial_store]
        self.__pinned: collections.Counter[_Node] = collections.Counter()
        self.__acting: weakref.WeakSet[_Node] = weakref.WeakSet()

    def get_store(self) -> "_Store":
        """Get current store."""
        return self.__stores[-1]

    def initialize(self, obj: "AbstractObject[_ST]", state: _ST, adoptions: Iterable["AbstractObject"]):
        """Initialize object with state and children."""

    @property
    def initial_store(self) -> "_Store":
        """Initial store."""
        return self.__stores[0]


_context: contextvars.ContextVar[Optional[_Context]] = contextvars.ContextVar("_context", default=None)
"""Current context variable."""


@contextlib.contextmanager
def current_context() -> Iterator[_Context]:
    """Current context manager."""
    ctx: Optional[_Context] = _context.get()
    if ctx is None:
        raise ContextError("not in a context")
    yield ctx


@final
class _Node:
    """Represents an object in a weak parent/strong children hierarchy."""

    __slots__ = ("__weakref__", "__obj_ref")

    @staticmethod
    def __new__(cls, obj: "AbstractObject"):
        try:
            return obj.__node__
        except AttributeError:
            return super().__new__(cls)

    def __init__(self, obj: "AbstractObject"):
        try:
            obj.__node__
        except AttributeError:
            self.__obj_ref: weakref.ref["AbstractObject"] = weakref.ref(obj)

    @property
    def obj(self) -> "AbstractObject":
        obj = self.__obj_ref()
        if obj is None:
            raise ReferenceError("object is no longer in memory")
        return obj


class AbstractObject(Generic[_ST], metaclass=slotted.SlottedMeta):
    """Interface for accessing/manipulating state within a context."""

    __slots__ = ("__weakref__", "__node__")
    __hash__ = None  # type: ignore

    @classmethod
    @abc.abstractmethod
    def __init_state__(cls, *args, **kwargs) -> Tuple[_ST, Tuple["AbstractObject", ...]]:
        raise NotImplementedError()

    def __init__(self, *args, **kwargs):
        self.__node__ = _Node(self)
        with current_context() as context:
            state, adoptions = self.__init_state__(*args, **kwargs)
            context.initialize(self, state, adoptions)
            self.__post_init__(*args, **kwargs)

    def __post_init__(self, *args, **kwargs):
        pass


def objs_only(values: Iterable) -> Tuple[AbstractObject, ...]:
    """Filter objects only from values."""
    return tuple(v for v in values if isinstance(v, AbstractObject))
