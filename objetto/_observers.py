# -*- coding: utf-8 -*-
"""Observer mixin class."""

from abc import abstractmethod
from typing import TYPE_CHECKING
from weakref import ref

from ._objects import BaseObject
from .utils.reraise_context import ReraiseContext
from .utils.subject_observer import Observer, ObserverToken
from .utils.type_checking import assert_is_instance

if TYPE_CHECKING:
    from typing import Any, Optional

    from ._applications import Action, Phase

__all__ = ["ActionObserver"]


class InternalObserver(Observer):
    """
    Internal observer.

    :param action_observer: Action observer.
    """

    def __init__(self, action_observer):
        # type: (ActionObserver) -> None
        self.action_observer_ref = ref(action_observer)

    def __receive__(self, *payload):
        # type: (Any) -> None
        """
        Receive payload, unpack it, and relay it to the action observer.

        :param payload: Payload.
        """
        action_observer = self.action_observer_ref()
        if action_observer is not None:
            action, phase = payload
            action_observer.__receive__(action, phase)


# noinspection PyAbstractClass
class ActionObserver(object):
    """
    Mixin/abstract class for observing an object for actions.

    .. code:: python

        >>> from objetto import Application, Object, attribute
        >>> from objetto.observers import ActionObserver

        >>> class Person(Object):
        ...     name = attribute(str, default="Albert")
        ...
        >>> class PersonObserver(ActionObserver):
        ...
        ...     def __receive__(self, action, phase):
        ...         print(action.change.name, phase.value)
        ...
        >>> app = Application()
        >>> person = Person(app)
        >>> observer = PersonObserver()
        >>> token = observer.start_observing(person)
        >>> person.name = "Einstein"
        Update Attributes PRE
        Update Attributes POST
    """

    __internal_observer = None  # type: Optional[InternalObserver]

    @abstractmethod
    def __receive__(self, action, phase):
        # type: (Action, Phase) -> None
        """
        Receive an action (and its phase) from an object and react to it.

        :param action: Action.
        :param phase: Phase.
        :raises NotImplementedError: Abstract method not implemented.
        """
        error = (
            "object action observer class '{}' did not implement abstract method "
            "'__receive__'; can't receive action {} during {}"
        ).format(type(self).__name__, action, phase)
        raise NotImplementedError(error)

    def start_observing(self, obj):
        # type: (BaseObject) -> ObserverToken
        """
        Start observing an object for actions.

        :param obj: Object.
        :return: Observer token.
        :raises TypeError: Invalid 'obj' parameter type.
        :raises RuntimeError: Can't start observing while object is initializing.
        """
        with ReraiseContext(TypeError, "'obj' parameter"):
            assert_is_instance(obj, BaseObject)
        if obj._initializing:
            error = "can't start observing object {} during its initialization"
            raise RuntimeError(error)
        return obj.__.subject.register_observer(self.__observer)

    def stop_observing(self, obj):
        # type: (BaseObject) -> None
        """
        Stop observing an object for actions.

        :param obj: Object.
        :raises TypeError: Invalid 'obj' parameter type.
        """
        with ReraiseContext(TypeError, "'obj' parameter"):
            assert_is_instance(obj, BaseObject)
        obj.__.subject.deregister_observer(self.__observer)

    @property
    def __observer(self):
        # type: () -> InternalObserver
        """Internal observer."""
        if self.__internal_observer is None:
            self.__internal_observer = InternalObserver(self)
        return self.__internal_observer
