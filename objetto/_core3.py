import abc
import contextvars
import contextlib

import slotted
import registtro
import basicco.explicit_hash
from tippo import (
    Any, TypeVar, Counter, NamedTuple, Mapping, Generic, Tuple, Optional, Iterable, Iterator, List, WeakSet, ref, final
)
from pyrsistent.typing import PMap, PSet

from .exceptions import ContextError, NotInitializedError


_ST = TypeVar("_ST")  # state type


@final
class Snapshot:
    """Represents a snapshot of the states for multiple objects."""

    __slots__ = ("__event", "__registry")

    def __init__(
        self,
        event: Optional[NamedTuple] = None,
        registry: registtro.Registry["Node", "Entry"] = registtro.Registry()
    ):
        self.__event = event
        self.__registry: registtro.Registry[Node, Entry] = registry

    def get_entry(self, obj: "AbstractObject") -> "Entry":
        try:
            return self.__registry.query(obj.__node__)
        except registtro.EntryNotFoundError:
            raise NotInitializedError(f"{obj} not initialized") from None


@final
class Context:
    """Keeps track of snapshots."""

    __slots__ = ("__snapshots", "__frozen", "__pinned", "__acting")

    def __init__(self, initial_snapshot: Snapshot):
        self.__snapshots: List[Snapshot] = [initial_snapshot]
        self.__pinned: Counter[Node] = Counter()
        self.__acting: WeakSet[Node] = WeakSet()

    def get_snapshot(self) -> Snapshot:
        """Get current snapshot."""
        return self.__snapshots[-1]

    def initialize(self, obj: "AbstractObject[_ST]", state: _ST, adoptions: Iterable["AbstractObject"]):
        """Initialize object with state and children."""

    @property
    def initial_snapshot(self) -> Snapshot:
        """Initial snapshot."""
        return self.__snapshots[0]


_context: contextvars.ContextVar[Optional[Context]] = contextvars.ContextVar("_context", default=None)
"""Current context variable."""


@contextlib.contextmanager
def _current_context() -> Iterator[Context]:
    """Current context manager."""
    ctx: Optional[Context] = _context.get()
    if ctx is None:
        raise ContextError("not in a context")
    yield ctx


@final
class Hierarchy:
    __slots__ = ("__weakref__",)


@final
class Entry(NamedTuple):
    """Holds an object's state, children, and weak references to parents."""
    state: Any
    children: PMap[Hierarchy, PSet["Node"]]
    parent_refs: PMap[Hierarchy, ref["Node"]]


@final
class Node:
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
            self.__obj_ref: ref["AbstractObject"] = ref(obj)

    @property
    def obj(self) -> "AbstractObject":
        obj = self.__obj_ref()
        if obj is None:
            raise ReferenceError("object is no longer in memory")
        return obj


class AbstractObjectMeta(slotted.SlottedMeta, basicco.explicit_hash.ExplicitHashMeta):
    pass


class AbstractObject(Generic[_ST], metaclass=AbstractObjectMeta):
    """Interface for accessing/manipulating state within a context."""

    __slots__ = ("__weakref__", "__node__")
    __hash__ = None  # type: ignore

    @classmethod
    @abc.abstractmethod
    def __init_state__(cls, *args, **kwargs) -> Tuple[_ST, Mapping[Hierarchy, Tuple["AbstractObject", ...]]]:
        raise NotImplementedError()

    def __init__(self, *args, **kwargs):
        self.__node__ = Node(self)
        with _current_context() as context:
            state, adoptions = self.__init_state__(*args, **kwargs)
            context.initialize(self, state, adoptions)
            self.__post_init__(*args, **kwargs)

    def __post_init__(self, *args, **kwargs):
        pass


def objs_only(values: Iterable) -> Tuple[AbstractObject, ...]:
    """Filter objects only from values."""
    return tuple(v for v in values if isinstance(v, AbstractObject))
