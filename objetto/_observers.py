# -*- coding: utf-8 -*-
"""Observer mixin class."""

from abc import abstractmethod
from types import TracebackType
from typing import TYPE_CHECKING, Optional, Type, cast
from weakref import ref

from ._applications import Action, Phase
from ._bases import final
from ._objects import BaseObject
from .data import Data, data_attribute
from .utils.reraise_context import ReraiseContext
from .utils.subject_observer import Observer, ObserverToken
from .utils.type_checking import assert_is_instance

if TYPE_CHECKING:
    from typing import Any

    from .data import DataAttribute

__all__ = ["ActionObserver", "ActionObserverToken", "ActionObserverExceptionData"]


class InternalObserver(Observer):
    """
    Internal observer.

    :param action_observer: Action observer.
    """

    def __init__(self, action_observer):
        # type: (ActionObserver) -> None
        self.action_observer_ref = ref(action_observer)

    def __observe__(self, *payload):
        # type: (Any) -> None
        """
        Receive payload, unpack it, and relay it to the action observer.

        :param payload: Payload.
        """
        action_observer = self.action_observer_ref()
        if action_observer is not None:
            action, phase = payload
            action_observer.__observe__(action, phase)


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
        ...     def __observe__(self, action, phase):
        ...         print((action.change.name, phase.value))
        ...
        >>> app = Application()
        >>> person = Person(app)
        >>> observer = PersonObserver()
        >>> token = observer.start_observing(person)
        >>> person.name = "Einstein"
        ('Update Attributes', 'PRE')
        ('Update Attributes', 'POST')
    """

    __internal_observer = None  # type: Optional[InternalObserver]

    @abstractmethod
    def __observe__(self, action, phase):
        # type: (Action, Phase) -> None
        """
        Observe an action (and its execution phase) from an object.

        :param action: Action.
        :type action: objetto.objects.Action

        :param phase: Phase.
        :type phase: :data:`objetto.constants.PRE` or :data:`objetto.constants.POST`

        :raises NotImplementedError: Abstract method not implemented.
        """
        error = (
            "object action observer class '{}' did not implement abstract method "
            "'__observe__'; can't observe action {} during {}"
        ).format(type(self).__name__, action, phase)
        raise NotImplementedError(error)

    def start_observing(self, obj):
        # type: (BaseObject) -> ActionObserverToken
        """
        Start observing an object for actions.

        :param obj: Object.
        :type obj: objetto.objects.Object

        :return: Observer token.
        :rtype: objetto.observers.ActionObserverToken

        :raises TypeError: Invalid 'obj' parameter type.
        :raises RuntimeError: Can't start observing while object is initializing.
        """
        with ReraiseContext(TypeError, "'obj' parameter"):
            assert_is_instance(obj, BaseObject)
        if obj._initializing:
            error = "can't start observing object {} during its initialization"
            raise RuntimeError(error)
        obj.__.subject.register_observer(self.__observer)
        action_observer_token = cast(
            "ActionObserverToken",
            ActionObserverToken.__make__(obj.__.subject, self.__observer),
        )
        return action_observer_token

    def stop_observing(self, obj):
        # type: (BaseObject) -> None
        """
        Stop observing an object for actions.

        :param obj: Object.
        :type obj: objetto.objects.Object

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


# noinspection PyAbstractClass
class ActionObserverToken(ObserverToken):
    """
    Allows control over observers' order/priority.

    Inherits from:
      - :class:`objetto.utils.subject_observer.ObserverToken`

    .. note::
        This class can't be instantiated directly. A token should be retrieved when an
        action observer starts observing an object.

    .. code:: python

        >>> from objetto import Application, Object, attribute
        >>> from objetto.constants import POST
        >>> from objetto.observers import ActionObserver

        >>> observed_names = []
        ...
        >>> class Person(Object):
        ...     name = attribute(str, default="Albert")
        ...
        >>> class PersonObserver(ActionObserver):
        ...     def __init__(self, this, dependency=None):
        ...         self.this = this
        ...         self.dependency = dependency
        ...
        ...     def __observe__(self, action, phase):
        ...         if self.dependency:
        ...             self.dependency.wait()
        ...         if phase is POST:
        ...             observed_names.append(
        ...                 "{} {}".format(self.this, action.change.new_values["name"])
        ...             )
        ...
        >>> app = Application()
        >>> person = Person(app)

        >>> observer_a = PersonObserver("A")
        >>> token_a = observer_a.start_observing(person)

        >>> observer_b = PersonObserver("B", dependency=token_a)
        >>> token_b = observer_b.start_observing(person)

        >>> person.name = "Einstein"
        >>> observed_names  # note how A will always observe the change before B does
        ['A Einstein', 'B Einstein']
    """

    __slots__ = ()

    @property
    def observer(self):
        # type: () -> Optional[ActionObserver]
        """
        Action observer.

        :rtype: objetto.observers.ActionObserver or None
        """
        internal_observer = self._observer_ref()
        if internal_observer is None:
            return None
        else:
            return cast("InternalObserver", internal_observer).action_observer_ref()


@final
class ActionObserverExceptionData(Data):
    """
    Describes an exception raised by an observer while observing an action.

    Inherits from:
      - :class:`objetto.data.Data`
    """

    observer = data_attribute(
        ActionObserver, checked=False
    )  # type: DataAttribute[ActionObserver]
    """
    Action observer.

    :type: objetto.observers.ActionObserver
    """

    action = data_attribute(Action, checked=False)  # type: DataAttribute[Action]
    """
    Action.

    :type: objetto.objects.Action
    """

    phase = data_attribute(Phase, checked=False)  # type: DataAttribute[Phase]
    """
    Phase.

    :type: :data:`objetto.constants.PRE` or :data:`objetto.constants.POST`
    """

    exception_type = data_attribute(
        (type(BaseException), None), checked=False
    )  # type: DataAttribute[Optional[Type[BaseException]]]
    """
    Exception type.

    :type: type[BaseException] or None
    """

    exception = data_attribute(
        (BaseException, None), checked=False
    )  # type: DataAttribute[Optional[BaseException]]
    """
    Exception.

    :type: BaseException or None
    """

    traceback = data_attribute(
        (TracebackType, None), checked=False
    )  # type: DataAttribute[Optional[TracebackType]]
    """
    Traceback.

    :type: types.TracebackType or None
    """
