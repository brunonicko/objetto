# -*- coding: utf-8 -*-
"""Models manage data access and modification."""

from contextlib import contextmanager
from six import with_metaclass
from typing import FrozenSet, Type, ContextManager, Optional, Dict
from slotted import SlottedABCMeta, SlottedABC

from ._constants import EventPhase
from ._partial import Partial
from ._runner import UndoableCommand
from ._events import ModelEvent
from ._component import Component, CompositeMixin
from ._hierarchy import Hierarchy
from ._broadcaster import Broadcaster
from ._runner import Runner


class ModelMeta(SlottedABCMeta):
    """Metaclass for 'Model'."""


class Model(with_metaclass(ModelMeta, CompositeMixin, SlottedABC)):
    """Abstract model."""

    __slots__ = (
        "___components",
        "___hierarchy",
        "___internal_broadcaster",
        "___broadcaster",
        "___runner",
    )

    # Supported event types
    __event_types__ = frozenset()  # type: FrozenSet[Type[ModelEvent], ...]

    def __dispatch__(self, name, redo, redo_event, undo, undo_event):
        # type: (str, Partial, ModelEvent, Partial, ModelEvent) -> bool
        """Change the model by dispatching events and commands accordingly."""
        command = ModelCommand(name, self, redo, redo_event, undo, undo_event)
        if self.__internal_broadcaster.emit(redo_event, EventPhase.INTERNAL_PRE):
            self.__runner.run(command)
            self.__internal_broadcaster.emit(redo_event, EventPhase.INTERNAL_POST)
            return True
        else:
            return False

    @contextmanager
    def __event_context__(self, event):
        # type: (ModelEvent) -> ContextManager
        """Internal event context."""
        self.__internal_broadcaster.emit(event, EventPhase.PRE)
        self.__broadcaster.emit(event, EventPhase.PRE)
        yield
        self.__internal_broadcaster.emit(event, EventPhase.POST)
        self.__broadcaster.emit(event, EventPhase.POST)

    def __get_component__(self, key):
        # type: (Type[Component]) -> Component
        """Get component by its unique type."""
        return self.__components[key]

    @property
    def __components(self):
        # type: () -> Dict[Type[Component], Component]
        """Component map."""
        try:
            components = self.___components
        except AttributeError:
            components = self.___components = {
                Hierarchy: self.__hierarchy,
                Broadcaster: self.__broadcaster,
                Runner: self.__runner
            }
        return components

    @property
    def __hierarchy(self):
        # type: () -> "modelo._hierarchy.Hierarchy"
        """Hierarchy component."""
        try:
            hierarchy = self.___hierarchy
        except AttributeError:
            hierarchy = self.___hierarchy = Hierarchy(self)
        return hierarchy

    @property
    def __internal_broadcaster(self):
        # type: () -> "modelo._broadcaster.Broadcaster"
        """Internal broadcaster component."""
        try:
            broadcaster = self.___internal_broadcaster
        except AttributeError:
            cls = type(self)
            broadcaster = self.___internal_broadcaster = Broadcaster(
                self, internal=True, event_types=cls.__event_types__,
            )
        return broadcaster

    @property
    def __broadcaster(self):
        # type: () -> "modelo._broadcaster.Broadcaster"
        """Broadcaster component."""
        try:
            broadcaster = self.___broadcaster
        except AttributeError:
            cls = type(self)
            broadcaster = self.___broadcaster = Broadcaster(
                self, internal=False, event_types=cls.__event_types__,
            )
        return broadcaster

    @property
    def __runner(self):
        # type: () -> "modelo._runner.Runner"
        """Command runner component."""
        try:
            runner = self.___runner
        except AttributeError:
            runner = self.___runner = Runner(self)
        return runner

    @property
    def _history(self):
        # type: () -> Optional["modelo._runner.History"]
        """Command history."""
        return self.__runner.history

    @_history.setter
    def _history(self, history):
        # type: (Optional["modelo._runner.History"]) -> None
        """Set command history."""
        self.__runner.history = history

    @property
    def _events(self):
        # type: () -> "modelo._broadcaster.Events"
        """Internal event emitters mapped by event type."""
        return self.__internal_broadcaster.events

    @property
    def events(self):
        # type: () -> "modelo._broadcaster.Events"
        """Event emitters mapped by event type."""
        return self.__broadcaster.events


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
