# -*- coding: utf-8 -*-
"""Event broadcasting."""

from abc import abstractmethod
from enum import Enum
from weakref import WeakKeyDictionary, WeakSet, ref
from slotted import Slotted
from six import raise_from
from typing import Any, FrozenSet, Optional, Union, Callable

from .._base.exceptions import ObjettoException, ObjettoError

from ..utils.frozen import FrozenObject, field
from ..utils.type_checking import assert_is_instance

__all__ = [
    "EventPhase",
    "Event",
    "field",
    "EventsException",
    "EventsError",
    "AlreadyEmittingError",
    "PhaseError",
    "StopEventPropagationException",
    "RejectEventException",
    "AlreadyEmittingError",
    "PhaseError",
    "StopEventPropagationException",
    "RejectEventException",
    "Broadcaster",
    "EventListenerMixin",
    "ListenerToken",
    "EventEmitter",
]


class EventPhase(Enum):
    """Event phase."""

    INTERNAL_PRE = "internal_pre"
    PRE = "pre"
    POST = "post"
    INTERNAL_POST = "internal_post"


class Event(FrozenObject):
    """Event."""


class EventsException(ObjettoException):
    """Events exception."""


class EventsError(ObjettoError, EventsException):
    """Events error."""


class AlreadyEmittingError(EventsError):
    """Raised when trying to emit during an ongoing emission."""


class PhaseError(EventsError):
    """Raised when the current phase is not the expected one."""


class StopEventPropagationException(EventsException):
    """When raised during event emission, will prevent next listeners to react."""


class RejectEventException(EventsException):
    """
    When raised during event emission, will prevent the action that originated the
    event from happening at all.
    """

    __slots__ = ("__callback",)

    def __init__(self, callback=None):
        # type: (Optional[Callable]) -> None
        """Initialize with an optional callback."""
        super(RejectEventException, self).__init__()
        if callback is not None and not callable(callback):
            error = (
                "expected None or a callable for 'callback' parameter, got '{}'"
            ).format(type(callback).__name__)
            raise TypeError(error)
        self.__callback = callback

    @property
    def callback(self):
        # type: () -> Optional[Callable]
        """Callback."""
        return self.__callback


class Broadcaster(Slotted):
    """Emits events."""

    __slots__ = ("__weakref__", "__emitter")

    def __init__(self):
        # type: () -> None
        """Initialize."""
        self.__emitter = EventEmitter(self)

    def emit(self, event, phase):
        # type: (Union[Event, Any], EventPhase) -> bool
        """Emit event. Return False if event was rejected."""
        return self.__emitter.__emit__(event, phase)

    @property
    def emitter(self):
        # type: () -> EventEmitter
        """Event emitter."""
        return self.__emitter


class EventListenerMixin(object):
    """Mixin for listening and reacting to events."""

    __slots__ = ("__weakref__",)

    @abstractmethod
    def __react__(self, event, phase):
        # type: (Union[Event, Any], EventPhase) -> None
        """React to an event."""
        error = "event listener class '{}' did not implement '__react__' method".format(
            type(self).__name__
        )
        raise NotImplementedError(error)


class ListenerToken(Slotted):
    """Token that allows control over event reaction order/priority."""

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
        error = "emitter is no longer alive"
        raise ReferenceError(error)

    @property
    def listener(self):
        # type: () -> EventListenerMixin
        """Event listener."""
        listener = self.__listener_ref()
        if listener is not None:
            return listener
        error = "listener is no longer alive"
        raise ReferenceError(error)


class EventEmitter(Slotted):
    """Keeps track of listeners and emit events for them to react."""

    __slots__ = (
        "__weakref__",
        "__broadcaster_ref",
        "__listeners",
        "__external_listeners",
        "__emitting",
        "__emitting_phase",
        "__reacting",
    )

    def __init__(self, broadcaster):
        # type: (Broadcaster) -> None
        """Init with a broadcaster object."""
        self.__broadcaster_ref = ref(broadcaster)
        self.__listeners = WeakKeyDictionary()
        self.__external_listeners = WeakSet()
        self.__emitting = None
        self.__emitting_phase = None
        self.__reacting = set()

    def __wait__(self, token):
        # type: (ListenerToken) -> None
        """Wait for the token's listener to react before continuing."""
        if self.__emitting is None:
            return
        listener = token.listener
        if listener in self.__reacting:
            self.__reacting.remove(listener)
            listener.__react__(self.__emitting, self.__emitting_phase)

    def __emit__(self, event, phase):
        # type: (Union[Event, Any], EventPhase) -> bool
        """Emit event to all listeners. Return False if event was rejected."""

        # Check phase type
        assert_is_instance(phase, EventPhase)

        # Can't emit None
        if event is None:
            error = "cannot emit '{}' object as an event".format(type(None).__name__)
            raise TypeError(error)

        # Can't emit if already emitting
        if self.__emitting is not None:
            error = "already emitting event {}, cannot emit {}".format(
                self.__emitting, event
            )
            raise AlreadyEmittingError(error)

        # Start emission
        self.__emitting = event
        self.__emitting_phase = phase
        self.__reacting = reacting = set(self.__listeners)
        callback = None
        try:
            while reacting:
                listener = reacting.pop()
                try:
                    listener.__react__(event, phase)

                # Requested to stop event propagation
                except StopEventPropagationException:
                    break

                # Requested to reject event (during INTERNAL_PRE phase only)
                except RejectEventException as exc:

                    # Error, not INTERNAL_PRE phase
                    if phase is not EventPhase.INTERNAL_PRE:
                        exc = PhaseError(
                            "'{}' can only be raised during '{}', not '{}'".format(
                                RejectEventException.__name__,
                                EventPhase.INTERNAL_PRE,
                                phase,
                            )
                        )
                        raise_from(exc, None)
                        raise exc

                    # Retrieve optional callback from exception and return False
                    callback = exc.callback
                    return False

        # No matter what, end event emission
        finally:
            self.__emitting = None
            self.__emitting_phase = None
            self.__reacting = set()

            # If a callback was set from a rejected internal pre phase, run it now
            if callback is not None:
                callback()

        return True

    def __add_listener__(self, listener, force=False, internal=True):
        # type: (EventListenerMixin, bool, bool) -> ListenerToken
        """Add a listener and get its token."""
        if listener in self.__listeners:
            return self.get_token(listener)

        listeners = self.__listeners
        reacting = self.__reacting

        try:
            token = listeners[listener]
        except KeyError:
            token = listeners[listener] = ListenerToken(self, listener)

        if force and self.__emitting is not None:
            reacting.add(listener)

        if not internal:
            self.__external_listeners.add(listener)

        return token

    def __remove_listener__(self, listener, force=False, internal=True):
        # type: (EventListenerMixin, bool, bool) -> None
        """Remove a listener."""
        if not internal and listener not in self.__external_listeners:
            return
        self.__listeners.pop(listener, None)
        self.__external_listeners.discard(listener)
        if force:
            self.__reacting.discard(listener)

    def __get_token__(self, listener):
        # type: (EventListenerMixin) -> ListenerToken
        """Get token for listener."""
        return self.__listeners[listener]

    def add_listener(self, listener, force=False):
        # type: (EventListenerMixin, bool) -> ListenerToken
        """Add a listener and get its token."""
        assert_is_instance(listener, EventListenerMixin)
        return self.__add_listener__(listener, force=force, internal=False)

    def remove_listener(self, listener, force=False):
        # type: (EventListenerMixin, bool) -> None
        """Remove a listener."""
        self.__remove_listener__(listener, force=force, internal=False)

    def get_token(self, listener):
        # type: (EventListenerMixin) -> ListenerToken
        """Get token for listener."""
        if listener not in self.__external_listeners:
            raise KeyError(listener)
        return self.__get_token__(listener)

    @property
    def __broadcaster(self):
        # type: () -> Broadcaster
        """Broadcaster."""
        broadcaster = self.__broadcaster_ref()
        if broadcaster is not None:
            return broadcaster
        error = "broadcaster is no longer alive"
        raise ReferenceError(error)

    @property
    def listeners(self):
        # type: () -> FrozenSet[EventListenerMixin, ...]
        """Listeners."""
        return frozenset(self.__external_listeners)

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
