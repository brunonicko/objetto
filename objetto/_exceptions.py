# -*- coding: utf-8 -*-

from os import linesep
from traceback import format_exception
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID
    from typing import Iterable, Tuple, Callable

    from ._structures import ObserverError

__all__ = [
    "AbstractObjettoException",
    "RevertException",
    "RejectException",
    "ObserversError",
]


class AbstractObjettoException(Exception):
    pass


class RevertException(AbstractObjettoException):
    pass


class RejectException(AbstractObjettoException):

    def __init__(self, message, action_uuid, callback):
        # type: (str, UUID, Callable[[], None]) -> None
        message = (
            "{}action with uuid '{}' was rejected but callback could not run because "
            "rejection was not raised and/or caught within the correct context"
        ).format(
            "'{}'; ".format(message) if message else "",
            action_uuid,
        )
        super(RejectException, self).__init__(message)

        self.__action_uuid = action_uuid
        self.__callback = callback

    @property
    def action_uuid(self):
        # type: () -> UUID
        """Action uuid."""
        return self.__action_uuid

    @property
    def callback(self):
        # type: () -> Callable[[], None]
        """Callback to run after action is reverted."""
        return self.__callback


class ObserversError(AbstractObjettoException):

    def __init__(self, message="observers raised exceptions", observer_errors=()):
        # type: (str, Iterable[ObserverError]) -> None
        observer_errors = tuple(observer_errors)
        if observer_errors:
            message += " (see tracebacks below)"
            for observer_error in observer_errors:
                message += (
                    "{linesep}{linesep}"
                    "Observer: {observer}{linesep}"
                    "Action: {action}{linesep}"
                    "Phase: {phase}{linesep}"
                    "{traceback}"
                ).format(
                    linesep=linesep,
                    observer=observer_error.exception_info.observer,
                    action=observer_error.action,
                    phase=observer_error.phase,
                    traceback="".join(
                        format_exception(
                            observer_error.exception_info.exception_type,
                            observer_error.exception_info.exception,
                            observer_error.exception_info.traceback,
                        )
                    ),
                )
        super(ObserversError, self).__init__(message)

        self.__observer_errors = observer_errors

    @property
    def observer_errors(self):
        # type: () -> Tuple[ObserverError, ...]
        return self.__observer_errors
