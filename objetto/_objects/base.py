# -*- coding: utf-8 -*-
"""Base object."""

from abc import abstractmethod
from contextlib import contextmanager
from weakref import ref
from six import with_metaclass, iteritems
from typing import FrozenSet, ContextManager, Optional, Type, Tuple, Any, Dict, cast
from slotted import SlottedABCMeta, SlottedABC, Slotted

from .._base.constants import DEAD_WEAKREF
from .._components.events import (
    EventPhase,
    Event,
    field,
    Broadcaster,
    EventListenerMixin,
    EventEmitter,
)
from .._components.hierarchy import (
    Hierarchy,
    HierarchicalMixin,
    HierarchyAccess,
    ChildrenUpdates,
)
from .._components.history import UndoableCommand, History

from ..utils.partial import Partial

__all__ = [
    "BaseObjectEvent",
    "HistoryDescriptor",
    "BaseObjectMeta",
    "BaseObject",
    "BaseObjectCommand",
]


class BaseObjectEvent(Event):
    """Base object event. Describes the adoption and/or release of child objects."""

    obj = field()
    adoptions = field()
    releases = field()


class BaseObjectHierarchy(Hierarchy):
    """BaseObject hierarchy."""

    def update_children(self, children_updates):
        # type: (ChildrenUpdates) -> None
        """Perform children adoptions and/or releases."""
        for adoption in children_updates.adoptions:
            adoption = cast(BaseObject, adoption)
            parent = cast(BaseObject, self.obj)
            last_parent_history = adoption.__get_last_parent_history__()
            parent_history = parent.__get_history__()
            if last_parent_history is not parent_history:
                if last_parent_history is not None:
                    last_parent_history.flush()
                adoption.__set_last_parent_history__(parent_history)
        super(BaseObjectHierarchy, self).update_children(children_updates)


class HistoryDescriptor(Slotted):
    """Descriptor that gives access to a obj's command history."""

    __slots__ = ("__size",)

    def __init__(self, size=0):
        # type: (int) -> None
        """Initialize with size."""
        size = int(size)
        if size < -1:
            size = -1
        self.__size = size

    def __get__(self, obj, obj_cls=None):
        # type: (Optional[BaseObject], Optional[Type[BaseObject]]) -> Any
        """Descriptor 'get' access."""
        if obj is None:
            return self
        if not obj.__initialized__:
            raise AttributeError(
                "can't access history before instance is fully initialized"
            )
        return obj.__get_history__()

    def __set__(self, obj, value):
        # type: (BaseObject, Any) -> None
        """Descriptor 'set' access."""
        error = "attribute is read-only"
        raise AttributeError(error)

    def __delete__(self, obj):
        # type: (BaseObject) -> None
        """Descriptor 'delete' access."""
        error = "attribute is read-only"
        raise AttributeError(error)

    @property
    def size(self):
        # type: () -> int
        """History size."""
        return self.__size


def _make_base_object_class(
    mcs,  # type: Type[BaseObjectMeta]
    name,  # type: str
    bases,  # type: Tuple[Type, ...]
    dct,  # type: Dict[str, Any]
):
    # type: (...) -> BaseObjectMeta
    """Make obj class/subclass."""
    dct = dict(dct)

    # Init 'history_descriptor'
    dct["__history_descriptor__"] = None

    # Make sure hash is the object hash
    def __hash__(self):
        return object.__hash__(self)

    dct["__hash__"] = __hash__

    # Make class
    cls = super(BaseObjectMeta, mcs).__new__(mcs, name, bases, dct)

    # Find a history descriptor
    for base in cls.__mro__:
        if base is not cls and isinstance(base, BaseObjectMeta):
            if base.__history_descriptor__ is not None:
                type.__setattr__(
                    cls, "__history_descriptor__", base.__history_descriptor__
                )
                break
            continue
        else:
            for member_name, member in iteritems(base.__dict__):
                if isinstance(member, HistoryDescriptor):
                    type.__setattr__(cls, "__history_descriptor__", member)
                    break
            else:
                continue
        break

    return cls


class BaseObjectMeta(SlottedABCMeta):
    """Metaclass for 'BaseObject'."""

    __new__ = staticmethod(_make_base_object_class)
    __history_descriptor__ = None  # type: Optional[HistoryDescriptor]

    def __call__(cls, *args, **kwargs):
        """Make an instance an initialize it."""

        # Make an instance
        self = cls.__new__(cls, *args, **kwargs)

        # Mark as not initialized
        self.__initialized__ = False

        # Initialize it
        self.__pre_init__()
        self.__init__(*args, **kwargs)

        # Post initialize history
        if cls.history_descriptor is not None:
            self.__post_initialize_history__()

        # Mark as initialized
        self.__initialized__ = True

        return self

    def __setattr__(cls, name, value):
        # type: (str, Any) -> None
        """Prevent class attribute setting."""
        if name not in SlottedABC.__dict__:
            error = "'{}' class attributes are read-only".format(cls.__name__)
            raise AttributeError(error)
        super(BaseObjectMeta, cls).__setattr__(name, value)

    def __delattr__(cls, name):
        # type: (str) -> None
        """Prevent class attribute deleting."""
        if name not in SlottedABC.__dict__:
            error = "'{}' class attributes are read-only".format(cls.__name__)
            raise AttributeError(error)
        super(BaseObjectMeta, cls).__delattr__(name)

    @property
    def history_descriptor(cls):
        # type: () -> Optional[HistoryDescriptor]
        """History descriptor."""
        return cls.__history_descriptor__


class BaseObject(
    with_metaclass(BaseObjectMeta, HierarchicalMixin, EventListenerMixin, SlottedABC)
):
    """Abstract obj."""

    __slots__ = (
        "__initialized__",
        "__history",
        "__history_provider_ref",
        "__hierarchy",
        "__hierarchy_access",
        "__broadcaster",
        "__last_parent_history_ref",
    )

    def __pre_init__(self):
        """Pre-initialize."""
        if type(self).history_descriptor is not None:
            self.__history = History(size=0)
            self.__history_provider_ref = ref(self)
        else:
            self.__history = None
            self.__history_provider_ref = DEAD_WEAKREF
        self.__hierarchy = BaseObjectHierarchy(self)
        self.__hierarchy_access = HierarchyAccess(self.__hierarchy)
        self.__broadcaster = Broadcaster()
        self.__last_parent_history_ref = DEAD_WEAKREF

    def __getattr__(self, name):
        # type: (str) -> Any
        """Raise informative exception if missed call to super's '__init__'."""
        if name in BaseObject.__members__:
            error = (
                "missing attribute '{}', maybe super-class '__init__' of type '{}' "
                "was never called?"
            ).format(type(self).__name__)
            raise RuntimeError(error)
        return self.__getattribute__(name)

    @abstractmethod
    def __repr__(self):
        # type: () -> str
        """Get representation."""
        raise NotImplementedError()

    @abstractmethod
    def __str__(self):
        # type: () -> str
        """Get string representation."""
        raise NotImplementedError()

    @abstractmethod
    def __eq__(self, other):
        # type: (BaseObject) -> bool
        """Compare for equality."""
        raise NotImplementedError()

    def __ne__(self, other):
        # type: (BaseObject) -> bool
        """Compare for inequality."""
        return not self.__eq__(other)

    def __get_hierarchy__(self):
        # type: () -> Hierarchy
        """Get hierarchy."""
        return self.__hierarchy

    def __get_history__(self):
        # type: () -> Optional[History]
        """Get command history."""
        if self.__history is not None:
            return self.__history
        provider = self.__history_provider_ref()
        if provider is not None:
            return provider.__get_history__()

    def __post_initialize_history__(self):
        # type: () -> None
        """Post-initialize history properties."""
        self.__history.size = type(self).history_descriptor.size

    def __get_last_parent_history__(self):
        # type: () -> Optional[History]
        """Get last parent history."""
        return self.__last_parent_history_ref()

    def __set_last_parent_history__(self, last_parent_history):
        # type: (Optional[History]) -> None
        """Set last parent history."""
        if last_parent_history is None:
            self.__last_parent_history_ref = DEAD_WEAKREF
        else:
            self.__last_parent_history_ref = ref(last_parent_history)

    def __dispatch__(
        self,
        name,  # type: str
        redo,  # type: Partial
        redo_event,  # type: BaseObjectEvent
        undo,  # type: Partial
        undo_event,  # type: BaseObjectEvent
        history_adopters,  # type: FrozenSet[BaseObject, ...]
    ):
        # type: (...) -> bool
        """Change the obj by dispatching events and commands accordingly."""
        command = BaseObjectCommand(name, self, redo, redo_event, undo, undo_event)

        # Emit event (internal pre phase), which will return True if event was accepted
        if self.__broadcaster.emit(redo_event, EventPhase.INTERNAL_PRE):

            # Filter history adopters, skipping the ones that provide their own history
            filtered_history_adopters = set(
                adopter
                for adopter in history_adopters
                if type(adopter).history_descriptor is None
            )

            # Run command
            history = self.__get_history__()
            if history is None:
                command.__flag_ran__()
                command.__redo__()
            else:
                history.__run__(command)

            # Attach history adopters and propagate history
            history = self.__get_history__()
            for adopter in filtered_history_adopters:
                old_history = adopter.__get_history__()
                if old_history is not None:
                    if old_history is not history:
                        old_history.flush()
                adopter.__history_provider_ref = ref(self)

            # Emit event (internal post phase)
            self.__broadcaster.emit(redo_event, EventPhase.INTERNAL_POST)

            # Return True since event was accepted
            return True

        # AbstractEvent was rejected, return False
        else:
            return False

    def __react__(self, event, phase):
        # type: (BaseObjectEvent, EventPhase) -> None
        """React to an event."""
        pass

    @contextmanager
    def __event_context__(self, event):
        # type: (BaseObjectEvent) -> ContextManager
        """Internal event context."""
        self.__broadcaster.emit(event, EventPhase.PRE)
        yield
        self.__broadcaster.emit(event, EventPhase.POST)

    @contextmanager
    def _batch_context(self, name="Batch"):
        # type: (str) -> ContextManager
        """Batch context."""
        history = self.__history
        if history is not None:
            with history.batch_context(name):
                yield
        else:
            yield

    @property
    def hierarchy(self):
        # type: () -> HierarchyAccess
        """Parent-child hierarchy."""
        return self.__hierarchy_access

    @property
    def events(self):
        # type: () -> EventEmitter
        """Event emitter."""
        return self.__broadcaster.emitter


class BaseObjectCommand(UndoableCommand):
    """Command to change the object."""

    __slots__ = ("__obj", "__redo", "__redo_event", "__undo", "__undo_event")

    def __init__(
        self,
        name,  # type: str
        obj,  # type: BaseObject
        redo,  # type: Partial
        redo_event,  # type: BaseObjectEvent
        undo,  # type: Partial
        undo_event,  # type: BaseObjectEvent
    ):
        # type: (...) -> None
        """Initialize with name, partials, and events."""
        super(BaseObjectCommand, self).__init__(name)
        self.__obj = obj
        self.__redo = redo
        self.__redo_event = redo_event
        self.__undo = undo
        self.__undo_event = undo_event

    def __redo__(self):
        # type: () -> None
        """Run 'redo' partial within its associated event context."""
        with self.obj.__event_context__(self.redo_event):
            self.__redo()

    def __undo__(self):
        # type: () -> None
        """Run 'undo' partial within its associated event context."""
        with self.obj.__event_context__(self.undo_event):
            self.__undo()

    @property
    def obj(self):
        # type: () -> BaseObject
        """BaseObject."""
        return self.__obj

    @property
    def redo_event(self):
        # type: () -> BaseObjectEvent
        """Redo event."""
        return self.__redo_event

    @property
    def undo_event(self):
        # type: () -> BaseObjectEvent
        """Undo event."""
        return self.__undo_event
