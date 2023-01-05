from collections import Counter, OrderedDict
from contextlib import contextmanager
from weakref import ref, WeakSet

import six
import datta
from basicco import SlottedBaseMeta, SlottedBase
from basicco.get_mro import get_mro
from basicco.context_vars import ContextVar
from basicco.weak_reference import WeakReference
from basicco.runtime_final import final
from registtro import Registry, EntryNotFoundError
from estruttura import (
    BaseMutableCollectionStructure,
    BaseMutableStructure,
    BaseProxyMutableCollectionStructure,
    BaseProxyMutableStructure,
    BaseProxyStructureMeta,
    BaseProxyUserMutableCollectionStructure,
    BaseProxyUserMutableStructure,
    BaseStructureMeta,
    BaseUserMutableCollectionStructure,
    BaseUserMutableStructure,
)
from tippo import Any, TypeVar, Iterator, Generic, Mapping, Iterable

from ._relationship import Relationship
from .exceptions import (
    ContextError,
    AlreadyActingError,
    AlreadyInitializedError,
    HierarchyLockedError,
    AlreadyParentedError,
    NotInitializedError,
    ParentCycleError,
    NotAChildError,
    MultiParentError,
    MultiUnparentError,
)

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

_REACTION_TAG = "__isreactionmethod__"


_context = ContextVar("_context", default=None)  # type: ContextVar[Context | None]


def reaction(func):
    # type: (T) -> T
    """Reaction method decorator."""
    setattr(func, _REACTION_TAG, True)
    return func


class BaseEvent(datta.Data):
    """Base event."""

    __kw_only__ = True


class ObjectInitialized(BaseEvent):
    """Event: object initialized."""


@final
class Action(datta.Data):
    """Describes an event."""

    __kw_only__ = True

    obj = datta.attribute()  # type: BasePrivateObject
    event = datta.attribute()  # type: BaseEvent
    adoptions = datta.list_attribute()  # type: datta.ListData[BasePrivateObject]
    releases = datta.list_attribute()  # type: datta.ListData[BasePrivateObject]
    old_state = datta.attribute()  # type: Any
    new_state = datta.attribute()  # type: Any


@final
class _Entry(datta.Data):
    """Entry for a node in the registry."""

    __kw_only__ = True

    state = datta.attribute()  # type: Any
    child_nodes = datta.set_attribute()  # type: datta.SetData[Node]
    parent_node_ref = datta.attribute()  # type: ref[Node] | None

    def get_parent_node(self):
        # type: () -> Node | None
        """
        Get parent node.

        :return: Parent node or None.
        :raises ReferenceError: Parent no longer in memory.
        """
        if self.parent_node_ref is None:
            return None
        parent_node = self.parent_node_ref()
        if parent_node is None:
            raise ReferenceError("parent is no longer in memory")
        return parent_node


@final
class Snapshot(SlottedBase):
    """Snapshot of object states."""

    __slots__ = ("__action", "__registry", "__previous_ref", "__followings")

    def __init__(self):
        # type: () -> None
        self.__action = None  # type: Action | None
        self.__registry = Registry()  # type: Registry[Node, _Entry]
        self.__previous_ref = None  # type: ref[Snapshot] | None
        self.__followings = []  # type: list[Snapshot]

    def __evolve__(self, action, updates):
        # type: (Action, Mapping[Node, _Entry]) -> Snapshot
        """Evolve into a new snapshot."""

        # Make a new snapshot object.
        snapshot = Snapshot.__new__(Snapshot)
        snapshot.__action = action
        snapshot.__registry = self.__registry.update(updates)
        snapshot.__previous_ref = ref(self)
        snapshot.__followings = []

        # Keep track of the new snapshot in this one.
        self.__followings.append(snapshot)

        return snapshot

    def __get_entry__(self, node):
        # type: (Node) -> _Entry
        """Get entry in the registry for a node."""
        try:
            return self.__registry.query(node)
        except EntryNotFoundError:
            error = "{!r} not initialized".format(node.obj)
            exc = NotInitializedError(error)
            six.raise_from(exc, None)
            raise exc

    def get_state(self, obj):
        # type: (BasePrivateObject) -> Any
        """Get state."""
        return self.__get_entry__(Node(obj)).state

    def get_children(self, obj):
        # type: (BasePrivateObject) -> tuple[BasePrivateObject, ...]
        """Get children."""
        child_nodes = self.__get_entry__(Node(obj)).child_nodes
        return tuple(sorted((n.obj for n in child_nodes), key=lambda o: id(o)))

    def get_parent(self, obj):
        # type: (BasePrivateObject) -> BasePrivateObject | None
        """Get parent."""
        parent_node = self.__get_entry__(Node(obj)).get_parent_node()
        if parent_node is None:
            return None
        else:
            return parent_node.obj

    def iter_up(self, obj):
        # type: (BasePrivateObject) -> Iterator[BasePrivateObject]
        """Iterate over the hierarchy above, starting with the object itself."""
        yield obj
        parent = self.get_parent(obj)
        while parent is not None:
            yield parent
            parent = self.get_parent(parent)

    def is_child(self, child, parent):
        # type: (BasePrivateObject, BasePrivateObject) -> bool
        """Whether an object is a child of another object in a specific hierarchy."""
        return Node(child) in self.__get_entry__(Node(parent)).child_nodes

    def has_children(self, obj):
        # type: (BasePrivateObject) -> bool
        """Whether object has children in a specific hierarchy."""
        return bool(self.__get_entry__(Node(obj)).child_nodes)

    def has_parent(self, obj):
        # type: (BasePrivateObject) -> bool
        """Whether object has a parent in a specific hierarchy."""
        return self.__get_entry__(Node(obj)).get_parent_node() is not None

    def has_state(self, obj):
        # type: (BasePrivateObject) -> bool
        """Whether an object has state (was initialized)."""
        try:
            self.__get_entry__(Node(obj))
        except NotInitializedError:
            return False
        else:
            return True

    def get_previous(self):
        # type: () -> Snapshot | None
        """Get previous snapshot (which generated this one)."""
        if self.__previous_ref is None:
            return None
        previous = self.__previous_ref()
        if previous is None:
            raise ReferenceError("previous snapshot is no longer in memory")
        return previous

    def get_followings(self):
        # type: () -> tuple[Snapshot, ...]
        """Get following snapshots (generated from this one)."""
        return tuple(self.__followings)

    @property
    def action(self):
        # type: () -> Action | None
        """Action that generated this snapshot."""
        return self.__action


@final
class Context(SlottedBase):
    """Keeps track of snapshots."""

    __slots__ = ("__snapshots", "__frozen", "__pinned", "__acting")

    def __init__(self, initial_snapshot=None, frozen=False):
        # type: (Snapshot | None, bool) -> None

        # Start with blank snapshot if not specified.
        if initial_snapshot is None:
            initial_snapshot = Snapshot()

        self.__snapshots = [initial_snapshot]  # type: list[Snapshot]
        self.__pinned = Counter()  # type: Counter[Node]
        self.__acting = WeakSet()  # type: WeakSet[Node]
        self.__frozen = bool(frozen)  # type: bool

    @contextmanager
    def __acting_context(self, node):
        # type: (Node) -> Iterator[tuple[Node, ...]]
        """Context manager that marks a node as acting (errors out if already acting) and pins its parent nodes."""

        # Check if node is already acting.
        if node in self.__acting:
            error = "{!r} is already acting".format(node.obj)
            raise AlreadyActingError(error)

        # Get the current snapshot.
        snapshot = self.get_snapshot()

        # Mark node as acting and pin it.
        self.__acting.add(node)

        # Pin all the node's parents and grand parents.
        nodes = [node]  # type: list[Node]
        pinned_nodes = []  # type: list[Node]
        while nodes:
            child = nodes.pop()
            pinned_nodes.append(child)
            self.__pinned[child] += 1
            try:
                child_entry = snapshot.__get_entry__(child)
            except NotInitializedError:
                break
            parent_node = child_entry.get_parent_node()
            if parent_node is not None:
                nodes.append(parent_node)

        try:

            # Yield the pinned nodes.
            yield tuple(pinned_nodes)

        finally:

            # Unmark node as acting and unpin it.
            self.__acting.remove(node)

            # Unpin the hierarchy above the node in all hierarchies.
            while pinned_nodes:
                child = pinned_nodes.pop()
                self.__pinned[child] -= 1
                if not self.__pinned[child]:
                    del self.__pinned[child]

    def __act(self, obj, state, event, adoptions, releases):
        # type: (BasePrivateObject, Any, BaseEvent, tuple[BasePrivateObject, ...], tuple[BasePrivateObject, ...]) -> None
        """Perform action."""

        # Can't act if context is frozen.
        if self.frozen:
            raise ContextError("context is frozen")

        # Get node and enter acting context.
        node = Node(obj)
        with self.__acting_context(node) as pinned_nodes:

            # Get current snapshot and whether object has state in it already.
            current_snapshot = self.get_snapshot()
            has_state = current_snapshot.has_state(obj)

            # Check whether object has been initialized already depending on the event type.
            initializing = isinstance(event, ObjectInitialized)
            if initializing:
                if has_state:
                    raise AlreadyInitializedError("{!r} already initialized".format(obj))
                assert not releases
            elif not has_state:
                raise NotInitializedError("{!r} not initialized".format(obj))

            # Count child changes.
            child_changes = Counter()  # type: Counter[Node]
            for adoption in adoptions:
                child_changes[Node(adoption)] += 1
            for release in releases:
                child_changes[Node(release)] -= 1

            # Get old children and parent references.
            if has_state:
                previous_entry = current_snapshot.__get_entry__(node)
                previous_state = previous_entry.state
                previous_child_nodes = previous_entry.child_nodes
                parent_node_ref = previous_entry.parent_node_ref
            else:
                previous_state = None
                previous_child_nodes = datta.SetData()
                parent_node_ref = None

            # Perform parenting checks.
            for child, count in list(six.iteritems(child_changes)):

                # Skip if no changes for this child.
                if not count:
                    del child_changes[child]
                    continue

                # Get child object.
                child_obj = child.obj

                # Child parent hierarchy is pinned.
                if self.__pinned.get(child, 0):
                    error = "hierarchy is locked for {!r}".format(child_obj)
                    raise HierarchyLockedError(error)

                # Adoption checks.
                if count == 1:

                    # Child is already parented.
                    child_parent = current_snapshot.get_parent(child_obj)
                    if child_parent is not None:
                        error = "{!r} is already parented".format(child_obj)
                        raise AlreadyParentedError(error)

                    # Child not initialized.
                    if not current_snapshot.has_state(child_obj):
                        error = "{!r} is not initialized".format(child_obj)
                        raise NotInitializedError(error)

                    # Parent cycle.
                    for parent in pinned_nodes:
                        if child is parent:
                            error = "{!r}".format(child_obj)
                            raise ParentCycleError(error)

                # Release checks.
                elif count == -1:

                    # Not a child.
                    if child not in previous_child_nodes:
                        error = "{!r} is not a child of {!r}".format(child_obj, obj)
                        raise NotAChildError(error)

                # Can't parent/unparent more than once.
                elif count > 1:
                    error = "{!r} can't be parented under {!r} more than once".format(child_obj, obj)
                    raise MultiParentError(error)
                elif count < -1:
                    error = "{!r} can't be unparented from {!r} more than once".format(child_obj, obj)
                    raise MultiUnparentError(error)

            # Compile child changes for this hierarchy.
            release_nodes = {c for c in child_changes if child_changes[c] == -1}
            adopt_nodes = {c for c in child_changes if child_changes[c] == 1}
            child_nodes = set(previous_child_nodes).difference(release_nodes).union(adopt_nodes)

            # Prepare action.
            action = Action(
                obj=obj,
                event=event,
                adoptions=adoptions,
                releases=releases,
                old_state=previous_state,
                new_state=state,
            )

            # Run pre reactions.
            if not initializing:
                for reacting_node in pinned_nodes:
                    reacting_obj = reacting_node.obj
                    for reaction_name in type(reacting_obj).reactions:
                        getattr(reacting_obj, reaction_name)(action, "PRE")

            # Commit new entry as a new snapshot.
            entry = _Entry(
                state=state,
                child_nodes=child_nodes,
                parent_node_ref=parent_node_ref,
            )
            current_snapshot = self.get_snapshot()
            updates = {Node(obj): entry}  # type: dict[Node, _Entry]

            for release_node in release_nodes:
                release_entry = current_snapshot.__get_entry__(release_node)
                updates[release_node] = release_entry.set("parent_node_ref", None)
            for adopt_node in adopt_nodes:
                adoption_entry = current_snapshot.__get_entry__(adopt_node)
                updates[adopt_node] = adoption_entry.set("parent_node_ref", ref(node))

            new_snapshot = self.get_snapshot().__evolve__(action, updates)
            self.__snapshots.append(new_snapshot)

            # Run post reactions.
            if not initializing:
                for reacting_node in pinned_nodes:
                    reacting_obj = reacting_node.obj
                    for reaction_name in type(reacting_obj).reactions:
                        getattr(reacting_obj, reaction_name)(action, "POST")

    def get_snapshot(self) -> Snapshot:
        """Get current snapshot."""
        return self.__snapshots[-1]

    def initialize(self, obj, state, adoptions):
        # type: (BasePrivateObject, Any, tuple[BasePrivateObject, ...]) -> None
        """Initialize object with state and children."""
        self.__act(obj, state, ObjectInitialized(), adoptions, ())

    def update(
        self,
        obj,  # type: BasePrivateObject
        state,  # type: Any
        event,  # type: BaseEvent
        adoptions,  # type: tuple[BasePrivateObject, ...]
        releases,  # type: tuple[BasePrivateObject, ...]
    ):
        # type: (...) -> None
        """Update object with new state, child adoptions and releases."""
        assert not isinstance(event, ObjectInitialized)
        self.__act(obj, state, event, adoptions, releases)

    @property
    def initial_snapshot(self):
        # type: () -> Snapshot
        """Initial snapshot."""
        return self.__snapshots[0]

    @property
    def frozen(self):
        # type: () -> bool
        """Whether context is frozen."""
        return self.__frozen


@contextmanager
def require_context():
    # type: () -> Iterator[Context]
    """Enter the current context manager."""
    ctx = _context.get()  # type: Context | None
    if ctx is None:
        raise ContextError("not in a context")
    yield ctx


@contextmanager
def context(snapshot=None):
    # type: (Snapshot | None) -> Iterator[Context]
    """Enter a new context based on a snapshot."""
    ctx = Context(snapshot)
    token = _context.set(ctx)
    try:
        yield ctx
    finally:
        _context.reset(token)


class BaseObjectMeta(BaseStructureMeta):
    """Metaclass for :class:`BasePrivateObject`."""

    def __init__(cls, name, bases, dct, **kwargs):  # noqa
        super().__init__(name, bases, dct, **kwargs)

        # Look for reaction methods.
        reaction_names = OrderedDict()
        for base in reversed(get_mro(cls)):
            for member_name, member in base.__dict__.items():
                reaction_names.pop(member_name, None)
                if callable(member) and getattr(member, _REACTION_TAG, None) is True:
                    reaction_names[member_name] = member

        cls.__reactionmethods__ = tuple(reaction_names)

    @property
    def reactions(cls):  # noqa
        # type: () -> tuple[str, ...]
        return cls.__reactionmethods__


# noinspection PyAbstractClass
class BasePrivateObject(six.with_metaclass(BaseObjectMeta, BaseMutableStructure)):
    """Base private object."""

    __slots__ = ("__node",)

    @property
    def __node__(self):
        # type: (BPO) -> Node[BPO]
        """Node."""
        try:
            return self.__node  # type: ignore
        except AttributeError:
            self.__node = Node.__new__(Node)
            self.__node.__init__(self)  # type: ignore
            return self.__node

    @property
    def _state(self):
        # type: () -> Any
        """State."""
        with require_context() as ctx:
            return ctx.get_snapshot().get_state(self)


BPO = TypeVar("BPO", bound=BasePrivateObject)  # base private object self type


# noinspection PyAbstractClass
class BaseObject(BasePrivateObject, BaseUserMutableStructure):
    """Base object."""

    __slots__ = ()


BO = TypeVar("BO", bound=BaseObject)  # base object self type


class BaseProxyObjectMeta(BaseObjectMeta, BaseProxyStructureMeta):
    """Metaclass for :class:`BaseProxyPrivateObject`."""


# noinspection PyAbstractClass
class BaseProxyPrivateObject(
    six.with_metaclass(BaseProxyObjectMeta, BaseProxyMutableStructure[BPO], BasePrivateObject)
):
    """Base proxy private object."""

    __slots__ = ()

    @property
    def _state(self):
        # type: () -> Any
        """State."""
        return self.__wrapped__._state


# noinspection PyAbstractClass
class BaseProxyObject(BaseProxyPrivateObject[BO], BaseProxyUserMutableStructure[BO], BaseObject):
    """Base proxy object."""

    __slots__ = ()


# noinspection PyAbstractClass
class PrivateCollectionObject(BasePrivateObject, BaseMutableCollectionStructure[T_co]):
    """Private collection object."""

    __slots__ = ()
    relationship = Relationship()  # type: Relationship[T_co]


PCO = TypeVar("PCO", bound=PrivateCollectionObject)  # private collection object self type


# noinspection PyAbstractClass
class CollectionObject(PrivateCollectionObject[T_co], BaseUserMutableCollectionStructure[T_co]):
    """Base collection object."""

    __slots__ = ()


CO = TypeVar("CO", bound=CollectionObject)  # collection object self type


# noinspection PyAbstractClass
class ProxyPrivateCollectionObject(
    BaseProxyPrivateObject[PCO],
    BaseProxyMutableCollectionStructure[PCO, T_co],
    PrivateCollectionObject[T_co],
):
    """Proxy private collection object."""

    __slots__ = ()


# noinspection PyAbstractClass
class ProxyCollectionObject(
    ProxyPrivateCollectionObject[CO, T_co],
    BaseProxyUserMutableCollectionStructure[CO, T_co],
    CollectionObject[T_co],
):
    """Proxy collection object."""

    __slots__ = ()


class NodeMeta(SlottedBaseMeta):
    """Metaclass for :class:`Node`."""

    def __call__(cls, obj):  # noqa
        """
        Enforce a singleton pattern (one node per object).

        :param obj: Object.
        :return: Node.
        """
        try:
            return obj.__node__
        except AttributeError:
            return super(NodeMeta, cls).__call__(obj)


@final
class Node(six.with_metaclass(NodeMeta, SlottedBase, Generic[BPO])):
    """Represents an object in the hierarchy."""

    __slots__ = ("__obj_ref",)

    def __init__(self, obj):
        # type: (BPO) -> None
        """
        :param obj: Object.
        """
        self.__obj_ref = WeakReference(obj)

    @property
    def obj(self):
        # type: () -> BPO
        """Object."""
        obj = self.__obj_ref()
        if obj is None:
            error = "object is no longer in memory"
            raise ReferenceError(error)
        return obj


def objs_only(values):
    # type: (Iterable) -> tuple[BasePrivateObject, ...]
    """Filter objects only from values."""
    return tuple(v for v in values if isinstance(v, BasePrivateObject))
