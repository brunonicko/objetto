# -*- coding: utf-8 -*-
"""
Implementation of the `Subject-Observer Pattern
<https://en.wikipedia.org/wiki/Observer_pattern>`_.
"""

from abc import abstractmethod
from sys import exc_info
from types import TracebackType
from typing import TYPE_CHECKING, NamedTuple, Optional, Type
from weakref import WeakKeyDictionary, ref

if TYPE_CHECKING:
    from typing import Any, Dict, List, MutableMapping, Set, Tuple

__all__ = ["Subject", "Observer", "ObserverToken", "ObserverExceptionInfo"]


class Subject(object):
    """Sends payloads to observers."""

    __slots__ = (
        "__weakref__",
        "__observers",
        "__observing",
        "__receiving",
        "__failed",
        "__payload",
        "__exception_infos",
    )

    def __init__(self):
        # type: () -> None
        self.__observers = WeakKeyDictionary(
            {}
        )  # type: MutableMapping[Observer, ObserverToken]
        self.__observing = set()  # type: Set[Observer]
        self.__receiving = set()  # type: Set[Observer]
        self.__failed = set()  # type: Set[Observer]
        self.__payload = None  # type: Optional[Tuple[Any, ...]]
        self.__exception_infos = []  # type: List[ObserverExceptionInfo]

    def __deepcopy__(self, memo=None):
        # type: (Optional[Dict[int, Any]]) -> Subject
        """
        Get a new subject, does not copy registered observers.

        :return: New subject.
        """
        if memo is None:
            memo = {}
        try:
            return memo[id(self)]
        except KeyError:
            subject_copy = memo[id(self)] = type(self)()
            return subject_copy

    def __copy__(self):
        # type: () -> Subject
        """
        Get a new subject, does not copy registered observers.

        :return: New subject.
        """
        return type(self)()

    def __reduce__(self):
        # type: () -> Tuple[Type[Subject], Any]
        """
        Reduce for pickling purposes.

        :return: Subject class, no arguments.
        """
        return type(self), ()

    def wait(self, token):
        # type: (ObserverToken) -> None
        """
        Wait for the token's observer to receive the payload before continuing.

        :param token: Observer token.
        """
        if self.__payload is not None:
            observer = token.observer
            if observer in self.__receiving:
                error = "token wait cycle detected in {}".format(observer)
                raise RuntimeError(error)
            if observer in self.__failed:
                error = "can't wait for failed observer {}".format(observer)
                raise RuntimeError(error)
            if observer in self.__observing:
                self.__observing.remove(observer)
                self.__receiving.add(observer)
                try:
                    observer.__receive__(*self.__payload)
                except Exception:
                    exception_type, exception, traceback = exc_info()
                    exception_info = ObserverExceptionInfo(
                        observer=observer,
                        exception_type=exception_type,
                        exception=exception,
                        traceback=traceback,
                    )
                    self.__exception_infos.append(exception_info)
                    self.__failed.add(observer)
                    raise
                finally:
                    self.__receiving.remove(observer)

    def send(self, *payload):
        # type: (Any) -> Tuple[ObserverExceptionInfo, ...]
        """
        Send payload to all observers.

        :param payload: Payload.
        :return: Exception infos (for exceptions raised during observers' responses).
        :raises RuntimeError: Already sending.
        """
        if self.__payload is not None:
            error = "already sending {}, can't send {}".format(self.__payload, payload)
            raise RuntimeError(error)

        self.__observing = set(self.__observers)
        self.__payload = payload

        while self.__observing:
            observer = self.__observing.pop()
            self.__receiving.add(observer)
            try:
                observer.__receive__(*self.__payload)
            except Exception:
                exception_type, exception, traceback = exc_info()
                exception_info = ObserverExceptionInfo(
                    observer=observer,
                    exception_type=exception_type,
                    exception=exception,
                    traceback=traceback,
                )
                self.__exception_infos.append(exception_info)
                self.__failed.add(observer)
            finally:
                self.__receiving.remove(observer)

        exception_infos = tuple(self.__exception_infos)

        self.__observing.clear()
        self.__receiving.clear()
        self.__failed.clear()
        self.__payload = None
        del self.__exception_infos[:]

        return exception_infos

    def register_observer(self, observer):
        # type: (Observer) -> ObserverToken
        """
        Register an observer and get its token.

        :param observer: Observer.
        :return: Observer token.
        """
        try:
            token = self.__observers[observer]
        except KeyError:
            token = self.__observers[observer] = ObserverToken.__make__(self, observer)
        return token

    def deregister_observer(self, observer):
        # type: (Observer) -> None
        """
        De-register an observer.

        :param observer: Observer.
        """
        self.__observers.pop(observer, None)

    def get_token(self, observer):
        # type: (Observer) -> ObserverToken
        """
        Get token for already registered observer.

        :param observer: Observer.
        :return: Observer token.
        :raises ValueError: Observer is not registered.
        """
        try:
            return self.__observers[observer]
        except KeyError:
            pass
        error = "observer is not registered"
        raise ValueError(error)


class Observer(object):
    """
    Observes payloads sent from a subject.

    .. code:: python

        >>> from objetto.utils.subject_observer import Subject, Observer

        >>> class MyObserver(Observer):
        ...
        ...     def __receive__(self, *payload):
        ...         print("received payload {}".format(payload))
        ...
        >>> subject = Subject()
        >>> observer = MyObserver()
        >>> token = observer.start_observing(subject)
        >>> exception_infos = subject.send(1, 2, 3)
        received payload (1, 2, 3)
    """

    @abstractmethod
    def __receive__(self, *payload):
        # type: (Any) -> None
        """
        Receive a payload sent from a subject and react to it.

        :param payload: Payload.
        :raises NotImplementedError: Abstract method not implemented.
        """
        error = (
            "observer class '{}' did not implement abstract method '__receive__'; "
            "can't receive payload {}"
        ).format(type(self).__name__, payload)
        raise NotImplementedError(error)

    def start_observing(self, subject):
        # type: (Subject) -> ObserverToken
        """
        Start observing a subject.

        :param subject: Subject.
        :return: Observer token.
        """
        return subject.register_observer(self)

    def stop_observing(self, subject):
        # type: (Subject) -> None
        """
        Stop observing a subject.

        :param subject: Subject.
        """
        subject.deregister_observer(self)


class ObserverToken(object):
    """
    Allows control over observers' order/priority.

    .. note::
        This class can't be instantiated directly. A token should be retrieved when an
        observer starts observing a subject or by using the :meth:`Subject.get_token`
        method.

    .. code:: python

        >>> from objetto.utils.subject_observer import Subject, Observer

        >>> class MyObserver(Observer):
        ...     def __init__(self, name, actions, dependency=None):
        ...         self.name = name
        ...         self.actions = actions
        ...         self.dependency = dependency
        ...
        ...     def __receive__(self, *payload):
        ...         if self.dependency:
        ...             self.dependency.wait()
        ...         action = "{} received payload {}".format(self.name, payload)
        ...         self.actions.append(action)
        ...
        >>> subject = Subject()
        >>> executed_actions = []

        >>> observer_a = MyObserver("A", executed_actions)
        >>> token_a = observer_a.start_observing(subject)

        >>> observer_b = MyObserver("B", executed_actions, dependency=token_a)
        >>> token_b = observer_b.start_observing(subject)

        >>> exception_infos = subject.send(1, 2, 3)
        >>> executed_actions  # note how A will always receive the payload before B
        ['A received payload (1, 2, 3)', 'B received payload (1, 2, 3)']
    """

    __slots__ = ("__subject_ref", "__observer_ref")

    @classmethod
    def __make__(cls, subject, observer):
        # type: (Subject, Observer) -> ObserverToken
        """
        Make a new token.

        :param subject: Subject.
        :param observer: Observer.
        :return: New token.
        """
        self = cls.__new__(cls)
        self.__subject_ref = ref(subject)
        self.__observer_ref = ref(observer)
        return self

    def __init__(self, subject, observer):
        # type: (Subject, Observer) -> None
        self.__subject_ref = ref(subject)
        self.__observer_ref = ref(observer)
        error = "'{}' object can't be instantiated directly".format(type(self).__name__)
        raise RuntimeError(error)

    def wait(self):
        # type: () -> None
        """Wait for the associated observer to receive payload before continuing."""
        subject = self.__subject_ref()
        if subject is None:
            return
        observer = self.observer
        if observer is None:
            return
        subject.wait(self)

    @property
    def observer(self):
        """Observer."""
        return self.__observer_ref()


class ObserverExceptionInfo(
    NamedTuple(
        "ObserverExceptionInfo",
        (
            ("observer", Observer),
            ("exception_type", Optional[Type[BaseException]]),
            ("exception", Optional[BaseException]),
            ("traceback", Optional[TracebackType]),
        ),
    )
):
    """
    Describes an exception raised by an observer receiving a payload.

    :param observer: Observer.
    :param exception_type: Exception type.
    :param exception: Exception.
    :param traceback: Traceback.
    """

    __slots__ = ()
