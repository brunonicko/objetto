# -*- coding: utf-8 -*-
"""Models manage data access and modification."""

from contextlib import contextmanager
from six import with_metaclass
from typing import FrozenSet, Type, ContextManager, Optional, Any, cast
from slotted import SlottedABCMeta, SlottedABC
from componente import COMPONENTS_SLOT, CompositeMixin

from .._components.broadcaster import (
    Broadcaster,
    InternalBroadcaster,
    EventPhase,
    Events,
    Event,
)
from .._components.hierarchy import Hierarchy
from .._components.runner import Runner, UndoableCommand, History
from ..utils.partial import Partial

__all__ = [
    "ModelMeta",
    "Model",
    "ModelEvent",
    "ModelCommand",
]


class ModelMeta(SlottedABCMeta):
    """Metaclass for 'Model'."""

    def __setattr__(cls, name, value):
        # type: (str, Any) -> None
        """Prevent class attribute setting."""
        if name not in SlottedABC.__dict__:
            raise AttributeError(
                "'{}' class attributes are read-only".format(cls.__name__)
            )
        super(ModelMeta, cls).__setattr__(name, value)

    def __delattr__(cls, name):
        # type: (str) -> None
        """Prevent class attribute deleting."""
        if name not in SlottedABC.__dict__:
            raise AttributeError(
                "'{}' class attributes are read-only".format(cls.__name__)
            )
        super(ModelMeta, cls).__delattr__(name)


class Model(with_metaclass(ModelMeta, CompositeMixin, SlottedABC)):
    """Abstract model."""

    __slots__ = (COMPONENTS_SLOT,)
    __events__ = frozenset()  # type: FrozenSet[Type[ModelEvent], ...]

    def __init__(self):
        cls = type(self)
        self._.add_component(Hierarchy)
        self._.add_component(InternalBroadcaster, event_types=cls.__events__)
        self._.add_component(Broadcaster, event_types=cls.__events__)
        self._.add_component(Runner)

    def __dispatch__(self, name, redo, redo_event, undo, undo_event):
        # type: (str, Partial, ModelEvent, Partial, ModelEvent) -> bool
        """Change the model by dispatching events and commands accordingly."""
        internal_broadcaster = cast(InternalBroadcaster, self._[InternalBroadcaster])
        runner = cast(Runner, self._[Runner])

        command = ModelCommand(name, self, redo, redo_event, undo, undo_event)
        if internal_broadcaster.emit(redo_event, EventPhase.INTERNAL_PRE):
            runner.run(command)
            internal_broadcaster.emit(redo_event, EventPhase.INTERNAL_POST)
            return True
        else:
            return False

    @contextmanager
    def __event_context__(self, event):
        # type: (ModelEvent) -> ContextManager
        """Internal event context."""
        internal_broadcaster = cast(InternalBroadcaster, self._[InternalBroadcaster])
        broadcaster = cast(Broadcaster, self._[Broadcaster])

        internal_broadcaster.emit(event, EventPhase.PRE)
        broadcaster.emit(event, EventPhase.PRE)
        yield
        internal_broadcaster.emit(event, EventPhase.POST)
        broadcaster.emit(event, EventPhase.POST)

    @property
    def _history(self):
        # type: () -> Optional[History]
        """Command history."""
        runner = cast(Runner, self._[Runner])
        return runner.history

    @_history.setter
    def _history(self, history):
        # type: (Optional[History]) -> None
        """Set command history."""
        runner = cast(Runner, self._[Runner])
        runner.history = history

    @property
    def _events(self):
        # type: () -> Events
        """Internal event emitters mapped by event type."""
        internal_broadcaster = cast(InternalBroadcaster, self._[InternalBroadcaster])
        return internal_broadcaster.events

    @property
    def events(self):
        # type: () -> Events
        """Event emitters mapped by event type."""
        broadcaster = cast(Broadcaster, self._[Broadcaster])
        return broadcaster.events


class ModelEvent(Event):
    """Abstract event. Describes the adoption and/or release of child _models."""

    __slots__ = ("__adoptions", "__releases")

    def __init__(self, adoptions, releases):
        # type: (FrozenSet[Model, ...], FrozenSet[Model, ...]) -> None
        """Initialize with adoptions and releases."""
        self.__adoptions = adoptions
        self.__releases = releases

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
