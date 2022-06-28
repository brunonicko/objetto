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

from .exceptions import ContextError, NotInitializedError, AlreadyInitializedError, AlreadyActingError


_ST = TypeVar("_ST")  # state type


@final
@dataclasses.dataclass(frozen=True)
class _Entry(Generic[_ST]):
    """Entry for a node in a registry."""

    state: _ST
    """State."""

    all_child_nodes: PMap[Hierarchy, PSet[Node]]
    """Child nodes per hierarchy."""

    all_parent_node_refs: PMap[Hierarchy, ref[Node]]
    """Parent node weak reference per hierarchy."""

    def get_child_nodes(self, hierarchy: Hierarchy) -> PSet[Node]:
        """Get child nodes in a specific hierarchy."""
        return self.all_child_nodes.get(hierarchy, pyrsistent.pset())

    def get_parent_node(self, hierarchy: Hierarchy) -> Optional[Node]:
        """Get parent node in a specific hierarchy."""
        try:
            parent_node_ref = self.all_parent_node_refs[hierarchy]
        except KeyError:
            return None
        else:
            parent_node = parent_node_ref()
            if parent_node is None:
                raise ReferenceError("parent is no longer in memory")
            return parent_node

    def get_all_parent_nodes(self) -> PMap[Hierarchy, Node]:
        """Get all parent nodes mapped by each hierarchy."""
        all_parent_nodes: Dict[Hierarchy, Node] = {}
        for hierarchy in self.all_parent_node_refs:
            parent_node = self.get_parent_node(hierarchy)
            assert parent_node is not None
            all_parent_nodes[hierarchy] = parent_node
        return pyrsistent.pmap(all_parent_nodes)


@dataclasses.dataclass(frozen=True)
class Event:
    """Base event dataclass."""


@dataclasses.dataclass(frozen=True)
class ObjectInitialized(Event):
    """Event: object initialized."""


@final
@dataclasses.dataclass(frozen=True)
class Action(Generic[_ST]):
    """Describes an event."""

    obj: AbstractObject[_ST]
    """Object that changed."""

    event: Event
    """Event data."""

    all_adoptions: PMap[Hierarchy, Tuple[AbstractObject, ...]]
    """Adopted objects per hierarchy."""

    all_releases: PMap[Hierarchy, Tuple[AbstractObject, ...]]
    """Released objects per hierarchy."""

    old_state: Optional[_ST]
    """Old state or None if not initialized."""

    new_state: _ST
    """New state."""

    def get_adoptions(self, hierarchy: Hierarchy) -> Tuple[AbstractObject, ...]:
        """Adoptions that happened in a specific hierarchy."""
        return self.all_adoptions.get(hierarchy, ())

    def get_releases(self, hierarchy: Hierarchy) -> Tuple[AbstractObject, ...]:
        """Releases that happened in a specific hierarchy."""
        return self.all_releases.get(hierarchy, ())


@final
class Snapshot:
    """Snapshot of object states."""

    __slots__ = ("__weakref__", "__action", "__registry", "__previous_ref", "__followings")

    def __init__(self):
        self.__action: Optional[Action] = None  # action that generated this snapshot
        self.__registry: registtro.Registry[Node, _Entry] = registtro.Registry()  # registry of entries
        self.__previous_ref: Optional[ref[Snapshot]] = None  # weak reference to the snapshot that generated this one
        self.__followings: Set[Snapshot] = set()  # snapshots generated from this one

    def __evolve__(self, action: Action, registry: registtro.Registry[Node, _Entry]) -> Snapshot:
        """Evolve into a new snapshot."""

        # Make a new snapshot object.
        snapshot = Snapshot.__new__(Snapshot)
        snapshot.__action = action
        snapshot.__registry = registry
        snapshot.__previous_ref = ref(self)
        snapshot.__followings = set()

        # Keep track of it in this one.
        self.__followings.add(snapshot)

        return snapshot

    def __get_entry(self, node: Node) -> _Entry:
        """Get entry in the registry for a node."""
        try:
            return self.__registry.query(node)
        except registtro.EntryNotFoundError:
            raise NotInitializedError(f"{node.obj} not initialized") from None

    def get_state(self, obj: AbstractObject[_ST]) -> _ST:
        """Get state."""
        return self.__get_entry(obj.__node__).state

    def get_children(self, obj: AbstractObject, hierarchy: Hierarchy) -> Tuple[AbstractObject, ...]:
        """Get children in a specific hierarchy."""
        child_nodes = self.__get_entry(obj.__node__).get_child_nodes(hierarchy)
        return tuple(sorted((n.obj for n in child_nodes), key=lambda o: id(o)))

    def get_parent(self, obj: AbstractObject, hierarchy: Hierarchy) -> Optional[AbstractObject]:
        """Get parent in a specific hierarchy."""
        parent_node = self.__get_entry(obj.__node__).get_parent_node(hierarchy)
        if parent_node is None:
            return None
        else:
            return parent_node.obj

    def get_all_parents(self, obj: AbstractObject) -> PMap[Hierarchy, AbstractObject]:
        """Get all parents mapped by each hierarchy."""
        all_parent_nodes = self.__get_entry(obj.__node__).get_all_parent_nodes()
        all_parents: Dict[Hierarchy, AbstractObject] = {h: pn.obj for h, pn in all_parent_nodes.items()}
        return pyrsistent.pmap(all_parents)

    def get_all_children(self, obj: AbstractObject) -> PMap[Hierarchy, Tuple[AbstractObject, ...]]:
        """Get all children mapped by each hierarchy."""
        all_child_nodes = self.__get_entry(obj.__node__).all_child_nodes
        all_children: Dict[Hierarchy, Tuple[AbstractObject, ...]] = {
            h: tuple(sorted((cn.obj for cn in cns), key=lambda o: id(o))) for h, cns in all_child_nodes.items()
        }
        return pyrsistent.pmap(all_children)

    def iter_up(self, obj: AbstractObject, hierarchy: Hierarchy) -> Iterator[AbstractObject]:
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

    def is_child(self, child: AbstractObject, parent: AbstractObject, hierarchy: Hierarchy) -> bool:
        """Whether an object is a child of another object in a specific hierarchy."""
        return Node(child) in self.__get_entry(Node(parent)).all_child_nodes.get(hierarchy, pyrsistent.pset())

    def has_children(self, obj: AbstractObject, hierarchy: Hierarchy) -> bool:
        """Whether object has children in a specific hierarchy."""
        return bool(self.__get_entry(Node(obj)).all_child_nodes.get(hierarchy, pyrsistent.pset()))

    def has_parent(self, obj: AbstractObject, hierarchy: Hierarchy) -> bool:
        """Whether object has a parent in a specific hierarchy."""
        return self.get_parent(obj, hierarchy) is not None

    def has_state(self, obj: AbstractObject) -> bool:
        """Whether an object has state (was initialized)."""
        try:
            self.__get_entry(obj.__node__)
        except NotInitializedError:
            return False
        else:
            return True

    @property
    def action(self) -> Optional[Action]:
        """Action that generated this snapshot."""
        return self.__action


@final
class Context:
    """Keeps track of snapshots."""

    __slots__ = ("__snapshots", "__frozen", "__pinned", "__acting")

    def __init__(self, initial_snapshot: Optional[Snapshot] = None, frozen: bool = False):
        if initial_snapshot is None:
            initial_snapshot = Snapshot()
        self.__snapshots: List[Snapshot] = [initial_snapshot]
        self.__pinned: Counter[Node] = Counter()
        self.__acting: WeakSet[Node] = WeakSet()
        self.__frozen: bool = bool(frozen)

    @contextlib.contextmanager
    def __acting_context(self, node: Node) -> Iterator[PMap[Hierarchy, Tuple[Node, ...]]]:

        # Mark node as acting.
        if node in self.__acting:
            raise AlreadyActingError(f"{node.obj} is already acting")
        self.__acting.add(node)

        # Pin hierarchy above the node in all of its hierarchies.
        nodes: List[Node] = [node]
        pinned_nodes: Dict[Hierarchy, List[Node]] = {}
        snapshot = self.get_snapshot()
        while nodes:
            child = nodes.pop()
            pinned_nodes.append(child)
            self.__pinned[child] += 1
            child_obj = child.obj
            if not snapshot.has_state(child_obj):
                break
            parent_objs = snapshot.get_all_parents(child_obj)
            for hierarchy, parent_obj in parent_objs.items():
                if parent_obj is not None:
                    nodes.append(parent_obj.__node__)

        try:

            # Yield the flattened hierarchies as tuples (node, parent node, grandparent node, ...).
            yield tuple(hierarchy)

        finally:

            # Unmark node as acting.
            self.__acting.remove(node)

            # Unpin the hierarchy above the node in all hierarchies.
            while hierarchy:
                child = hierarchy.pop()
                self.__pinned[child] -= 1
                assert self.__pinned[child] >= 0
                if not self.__pinned[child]:
                    del self.__pinned[child]

    def __act(
        self,
        obj: AbstractObject[_ST],
        state: _ST,
        event: Event,
        adoptions: Dict[Hierarchy, Tuple[AbstractObject, ...]],
        releases: Dict[Hierarchy, Tuple[AbstractObject, ...]],
    ) -> None:

        # Can't act if context is frozen.
        if self.frozen:
            raise ContextError("context is frozen")

        # Get node and enter pinned hierarchy context.
        node = obj.__node__
        with self.__acting_context(node) as hierarchy:

            # Get previous snapshot and whether object has state in it already.
            previous_snapshot = self.get_snapshot()
            has_state = previous_snapshot.has_state(obj)

            # Check whether object has been initialized already depending on the event type.
            initializing = isinstance(event, InitializeEvent)
            if initializing:
                if has_state:
                    raise AlreadyInitializedError(f"{obj} already initialized")
                assert not releases
            elif not has_state:
                raise NotInitializedError(f"{obj} not initialized")

            # Count child changes.
            child_changes: collections.Counter[Node] = collections.Counter()
            for adoption in adoptions:
                child_changes[adoption.__node__] += 1
            for release in releases:
                child_changes[release.__node__] -= 1

        children = pyrsistent.pmap({h: pyrsistent.pset(o.__node__ for o in os) for h, os in adoptions.items()})
        entry = Entry(state=state, children=children, parent_refs=pyrsistent.pmap())
        updates: Dict[Node, Entry] = {obj.__node__: entry}

        registry = self.__registry.update(updates)
        event = InitializeEvent()
        action = Action(
            obj=obj,
            event=event,
            adoptions=pyrsistent.pmap(adoptions),
            releases=pyrsistent.pmap(),
            old_state=None,
            new_state=state,
        )

        evolution = self.__evolve(action, registry)
        return evolution

    def get_snapshot(self) -> Snapshot:
        """Get current snapshot."""
        return self.__snapshots[-1]

    def initialize(
        self,
        obj: AbstractObject[_ST],
        state: _ST,
        adoptions: Dict["Hierarchy", Tuple[AbstractObject, ...]],
    ):
        """Initialize object with state and children."""

        # Get node.
        node = obj.__node__

        # Mark node as acting.
        if node in self.__acting:
            raise AlreadyActingError(f"{node.obj} is already acting")
        self.__acting.add(node)

        # Pin node in the hierarchy.
        assert node not in self.__pinned
        self.__pinned[node] = 1

        #
        snapshot = self.get_snapshot()
        self.__snapshots.append(snapshot.__initialize__(obj, state, adoptions))

    @property
    def initial_snapshot(self) -> Snapshot:
        """Initial snapshot."""
        return self.__snapshots[0]

    @property
    def frozen(self) -> bool:
        """Whether context is frozen."""
        return self.__frozen


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
class Node(Generic[_ST]):
    __slots__ = ("__weakref__", "__obj_ref")

    @staticmethod
    def __new__(cls, obj: AbstractObject[_ST]):
        try:
            return obj.__node__
        except AttributeError:
            return super().__new__(cls)

    def __init__(self, obj: AbstractObject[_ST]):
        try:
            obj.__node__
        except AttributeError:
            self.__obj_ref: ref[AbstractObject[_ST]] = ref(obj)

    @property
    def obj(self) -> AbstractObject[_ST]:
        obj = self.__obj_ref()
        if obj is None:
            raise ReferenceError("object is no longer in memory")
        return obj


class AbstractObjectMeta(
    slotted.SlottedABCMeta,
    basicco.explicit_hash.ExplicitHashMeta,
    basicco.runtime_final.FinalizedMeta,
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
