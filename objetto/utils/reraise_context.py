# -*- coding: utf-8 -*-
"""Re-raise exceptions context manager."""

from typing import TYPE_CHECKING

from six import raise_from

if TYPE_CHECKING:
    from typing import Optional, Tuple, Type, Union

__all__ = ["ReraiseContext"]


class ReraiseContext(object):
    """
    Re-raise exceptions context manager for shorter tracebacks and custom messages.

    .. code:: python

        >>> from objetto.utils.reraise_context import ReraiseContext

        >>> def func_a():
        ...     func_b()
        ...
        >>> def func_b():
        ...     func_c()
        ...
        >>> def func_c():
        ...     raise ValueError("something is wrong")
        ...
        >>> with ReraiseContext(ValueError, "oops"):
        ...     func_a()
        Traceback (most recent call last):
        ValueError: oops; something is wrong

    :param exc_type: Exception type(s) to catch.
    :type exc_type: type[Exception] or tuple[type[Exception]]

    :param message: Optional additional custom message.
    :type message: str
    """

    __slots__ = ("__exc_type", "__message")

    def __init__(
        self,
        exc_type=Exception,  # type: Union[Type[Exception], Tuple[Type[Exception], ...]]
        message=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        self.__exc_type = exc_type
        self.__message = message

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            if not isinstance(exc_val, self.exc_type):
                return False
            exc_message = "{}".format(exc_val)
            if self.message is not None:
                if exc_message:
                    exc_message = "{}; {}".format(self.message, exc_message)
                else:
                    exc_message = self.message
            exc = type(exc_val)(exc_message, *exc_val.args[1:])
            raise_from(exc, None)
        return False

    @property
    def exc_type(self):
        # type: () -> Union[Type[Exception], Tuple[Type[Exception], ...]]
        """
        Exception type(s) to catch.

        :rtype: type[Exception] or tuple[type[Exception]]
        """
        return self.__exc_type

    @property
    def message(self):
        # type: () -> Optional[str]
        """
        Optional additional custom message.

        :rtype: str or None
        """
        return self.__message
