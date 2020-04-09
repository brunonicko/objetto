# -*- coding: utf-8 -*-

from contextlib import contextmanager
from six import with_metaclass
from typing import FrozenSet
from slotted import SlottedABCMeta, SlottedABC

from ._constants import EventPhase
from ._runner import UndoableCommand
from ._events import ModelEvent


class BaseModelMeta(SlottedABCMeta):
    pass


class BaseModel(with_metaclass(BaseModelMeta, SlottedABC)):
    __slots__ = (
        "__weakref__",
        "___hierarchy",
        "___internal_broadcaster",
        "___broadcaster",
        "___runner",
    )
    __event_types__ = frozenset()  # type: FrozenSet[ModelEvent, ...]

    def __pprint__(self):
        return str(self)

    def __dispatch__(self, name, redo, redo_event, undo, undo_event):
        command = BaseModelCommand(name, self, redo, redo_event, undo, undo_event)
        if self.__internal_broadcaster.emit(redo_event, EventPhase.INTERNAL_PRE):
            self.__runner.run(command)
            self.__internal_broadcaster.emit(redo_event, EventPhase.INTERNAL_POST)
            return True
        else:
            return False

    @contextmanager
    def __event_context__(self, event):
        self.__internal_broadcaster.emit(event, EventPhase.PRE)
        self.__broadcaster.emit(event, EventPhase.PRE)
        yield
        self.__internal_broadcaster.emit(event, EventPhase.POST)
        self.__broadcaster.emit(event, EventPhase.POST)

    @property
    def __hierarchy__(self):
        try:
            hierarchy = self.___hierarchy
        except AttributeError:
            from ._hierarchy import Hierarchy

            hierarchy = self.___hierarchy = Hierarchy(self)
        return hierarchy

    @property
    def __internal_broadcaster(self):
        try:
            broadcaster = self.___internal_broadcaster
        except AttributeError:
            from ._broadcaster import Broadcaster

            cls = type(self)
            broadcaster = self.___internal_broadcaster = Broadcaster(
                self, internal=True, event_types=cls.__event_types__,
            )
        return broadcaster

    @property
    def __broadcaster(self):
        try:
            broadcaster = self.___broadcaster
        except AttributeError:
            from ._broadcaster import Broadcaster

            cls = type(self)
            broadcaster = self.___broadcaster = Broadcaster(
                self, internal=False, event_types=cls.__event_types__,
            )
        return broadcaster

    @property
    def __runner(self):
        try:
            runner = self.___runner
        except AttributeError:
            from ._runner import Runner

            runner = self.___runner = Runner(self)
        return runner

    @property
    def _history(self):
        return self.__runner.history

    @_history.setter
    def _history(self, history):
        self.__runner.history = history

    @property
    def _events(self):
        return self.__internal_broadcaster.events

    @property
    def events(self):
        return self.__broadcaster.events


class BaseModelCommand(UndoableCommand):
    __slots__ = ("__model", "__redo", "__redo_event", "__undo", "__undo_event")

    def __init__(self, name, model, redo, redo_event, undo, undo_event):
        super(BaseModelCommand, self).__init__(name)
        self.__model = model
        self.__redo = redo
        self.__redo_event = redo_event
        self.__undo = undo
        self.__undo_event = undo_event

    def __redo__(self):
        with self.model.__event_context__(self.redo_event):
            self.__redo()

    def __undo__(self):
        with self.model.__event_context__(self.undo_event):
            self.__undo()

    @property
    def model(self):
        return self.__model

    @property
    def redo_event(self):
        return self.__redo_event

    @property
    def undo_event(self):
        return self.__undo_event
