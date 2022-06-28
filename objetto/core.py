import abc
import collections
import contextvars
import contextlib
import weakref
from typing import (
    Any,
    Optional,
    Iterator,
    Iterable,
    List,
    TypeVar,
    Generic,
    Mapping,
    Tuple,
    final,
)

import pyrsistent
from pyrsistent.typing import PMap, PSet

from .exceptions import (
    ContextError,
    NotInitializedError,
    AlreadyInitializedError,
    AlreadyActingError,
    HierarchyLockedError,
    AlreadyParentedError,
    ParentCycleError,
    NotAChildError,
    MultiParentError,
    MultiUnparentError,
)

__all__ = [
    "SlottedMeta",
    "Slotted",
    "Node",
    "Entry",
    "Context",
    "get_context",
    "Store",
    "AbstractObject",
]

T = TypeVar("T")


class SlottedMeta(type):
    """Metaclass. Enforces `__slots__`."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):
        if "__slots__" not in dct:
            dct = dict(dct)
            dct["__slots__"] = ()
        return super().__new__(mcs, name, bases, dct, **kwargs)


class Slotted(metaclass=SlottedMeta):
    """Enforces `__slots__` and adds `__weakref__` slot."""

    __slots__ = ("__weakref__",)


@final
class Node(Slotted):
    """Represents an object in a weak parent/strong children hierarchy."""

    __slots__ = ("__obj_ref",)

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


@final
class Entry(pyrsistent.PClass):
    """Holds an object's state and metadata."""

    state: Any = pyrsistent.field()
    children: PSet[Node] = pyrsistent.pset_field(Node)
    parent_ref: Optional[weakref.ref[Node]] = pyrsistent.field()


@final
class Context(Slotted):
    """Keeps track of store changes."""

    __slots__ = ("__stores", "__frozen", "__pinned", "__acting")

    def __init__(self, initial_store: "Store", frozen: bool = False):
        self.__stores: List[Store] = [initial_store]
        self.__frozen: bool = bool(frozen)
        self.__pinned: collections.Counter[Node] = collections.Counter()
        self.__acting: weakref.WeakSet[Node] = weakref.WeakSet()

    @contextlib.contextmanager
    def __acting_context(self, node: Node) -> Iterator[Tuple[Node, ...]]:

        # Mark node as acting.
        if node in self.__acting:
            raise AlreadyActingError(f"{node.obj} is already acting")
        self.__acting.add(node)

        # Pin hierarchy above the node.
        nodes: List[Node] = [node]
        hierarchy: List[Node] = []
        store = self.get_store()
        while nodes:
            child = nodes.pop()
            hierarchy.append(child)
            self.__pinned[child] += 1
            child_obj = child.obj
            if not store.has_state(child_obj):
                break
            parent_obj = store.get_parent(child_obj)
            if parent_obj is not None:
                nodes.append(parent_obj.__node__)

        try:

            # Yield the hierarchy as a tuple (node, parent node, grandparent node, ...).
            yield tuple(hierarchy)

        finally:

            # Unmark node as acting.
            self.__acting.remove(node)

            # Unpin the hierarchy above the node.
            while hierarchy:
                child = hierarchy.pop()
                self.__pinned[child] -= 1
                assert self.__pinned[child] >= 0
                if not self.__pinned[child]:
                    del self.__pinned[child]

    def __act(
        self,
        obj: "AbstractObject[T]",
        state: T,
        event: Any,
        adoptions: Iterable["AbstractObject"],
        releases: Iterable["AbstractObject"],
    ):
        if self.frozen:
            raise ContextError("context is frozen")

        node = obj.__node__
        with self.__acting_context(node) as hierarchy:

            # Get old store and whether object has state in it already.
            old_store = self.get_store()
            has_state = old_store.has_state(obj)

            # Get initial (unprocessed) adoptions and releases.
            adoptions = tuple(adoptions)
            releases = tuple(releases)

            # When event is None it means the object is being initialized.
            initializing = event is None
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

            # Get old children and weak reference to the parent.
            if has_state:
                old_entry = old_store.__get_entry__(node)
                old_children = old_entry.children
                parent_ref = old_entry.parent_ref
            else:
                old_children = pyrsistent.pset()
                parent_ref = None

            # Perform parenting checks.
            if child_changes:
                for child, count in child_changes.items():
                    if not count:
                        del child_changes[child]
                        continue
                    child_obj = child.obj

                    # Child parent hierarchy is pinned.
                    if self.__pinned.get(child, 0):
                        raise HierarchyLockedError(f"hierarchy is locked for {child_obj}")

                    # Adoption checks.
                    if count == 1:

                        # Child is already parented.
                        child_parent = old_store.get_parent(child_obj)
                        if child_parent is not None:
                            raise AlreadyParentedError(f"{child_obj} is already parented")

                        # Child not initialized.
                        if not old_store.has_state(child_obj):
                            raise NotInitializedError(f"f{child_obj} is not initialized")

                        # Parent cycle.
                        for parent in hierarchy:
                            if child is parent:
                                raise ParentCycleError(f"{child_obj}")

                    # Release checks.
                    elif count == -1:

                        # Not a child.
                        if child not in old_children:
                            raise NotAChildError(f"{child_obj} is not a child of f{obj}")

                    # Can't parent/unparent more than once.
                    elif count > 1:
                        raise MultiParentError(f"{child_obj} can't parented under f{obj} more than once")
                    elif count < -1:
                        raise MultiUnparentError(f"{child_obj} can't unparented from f{obj} more than once")

            # Compile child changes.
            if child_changes:
                release_nodes = pyrsistent.pset(c for c in child_changes if child_changes[c] == -1)
                adopt_nodes = pyrsistent.pset(c for c in child_changes if child_changes[c] == 1)
                children = old_children.difference(release_nodes).union(adopt_nodes)
                adoptions = tuple(n.obj for n in adopt_nodes)
                releases = tuple(n.obj for n in release_nodes)
            else:
                release_nodes = pyrsistent.pset()
                adopt_nodes = pyrsistent.pset()
                children = old_children
                adoptions = ()
                releases = ()

            # Prepare updates.
            new_entry = Entry(state=state, children=children, parent_ref=parent_ref)
            updates = {node: new_entry}
            if child_changes:
                for child in adopt_nodes:
                    child_entry = old_store.__get_entry__(child).set("parent_ref", node_ref)
                    updates[child] = child_entry
                for child in release_nodes:
                    pass

            # Get new store.
            new_store = old_store.__update__(updates)

            # Add commit.
            self.__stores.append(new_store)

    def get_store(self) -> "Store":
        """Get current store."""
        return self.__stores[-1]

    def init(self, obj: "AbstractObject[T]", state: T, adoptions: Iterable["AbstractObject"]):
        """Initialize object with state and children."""
        self.__act(obj=obj, state=state, event=None, adoptions=adoptions, releases=())

    def act(
        self,
        obj: "AbstractObject[T]",
        state: T,
        event: Any,
        adoptions: Iterable["AbstractObject"],
        releases: Iterable["AbstractObject"],
    ):
        """Act on an object's state."""
        self.__act(obj=obj, state=state, event=event, adoptions=adoptions, releases=releases)

    @property
    def initial_store(self) -> "Store":
        """Initial store."""
        return self.__stores[0]

    @property
    def frozen(self) -> bool:
        """Whether context doesn't allow actions to run."""
        return self.__frozen


_context: contextvars.ContextVar[Optional[Context]] = contextvars.ContextVar("_context", default=None)


@contextlib.contextmanager
def get_context(frozen: Optional[bool] = None) -> Iterator[Context]:
    ctx: Optional[Context] = _context.get()
    if ctx is None:
        raise ContextError("not in a context")
    if frozen is not None:
        if frozen and not ctx.frozen:
            raise ContextError("in a frozen context")
        if not frozen and ctx.frozen:
            raise ContextError("not in a frozen context")
    yield ctx


@final
class Store(Slotted):
    """Holds entries for multiple objects."""

    __slots__ = ("__entries",)  # TODO: keep track of previous store and event in a weak key dict

    def __init__(self):
        self.__entries: PMap[Node, Entry] = pyrsistent.pmap()

    def __update__(self, updates: Mapping[Node, Entry]) -> "Store":
        store = Store.__new__(Store)
        store.__entries = self.__entries.update(updates)
        return store

    def __get_entry__(self, node: Node) -> Entry:
        try:
            return self.__entries[node]
        except KeyError:
            raise NotInitializedError(f"{node.obj} not initialized") from None

    def __get_entry(self, obj: "AbstractObject") -> Entry:
        return self.__get_entry__(obj.__node__)

    @contextlib.contextmanager
    def context(self, frozen: bool = False) -> Iterator[Context]:
        """Context manager based on this store."""
        ctx: Context = Context(self, frozen)
        token = _context.set(ctx)
        try:
            yield ctx
        finally:
            _context.reset(token)

    def get_state(self, obj: "AbstractObject[T]") -> T:
        """Get state."""
        return self.__get_entry(obj).state

    def get_children(self, obj: "AbstractObject") -> List["AbstractObject"]:
        """Get child objects."""
        return sorted((n.obj for n in self.__get_entry(obj).children), key=lambda o: id(o))

    def get_parent(self, obj: "AbstractObject") -> Optional["AbstractObject"]:
        """Get parent object."""
        node_ref = self.__get_entry(obj).parent_ref
        if node_ref is None:
            return None
        node = node_ref()
        if node is None:
            raise ReferenceError("parent is no longer in memory")
        return node.obj

    def iter_up(self, obj: "AbstractObject") -> Iterator["AbstractObject"]:
        """Iterate over the hierarchy above, starting with the object itself."""
        yield obj
        parent = self.get_parent(obj)
        while parent is not None:
            yield parent
            parent = self.get_parent(parent)

    def iter_down(self, obj: "AbstractObject", depth_first: bool = True) -> Iterator["AbstractObject"]:
        """Iterate over the hierarchy below, starting with the object itself."""
        pass  # TODO

    def is_child(self, child: "AbstractObject", parent: "AbstractObject") -> bool:
        """Whether an object is a child of another object."""
        return child.__node__ in self.__get_entry(parent).children

    def has_children(self, obj: "AbstractObject") -> bool:
        """Whether object has children."""
        return bool(self.__get_entry(obj).children)

    def has_parent(self, obj: "AbstractObject") -> bool:
        """Whether object has a parent."""
        return self.get_parent(obj) is not None

    def has_state(self, obj: "AbstractObject") -> bool:
        """Whether an object has state (was initialized)."""
        return obj.__node__ in self.__entries


class AbstractObject(Slotted, Generic[T]):
    """Interface for accessing/manipulating state while in a store context."""

    __slots__ = ("__node__",)
    __hash__ = None  # type: ignore

    @classmethod
    @abc.abstractmethod
    def __init_state__(cls, *args, **kwargs) -> Tuple[T, Tuple["AbstractObject", ...]]:
        raise NotImplementedError()

    def __init__(self, *args, **kwargs):
        self.__node__ = Node(self)
        with get_context(frozen=False) as ctx:
            state, adoptions = self.__init_state__(*args, **kwargs)
            ctx.init(self, state, adoptions)
            self.__post_init__(*args, **kwargs)

    def __post_init__(self, *args, **kwargs):
        pass


def filter_objs(values: Iterable) -> Tuple[AbstractObject, ...]:
    """Filter objects from a values."""
    return tuple(v for v in values if isinstance(v, AbstractObject))
