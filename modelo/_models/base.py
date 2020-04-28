# -*- coding: utf-8 -*-
"""Models manage data access and modification."""

from abc import abstractmethod
from contextlib import contextmanager
from weakref import ref
from six import with_metaclass, iteritems
from typing import FrozenSet, ContextManager, Optional, Type, Tuple, Any, Dict, cast
from slotted import SlottedABCMeta, SlottedABC, Slotted

from .._base.constants import DEAD_REF
from .._base.events import Event
from .._components.broadcaster import (
    Broadcaster,
    EventListenerMixin,
    EventPhase,
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

__all__ = ["HistoryDescriptor", "ModelMeta", "Model", "ModelEvent", "ModelCommand"]


class ModelHierarchy(Hierarchy):
    """Model hierarchy."""

    def update_children(self, children_updates):
        # type: (ChildrenUpdates) -> None
        """Perform children adoptions and/or releases."""
        for adoption in children_updates.adoptions:
            adoption = cast(Model, adoption)
            parent = cast(Model, self.obj)
            last_parent_history = adoption.__get_last_parent_history__()
            parent_history = parent.__get_history__()
            if last_parent_history is not parent_history:
                if last_parent_history is not None:
                    last_parent_history.flush()
                adoption.__set_last_parent_history__(parent_history)
        super(ModelHierarchy, self).update_children(children_updates)


class HistoryDescriptor(Slotted):
    """Descriptor that gives access to a model's command history."""

    __slots__ = ("__size",)

    def __init__(self, size=0):
        # type: (int) -> None
        """Initialize with size."""
        size = int(size)
        if size < -1:
            size = -1
        self.__size = size

    def __get__(self, model, model_cls=None):
        # type: (Optional[Model], Optional[Type[Model]]) -> Any
        """Descriptor 'get' access."""
        if model is None:
            return self
        if not model.__initialized__:
            raise AttributeError(
                "can't access history before instance is fully initialized"
            )
        return model.__get_history__()

    def __set__(self, model, value):
        # type: (Model, Any) -> None
        """Descriptor 'set' access."""
        error = "attribute is read-only"
        raise AttributeError(error)

    def __delete__(self, model):
        # type: (Model) -> None
        """Descriptor 'delete' access."""
        error = "attribute is read-only"
        raise AttributeError(error)

    @property
    def size(self):
        # type: () -> int
        """History size."""
        return self.__size


def _make_model_class(
    mcs,  # type: Type[ModelMeta]
    name,  # type: str
    bases,  # type: Tuple[Type, ...]
    dct,  # type: Dict[str, Any]
):
    # type: (...) -> ModelMeta
    """Make model class/subclass."""
    dct = dict(dct)

    # Init 'history_descriptor'
    dct["__history_descriptor__"] = None

    # Make class
    cls = super(ModelMeta, mcs).__new__(mcs, name, bases, dct)

    # Find a history descriptor
    for base in cls.__mro__:
        if base is not cls and isinstance(base, ModelMeta):
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


class ModelMeta(SlottedABCMeta):
    """Metaclass for 'Model'."""

    __new__ = staticmethod(_make_model_class)
    __history_descriptor__ = None  # type: Optional[HistoryDescriptor]

    def __call__(cls, *args, **kwargs):
        """Make an instance an initialize it."""

        # Make an instance
        self = cls.__new__(cls, *args, **kwargs)

        # Mark as not initialized
        self.__initialized__ = False

        # Initialize it
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
        super(ModelMeta, cls).__setattr__(name, value)

    def __delattr__(cls, name):
        # type: (str) -> None
        """Prevent class attribute deleting."""
        if name not in SlottedABC.__dict__:
            error = "'{}' class attributes are read-only".format(cls.__name__)
            raise AttributeError(error)
        super(ModelMeta, cls).__delattr__(name)

    @property
    def history_descriptor(cls):
        # type: () -> Optional[HistoryDescriptor]
        """History descriptor."""
        return cls.__history_descriptor__


class Model(
    with_metaclass(ModelMeta, HierarchicalMixin, EventListenerMixin, SlottedABC)
):
    """Abstract model."""

    __slots__ = (
        "__initialized__",
        "__history",
        "__history_provider_ref",
        "__hierarchy",
        "__hierarchy_access",
        "__broadcaster",
        "__last_parent_history_ref",
    )

    def __init__(self):
        """Initialize."""
        if type(self).history_descriptor is not None:
            self.__history = History(size=0)
            self.__history_provider_ref = ref(self)
        else:
            self.__history = None
            self.__history_provider_ref = DEAD_REF
        self.__hierarchy = ModelHierarchy(self)
        self.__hierarchy_access = HierarchyAccess(self.__hierarchy)
        self.__broadcaster = Broadcaster()
        self.__last_parent_history_ref = DEAD_REF

    def __getattr__(self, name):
        # type: (str) -> Any
        """Raise informative exception if missed call to super's '__init__'."""
        if name in Model.__members__:
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
        # type: (Model) -> bool
        """Compare for equality."""
        raise NotImplementedError()

    def __ne__(self, other):
        # type: (Model) -> bool
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
            self.__last_parent_history_ref = DEAD_REF
        else:
            self.__last_parent_history_ref = ref(last_parent_history)

    def __dispatch__(
        self,
        name,  # type: str
        redo,  # type: Partial
        redo_event,  # type: ModelEvent
        undo,  # type: Partial
        undo_event,  # type: ModelEvent
        history_adopters,  # type: FrozenSet[Model, ...]
    ):
        # type: (...) -> bool
        """Change the model by dispatching events and commands accordingly."""
        command = ModelCommand(name, self, redo, redo_event, undo, undo_event)

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
        # type: (ModelEvent, EventPhase) -> None
        """React to an event."""
        pass

    @contextmanager
    def __event_context__(self, event):
        # type: (ModelEvent) -> ContextManager
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
    def _hierarchy(self):
        # type: () -> HierarchyAccess
        """Parent-child hierarchy."""
        return self.__hierarchy_access

    @property
    def events(self):
        # type: () -> EventEmitter
        """Event emitter."""
        return self.__broadcaster.emitter


class ModelEvent(Event):
    """Abstract event. Describes the adoption and/or release of child models."""

    __slots__ = ("__model", "__adoptions", "__releases")

    def __init__(self, model, adoptions, releases):
        # type: (Model, FrozenSet[Model, ...], FrozenSet[Model, ...]) -> None
        """Initialize with adoptions and releases."""
        self.__model = model
        self.__adoptions = adoptions
        self.__releases = releases

    def __eq_id_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should compared using object identity."""
        return ("model",)

    @abstractmethod
    def __eq_equal_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should compared using equality."""
        return "adoptions", "releases"

    @abstractmethod
    def __repr_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__repr__'."""
        return "adoptions", "releases"

    @abstractmethod
    def __str_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__str__'."""
        return "history", "adoptions", "releases"

    @property
    def model(self):
        # type: () -> Model
        """Model."""
        return self.__model

    @property
    def adoptions(self):
        # type: () -> FrozenSet[Model, ...]
        """Adoptions."""
        return self.__adoptions

    @property
    def releases(self):
        # type: () -> FrozenSet[Model, ...]
        """Releases."""
        return self.__releases


class ModelCommand(UndoableCommand):
    """Command to change the model."""

    __slots__ = ("__model", "__redo", "__redo_event", "__undo", "__undo_event")

    def __init__(self, name, model, redo, redo_event, undo, undo_event):
        # type: (str, Model, Partial, ModelEvent, Partial, ModelEvent) -> None
        """Initialize with name, partials, and events."""
        super(ModelCommand, self).__init__(name)
        self.__model = model
        self.__redo = redo
        self.__redo_event = redo_event
        self.__undo = undo
        self.__undo_event = undo_event

    def __redo__(self):
        # type: () -> None
        """Run 'redo' partial within its associated event context."""
        with self.model.__event_context__(self.redo_event):
            self.__redo()

    def __undo__(self):
        # type: () -> None
        """Run 'undo' partial within its associated event context."""
        with self.model.__event_context__(self.undo_event):
            self.__undo()

    @property
    def model(self):
        # type: () -> Model
        """Model."""
        return self.__model

    @property
    def redo_event(self):
        # type: () -> ModelEvent
        """Redo event."""
        return self.__redo_event

    @property
    def undo_event(self):
        # type: () -> ModelEvent
        """Undo event."""
        return self.__undo_event
