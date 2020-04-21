# -*- coding: utf-8 -*-
"""Models manage data access and modification."""

from abc import abstractmethod
from contextlib import contextmanager
from six import with_metaclass
from typing import FrozenSet, ContextManager, Optional, Any
from slotted import SlottedABCMeta, SlottedABC

from .._components.broadcaster import (
    Broadcaster,
    InternalBroadcaster,
    EventListenerMixin,
    EventPhase,
    EventEmitter,
)
from .._components.hierarchy import Hierarchy, HierarchicalMixin, HierarchyAccess
from .._components.history import UndoableCommand, History
from ..utils.partial import Partial

__all__ = ["ModelMeta", "Model", "ModelEvent", "ModelCommand"]


class ModelMeta(SlottedABCMeta):
    """Metaclass for 'Model'."""

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


class Model(
    with_metaclass(ModelMeta, HierarchicalMixin, EventListenerMixin, SlottedABC)
):
    """Abstract model."""

    __slots__ = (
        "__hierarchy",
        "__hierarchy_access",
        "__internal_broadcaster",
        "__broadcaster",
        "__history",
    )

    def __init__(self):
        """Initialize."""
        self.__hierarchy = Hierarchy(self)
        self.__hierarchy_access = HierarchyAccess(self.__hierarchy)
        self.__internal_broadcaster = InternalBroadcaster()
        self.__broadcaster = Broadcaster()
        self.__history = None

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

    def __dispatch__(self, name, redo, redo_event, undo, undo_event):
        # type: (str, Partial, ModelEvent, Partial, ModelEvent) -> bool
        """Change the model by dispatching events and commands accordingly."""
        command = ModelCommand(name, self, redo, redo_event, undo, undo_event)
        if self.__internal_broadcaster.emit(redo_event, EventPhase.INTERNAL_PRE):
            if self.__history is None:
                command.__flag_ran__()
                command.__redo__()
            else:
                self.__history.run(command)
            self.__internal_broadcaster.emit(redo_event, EventPhase.INTERNAL_POST)
            return True
        else:
            return False

    def __react__(self, event, phase):
        # type: (Any, EventPhase) -> None
        """React to an event."""
        pass

    @contextmanager
    def __event_context__(self, event):
        # type: (ModelEvent) -> ContextManager
        """Internal event context."""
        self.__internal_broadcaster.emit(event, EventPhase.PRE)
        self.__broadcaster.emit(event, EventPhase.PRE)
        yield
        self.__internal_broadcaster.emit(event, EventPhase.POST)
        self.__broadcaster.emit(event, EventPhase.POST)

    @property
    def _history(self):
        # type: () -> Optional[History]
        """Command history."""
        return self.__history

    @_history.setter
    def _history(self, history):
        # type: (Optional[History]) -> None
        """Set command history."""
        if self.__history is not None:
            self.__history.flush()
        self.__history = history

    @property
    def _hierarchy(self):
        # type: () -> HierarchyAccess
        """Parent-child hierarchy."""
        return self.__hierarchy_access

    @property
    def _events(self):
        # type: () -> EventEmitter
        """Internal event emitter."""
        return self.__internal_broadcaster.emitter

    @property
    def events(self):
        # type: () -> EventEmitter
        """Event emitter."""
        return self.__broadcaster.emitter


class ModelEvent(SlottedABC):
    """Abstract event. Describes the adoption and/or release of child models."""

    __slots__ = ("__model", "__adoptions", "__releases")

    def __init__(self, model, adoptions, releases):
        # type: (Model, FrozenSet[Model, ...], FrozenSet[Model, ...]) -> None
        """Initialize with adoptions and releases."""
        self.__model = model
        self.__adoptions = adoptions
        self.__releases = releases

    def __eq__(self, other):
        # type: (ModelEvent) -> bool
        """Compare with another event for equality."""
        if type(self) is not type(other):
            return False
        if self.__model is not other.__model:
            return False
        if self.__adoptions != other.__adoptions:
            return False
        if self.__releases != other.__releases:
            return False
        return True

    def __ne__(self, other):
        # type: (ModelEvent) -> bool
        """Compare with another event for inequality."""
        return not self.__eq__(other)

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
