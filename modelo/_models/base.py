# -*- coding: utf-8 -*-
"""Models manage data access and modification."""

from abc import abstractmethod
from contextlib import contextmanager
from weakref import ref
from six import with_metaclass
from typing import FrozenSet, ContextManager, Optional, Union, Tuple, Any, cast
from slotted import SlottedABCMeta, SlottedABC

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
from ..utils.type_checking import assert_is_instance
from ..utils.partial import Partial

__all__ = ["ModelMeta", "Model", "ModelEvent", "ModelCommand"]


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
        "__history",
        "__hierarchy",
        "__hierarchy_access",
        "__broadcaster",
        "__last_parent_history_ref",
    )

    def __init__(self):
        """Initialize."""
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
        try:
            history = self.__history
        except AttributeError:
            history = self.__history = None
        return history

    def __set_history__(self, history):
        # type: (Optional[History]) -> None
        """Set command history."""
        old_history = self.__get_history__()
        if old_history is not None and old_history is not history:
            old_history.flush()
        self.__history = history

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

            # Get history
            history = self.__get_history__()

            # Filter out adopters which share the same history, clear history otherwise
            filtered_history_adopters = set()
            for history_adopter in history_adopters:
                if history_adopter.__get_history__() is history:
                    continue
                filtered_history_adopters.add(history_adopter)
                history_adopter.__set_history__(None)

            # Run command
            if history is None:
                command.__flag_ran__()
                command.__redo__()
            else:
                history.__run__(command)

            # Adopt history
            for model in filtered_history_adopters:
                model.__set_history__(history)

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
        history = self.__get_history__()
        if history is not None:
            with history.batch_context(name):
                yield
        else:
            yield

    @property
    def _history(self):
        # type: () -> Optional[History]
        """Command history."""
        return self.__get_history__()

    @_history.setter
    def _history(self, history):
        # type: (Optional[History]) -> None
        """Set command history."""
        assert_is_instance(history, History, optional=True)
        self.__set_history__(history)

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
