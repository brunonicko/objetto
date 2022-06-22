from __future__ import annotations

import abc
import contextvars
import contextlib
import dataclasses

import slotted
import registtro
import basicco.explicit_hash
import basicco.runtime_final
import pyrsistent
from pyrsistent.typing import PMap, PSet
from tippo import (
    TypeVar,
    Counter,
    Dict,
    Generic,
    Tuple,
    Optional,
    Iterable,
    Iterator,
    List,
    WeakSet,
    Set,
    ref,
    final,
)

from .exceptions import ContextError, NotInitializedError


_ST = TypeVar("_ST")  # state type


@final
class Snapshot:
    """Snapshot of object states."""

    __slots__ = ("__weakref__", "__event", "__registry", "__previous", "__followings")

    def __init__(self):
        self.__event = None
        self.__registry: registtro.Registry[Node, Entry] = registtro.Registry()
        self.__previous: Optional[ref[Snapshot]] = None
        self.__followings: Set[Snapshot] = set()

    def __get_entry(self, node: Node) -> Entry:
        try:
            return self.__registry.query(node)
        except registtro.EntryNotFoundError:
            raise NotInitializedError(f"{node.obj} not initialized") from None

    def initialize(
        self,
        obj: AbstractObject[_ST],
        state: _ST,
        adoptions: Dict["Hierarchy", Tuple[AbstractObject, ...]]
    ) -> Snapshot:
        """Initialize object with state and children and return a new snapshot."""

        children = pyrsistent.pmap({h: pyrsistent.pset(o.__node__ for o in os) for h, os in adoptions.items()})
        entry = Entry(state=state, children=children, parent_refs=pyrsistent.pmap())
        updates: Dict[Node, Entry] = {obj.__node__: entry}

        snapshot = Snapshot.__new__(Snapshot)
        snapshot.__event = None
        snapshot.__registry = self.__registry.update(updates)
        snapshot.__previous = ref(self)
        snapshot.__followings = set()

        return snapshot

    def get_state(self, obj: AbstractObject[_ST]) -> _ST:
        """Get object state."""
        return self.__get_entry(obj.__node__).state

    def get_children(self, obj: AbstractObject, hierarchy: "Hierarchy") -> List[AbstractObject]:
        """Get child objects."""
        child_nodes = self.__get_entry(obj.__node__).children.get(hierarchy, ())
        return sorted((n.obj for n in child_nodes), key=lambda o: id(o))

    def get_parent(self, obj: AbstractObject, hierarchy: "Hierarchy") -> Optional[AbstractObject]:
        """Get parent object."""
        parent_node_ref = self.__get_entry(obj.__node__).parent_refs.get(hierarchy, None)
        if parent_node_ref is None:
            return None
        parent_node = parent_node_ref()
        if parent_node is None:
            raise ReferenceError("parent is no longer in memory")
        return parent_node.obj

    def iter_up(self, obj: AbstractObject, hierarchy: "Hierarchy") -> Iterator[AbstractObject]:
        """Iterate over the hierarchy above, starting with the object itself."""
        yield obj
        parent = self.get_parent(obj, hierarchy)
        while parent is not None:
            yield parent
            parent = self.get_parent(parent, hierarchy)

    def iter_down(
        self,
        obj: AbstractObject,
        hierarchy: "Hierarchy",
        depth_first: bool = True,
    ) -> Iterator[AbstractObject]:
        """Iterate over the hierarchy below, starting with the object itself."""
        pass  # TODO

    def is_child(self, child: AbstractObject, parent: AbstractObject, hierarchy: "Hierarchy") -> bool:
        """Whether an object is a child of another object."""
        return child.__node__ in self.__get_entry(parent.__node__).children.get(hierarchy, ())

    def has_children(self, obj: AbstractObject, hierarchy: "Hierarchy") -> bool:
        """Whether object has children."""
        return bool(self.__get_entry(obj.__node__).children.get(hierarchy, ()))

    def has_parent(self, obj: AbstractObject, hierarchy: "Hierarchy") -> bool:
        """Whether object has a parent."""
        return self.get_parent(obj, hierarchy) is not None

    def has_state(self, obj: AbstractObject) -> bool:
        """Whether an object has state (was initialized)."""
        try:
            self.__get_entry(obj.__node__)
        except NotInitializedError:
            return False
        else:
            return True


@final
class Context:
    """Keeps track of snapshots."""

    __slots__ = ("__snapshots", "__frozen", "__pinned", "__acting")

    def __init__(self, initial_snapshot: Optional[Snapshot] = None):
        if initial_snapshot is None:
            initial_snapshot = Snapshot()
        self.__snapshots: List[Snapshot] = [initial_snapshot]
        self.__pinned: Counter[Node] = Counter()
        self.__acting: WeakSet[Node] = WeakSet()

    def get_snapshot(self) -> Snapshot:
        """Get current snapshot."""
        return self.__snapshots[-1]

    def initialize(
        self,
        obj: AbstractObject[_ST],
        state: _ST,
        adoptions: Dict["Hierarchy", Tuple[AbstractObject, ...]]
    ):
        """Initialize object with state and children."""
        snapshot = self.get_snapshot()
        self.__snapshots.append(snapshot.initialize(obj, state, adoptions))

    @property
    def initial_snapshot(self) -> Snapshot:
        """Initial snapshot."""
        return self.__snapshots[0]


_context: contextvars.ContextVar[Optional[Context]] = contextvars.ContextVar("_context", default=None)
"""Current context variable."""


@contextlib.contextmanager
def require_context() -> Iterator[Context]:
    """Enter the current context manager."""
    ctx: Optional[Context] = _context.get()
    if ctx is None:
        raise ContextError("not in a context")
    yield ctx


@contextlib.contextmanager
def context(snapshot: Optional[Snapshot] = None) -> Iterator[Context]:
    """Enter a new context based on a snapshot."""
    ctx = Context(snapshot)
    token = _context.set(ctx)
    try:
        yield ctx
    finally:
        _context.reset(token)


@final
class Hierarchy:
    """Hierarchy of weak parent/strong children objects."""

    __slots__ = ("__weakref__",)


@final
@dataclasses.dataclass(frozen=True)
class Entry(Generic[_ST]):
    state: _ST
    children: PMap[Hierarchy, PSet[Node]]
    parent_refs: PMap[Hierarchy, ref[Node]]


@final
class Node:
    __slots__ = ("__weakref__", "__obj_ref")

    @staticmethod
    def __new__(cls, obj: AbstractObject):
        try:
            return obj.__node__
        except AttributeError:
            return super().__new__(cls)

    def __init__(self, obj: AbstractObject):
        try:
            obj.__node__
        except AttributeError:
            self.__obj_ref: ref[AbstractObject] = ref(obj)

    @property
    def obj(self) -> AbstractObject:
        obj = self.__obj_ref()
        if obj is None:
            raise ReferenceError("object is no longer in memory")
        return obj


class AbstractObjectMeta(
    slotted.SlottedABCMeta,
    basicco.explicit_hash.ExplicitHashMeta,
    basicco.runtime_final.FinalizedMeta
):
    pass


class AbstractObject(slotted.SlottedABC, Generic[_ST], metaclass=AbstractObjectMeta):
    """Interface for accessing/manipulating state within a :meth:`context`."""

    __slots__ = ("__weakref__", "__node__")
    __hash__ = None  # type: ignore

    @classmethod
    @abc.abstractmethod
    def __init_state__(cls, *args, **kwargs) -> Tuple[_ST, Dict[Hierarchy, Tuple[AbstractObject, ...]]]:
        """
        *Abstract Class Method*
        Initialize state and children.
        Takes same arguments as `__init__`.

        :return: State and adoptions dictionary per hierarchy.
        """
        raise NotImplementedError()

    def __init__(self, *args, **kwargs):
        self.__node__ = Node(self)
        with require_context() as ctx:
            state, adoptions = self.__init_state__(*args, **kwargs)
            ctx.initialize(self, state, adoptions)
            self.__post_init__(*args, **kwargs)

    def __post_init__(self, *args, **kwargs):
        """
        Post-initialize.
        Takes same arguments as `__init__`.
        """
        pass


def objs_only(values: Iterable) -> Tuple[AbstractObject, ...]:
    """Filter objects only from values."""
    return tuple(v for v in values if isinstance(v, AbstractObject))
