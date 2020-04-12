# -*- coding: utf-8 -*-
"""Event broadcasting component."""

from abc import abstractmethod
from enum import Enum
from weakref import WeakKeyDictionary, ref
from slotted import Slotted, SlottedMapping
from six import raise_from
from typing import Type, FrozenSet, Optional, Iterator, Callable, cast
from componente import CompositeMixin, Component

from .._base.exceptions import ModeloException, ModeloError
from ..utils.type_checking import assert_is_instance

__all__ = [
    "Broadcaster",
    "InternalBroadcaster",
    "EventListenerMixin",
    "ListenerToken",
    "EventEmitter",
    "Events",
    "Event",
    "EventPhase",
    "BroadcasterException",
    "BroadcasterError",
    "StopEventPropagationException",
    "RejectEventException"
]


class Broadcaster(Slotted, Component):
    """Emits events."""

    __slots__ = ("__weakref__", "__events")

    @staticmethod
    def get_type():
        # type: () -> Type[Broadcaster]
        """Get component key type."""
        return Broadcaster

    def __init__(self, obj, event_types=frozenset()):
        # type: (CompositeMixin, FrozenSet[Type[Event], ...]) -> None
        """Initialize with supported event types."""
        super(Broadcaster, self).__init__(obj)
        self.__events = Events(self, event_types)

    @classmethod
    def get_component(cls, obj):
        # type: (CompositeMixin) -> Broadcaster
        """Get broadcaster component of a composite object."""
        return cast(Broadcaster, super(Broadcaster, cls).get_component(obj))

    def emit(self, event, phase):
        # type: (Event, EventPhase) -> bool
        """Emit event. Return False if event was rejected."""
        return self.__events[event.type].__emit__(event, phase)

    @property
    def internal(self):
        # type: () -> bool
        """Whether this broadcaster is internal."""
        return False

    @property
    def events(self):
        # type: () -> Events
        """Event emitters mapped by event type."""
        return self.__events


class InternalBroadcaster(Broadcaster):
    """Emits internal events."""

    __slots__ = ()

    @staticmethod
    def get_type():
        # type: () -> Type[InternalBroadcaster]
        """Get component key type."""
        return InternalBroadcaster

    @classmethod
    def get_component(cls, obj):
        # type: (CompositeMixin) -> InternalBroadcaster
        """Get internal broadcaster component of a composite object."""
        return cast(
            InternalBroadcaster, super(InternalBroadcaster, cls).get_component(obj)
        )

    @property
    def internal(self):
        # type: () -> bool
        """Whether this broadcaster is internal."""
        return True


class EventListenerMixin(object):
    """Mixin for listening and reacting to events."""

    __slots__ = ("__weakref__",)

    def __hash__(self):
        # type: () -> int
        """Make sure 'super' object has a valid hash method."""
        try:
            hash_method = super(EventListenerMixin, self).__hash__
            if hash_method is None:
                raise AttributeError()
        except AttributeError:
            exc = TypeError("'{}' is not hashable".format(type(self).__name__))
            raise_from(exc, None)
            raise exc
        return hash_method()

    @abstractmethod
    def __react__(self, obj, event, phase):
        # type: (CompositeMixin, Event, EventPhase) -> None
        """React to an event."""
        raise NotImplementedError()


class ListenerToken(Slotted):
    """Token that allows control event reaction priority."""

    __slots__ = ("__emitter_ref", "__listener_ref")

    def __init__(self, emitter, listener):
        # type: (EventEmitter, EventListenerMixin) -> None
        """Initialize with emitter and listener."""
        self.__emitter_ref = ref(emitter)
        self.__listener_ref = ref(listener)

    def wait(self):
        # type: () -> None
        """Wait for the associated listener to react before continuing."""
        emitter = self.emitter
        listener = self.listener
        if emitter is None:
            return
        if listener is None:
            return
        emitter.__wait__(self)

    @property
    def emitter(self):
        # type: () -> EventEmitter
        """Event emitter."""
        emitter = self.__emitter_ref()
        if emitter is not None:
            return emitter
        raise ReferenceError("emitter is no longer alive")

    @property
    def listener(self):
        # type: () -> EventListenerMixin
        """Event listener."""
        listener = self.__listener_ref()
        if listener is not None:
            return listener
        raise ReferenceError("listener is no longer alive")


class EventEmitter(Slotted):
    """Keeps track of listeners and emit events for them to react."""

    __slots__ = (
        "__weakref__",
        "__broadcaster_ref",
        "__internal",
        "__event_type",
        "__listeners",
        "__emitting",
        "__emitting_phase",
        "__reacting",
    )

    def __init__(self, broadcaster, event_type):
        # type: (Broadcaster, Type[Event]) -> None
        """Init with a broadcaster component and event type."""
        self.__broadcaster_ref = ref(broadcaster)
        self.__internal = broadcaster.internal
        self.__event_type = event_type
        self.__listeners = WeakKeyDictionary()
        self.__emitting = None
        self.__emitting_phase = None
        self.__reacting = set()

    def __wait__(self, token):
        # type: (ListenerToken) -> None
        """Wait for the token's listener to react before continuing."""
        if self.__emitting is None:
            return
        obj = self.obj
        if obj is None:
            return
        listener = token.listener
        if listener in self.__reacting:
            self.__reacting.remove(listener)
            listener.__react__(obj, self.__emitting, self.__emitting_phase)

    def __emit__(self, event, phase):
        # type: (Event, EventPhase) -> bool
        """Emit event to all listeners. Return False if event was rejected."""
        if self.__emitting is not None:
            raise RuntimeError(
                "already emitting event {}, cannot emit {}".format(
                    self.__emitting, event
                )
            )
        if event.type is not self.event_type:
            raise TypeError(
                "cannot emmit '{}' events, only '{}'".format(
                    event.type.__name__, self.event_type.__name__
                )
            )
        if not self.__internal:
            if phase in (EventPhase.INTERNAL_PRE, EventPhase.INTERNAL_POST):
                raise RuntimeError(
                    "cannot use phase '{}' on a non-internal event emitter".format(
                        phase
                    )
                )
        obj = self.obj
        self.__emitting = event
        self.__emitting_phase = phase
        self.__reacting = reacting = set(self.__listeners)

        callback = None
        try:
            while reacting:
                listener = reacting.pop()
                try:
                    listener.__react__(obj, event, phase)
                except StopEventPropagationException:
                    break
                except RejectEventException as exc:
                    if not self.__internal:
                        exc = RuntimeError(
                            "'{}' can only be raised during internal emission".format(
                                RejectEventException.__name__
                            )
                        )
                        raise_from(exc, None)
                        raise exc
                    if phase is not EventPhase.INTERNAL_PRE:
                        exc = RuntimeError(
                            "'{}' can only be raised during '{}', not '{}'".format(
                                RejectEventException.__name__,
                                EventPhase.INTERNAL_PRE,
                                phase,
                            )
                        )
                        raise_from(exc, None)
                        raise exc
                    callback = exc.callback
                    return False
        finally:
            self.__emitting = None
            self.__emitting_phase = None
            self.__reacting = set()
            if callback is not None:
                callback()

        return True

    def add_listener(self, listener, force=False):
        # type: (EventListenerMixin, bool) -> ListenerToken
        """Add a listener and get its token."""
        assert_is_instance(listener, EventListenerMixin)

        if listener in self.__listeners:
            raise ValueError("listener already added")

        listeners = self.__listeners
        reacting = self.__reacting

        try:
            token = listeners[listener]
        except KeyError:
            token = listeners[listener] = ListenerToken(self, listener)

        if force and self.__emitting is not None:
            reacting.add(listener)

        return token

    def remove_listener(self, listener, force=False):
        # type: (EventListenerMixin, bool) -> None
        """Remove a listener."""
        self.__listeners.pop(listener, None)
        if force:
            self.__reacting.discard(listener)

    def get_token(self, listener):
        # type: (ListenerToken) -> None
        """Get token for listener."""
        return self.__listeners[listener]

    @property
    def __broadcaster(self):
        # type: () -> Broadcaster
        """Broadcaster."""
        broadcaster = self.__broadcaster_ref()
        if broadcaster is not None:
            return broadcaster
        raise ReferenceError("broadcaster is no longer alive")

    @property
    def internal(self):
        # type: () -> bool
        """Whether this emitter is internal."""
        return self.__internal

    @property
    def obj(self):
        # type: () -> CompositeMixin
        """Source object."""
        broadcaster = self.__broadcaster
        if broadcaster is not None:
            return broadcaster.obj

    @property
    def event_type(self):
        # type: () -> Type[Event]
        """Event type."""
        return self.__event_type

    @property
    def listeners(self):
        # type: () -> FrozenSet[EventListenerMixin, ...]
        """Listeners."""
        return frozenset(self.__listeners)

    @property
    def emitting(self):
        # type: () -> Optional[Event]
        """Event currently being emitted."""
        return self.__emitting

    @property
    def emitting_phase(self):
        # type: () -> Optional[EventPhase]
        """Current emitting phase."""
        return self.__emitting_phase


class Events(SlottedMapping):
    """Mapping of event types and corresponding emitters."""

    __slots__ = ("__broadcaster_ref", "__event_types", "__emitters")

    def __init__(self, broadcaster, event_types):
        # type: (Broadcaster, FrozenSet[Type[Event], ...]) -> None
        """Initialize with broadcaster and supported event types."""
        self.__broadcaster_ref = ref(broadcaster)
        self.__event_types = event_types
        self.__emitters = {}

    def __repr__(self):
        # type: () -> str
        """Get representation."""
        return repr(self.__emitters)

    def __str__(self):
        # type: () -> str
        """Get string representation."""
        return str(self.__emitters)

    def __getitem__(self, event_type):
        # type: (Type[Event]) -> EventEmitter
        """Get event emitter for a given event type."""
        try:
            emitter = self.__emitters[event_type]
        except KeyError:
            if event_type in self.__event_types:
                broadcaster = self.__broadcaster_ref()
                if broadcaster is None or broadcaster.obj is None:
                    raise ReferenceError("object is no longer alive")
                emitter = self.__emitters[event_type] = EventEmitter(
                    broadcaster, event_type
                )
            else:
                raise
        return emitter

    def __iter__(self):
        # type: () -> Iterator[Type[Event], ...]
        """Iterate over event types."""
        for event_type in self.__event_types:
            yield event_type

    def __len__(self):
        # type: () -> int
        """Get number of supported event types."""
        return len(self.__event_types)


class Event(Slotted):
    """Abstract event."""

    __slots__ = ()

    @property
    def type(self):
        # type: () -> Type[Event]
        """Event type."""
        return type(self)


class EventPhase(Enum):
    """Event phase."""

    INTERNAL_PRE = "internal_pre"
    PRE = "pre"
    POST = "post"
    INTERNAL_POST = "internal_post"


class BroadcasterException(ModeloException):
    """Broadcaster exception."""


class BroadcasterError(ModeloError, BroadcasterException):
    """Broadcaster error."""


class StopEventPropagationException(BroadcasterException):
    """When raised during event emission, will prevent next listeners to react."""


class RejectEventException(BroadcasterException):
    """
    When raised during event emission, will prevent the action that originated the
    event from happening at all.
    """

    __slots__ = ("__callback",)

    def __init__(self, callback=None):
        # type: (Optional[Callable]) -> None
        super(RejectEventException, self).__init__()
        self.__callback = callback

    @property
    def callback(self):
        # type: () -> Optional[Callable]
        return self.__callback
