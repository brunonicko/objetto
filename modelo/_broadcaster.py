# -*- coding: utf-8 -*-

from abc import abstractmethod
from weakref import WeakKeyDictionary, ref
from slotted import Slotted, SlottedMapping
from six import raise_from

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc

from ._type_checking import assert_is_instance
from ._exceptions import StopEventPropagationException, RejectEventException
from ._constants import EventPhase
from ._base_model import BaseModel
from ._events import Event


class EventListenerMixin(object):
    """Mixin for listening and reacting to events."""

    __slots__ = ("__weakref__",)

    def __hash__(self):
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
    def __react__(self, model, event, phase):
        # type: (BaseModel, Event, EventPhase) -> None
        """React to an event."""
        raise NotImplementedError()


class ListenerToken(Slotted):
    __slots__ = ("__emitter_ref", "__listener_ref")

    def __init__(self, emitter, listener):
        self.__emitter_ref = ref(emitter)
        self.__listener_ref = ref(listener)

    def wait(self):
        emitter = self.emitter
        listener = self.listener
        if emitter is None:
            return
        if listener is None:
            return
        emitter.__wait__(self)

    @property
    def emitter(self):
        return self.__emitter_ref()

    @property
    def listener(self):
        return self.__listener_ref()


class EventEmitter(Slotted):
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
        self.__broadcaster_ref = ref(broadcaster)
        self.__internal = broadcaster.internal
        self.__event_type = event_type
        self.__listeners = WeakKeyDictionary()
        self.__emitting = None
        self.__emitting_phase = None
        self.__reacting = set()

    def __wait__(self, token):
        if self.__emitting is None:
            return
        model = self.model
        if model is None:
            return
        listener = token.listener
        if listener in self.__reacting:
            self.__reacting.remove(listener)
            listener.__react__(model, self.__emitting, self.__emitting_phase)

    def __emit__(self, event, phase):
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
        model = self.model
        if model is None:
            raise RuntimeError("model is no longer available")

        self.__emitting = event
        self.__emitting_phase = phase
        self.__reacting = reacting = set(self.__listeners)

        callback = None
        try:
            while reacting:
                listener = reacting.pop()
                try:
                    listener.__react__(model, event, phase)
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
        self.__listeners.pop(listener, None)
        if force:
            self.__reacting.discard(listener)

    def get_token(self, listener):
        return self.__listeners[listener]

    @property
    def __broadcaster(self):
        if self.__broadcaster_ref is not None:
            return self.__broadcaster_ref()

    @property
    def internal(self):
        return self.__internal

    @property
    def model(self):
        broadcaster = self.__broadcaster
        if broadcaster is not None:
            return broadcaster.model

    @property
    def event_type(self):
        return self.__event_type

    @property
    def listeners(self):
        return frozenset(self.__listeners)

    @property
    def emitting(self):
        return self.__emitting

    @property
    def emitting_phase(self):
        return self.__emitting_phase


class Events(SlottedMapping):
    __slots__ = ("__broadcaster_ref", "__event_types", "__emitters")

    def __init__(self, broadcaster, event_types):
        self.__broadcaster_ref = ref(broadcaster)
        self.__event_types = event_types
        self.__emitters = {}

    def __repr__(self):
        return repr(self.__emitters)

    def __str__(self):
        return self.__repr__()

    def __getitem__(self, event_type):
        try:
            emitter = self.__emitters[event_type]
        except KeyError:
            if event_type in self.__event_types:
                broadcaster = self.__broadcaster_ref()
                if broadcaster is None or broadcaster.model is None:
                    raise ReferenceError("object is no longer alive")
                emitter = self.__emitters[event_type] = EventEmitter(
                    broadcaster, event_type
                )
            else:
                raise
        return emitter

    def __iter__(self):
        for event_type in self.__event_types:
            yield event_type

    def __len__(self):
        return len(self.__event_types)


class Broadcaster(Slotted):
    __slots__ = ("__weakref__", "__model_ref", "__internal", "__events")

    def __init__(self, model, internal=False, event_types=frozenset()):
        self.__model_ref = ref(model)
        self.__internal = bool(internal)
        self.__events = Events(self, event_types)

    def emit(self, event, phase):
        return self.__events[event.type].__emit__(event, phase)

    @property
    def model(self):
        return self.__model_ref()

    @property
    def internal(self):
        return self.__internal

    @property
    def events(self):
        return self.__events
