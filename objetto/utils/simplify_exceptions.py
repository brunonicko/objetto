# -*- coding: utf-8 -*-
"""Decorator to simplify exception traceback when used with wrapped functions."""

import inspect
from functools import wraps
from sys import _getframe, exc_info
from typing import TYPE_CHECKING

from six import PY2

if TYPE_CHECKING:
    from typing import Callable, TypeVar

    RT = TypeVar("RT")  # Return type.

__all__ = ["simplify_exceptions"]


if PY2:

    def exec_(_code_, _globs_=None, _locs_=None):
        """Execute code in a namespace."""
        if _globs_ is None:
            frame = _getframe(1)
            _globs_ = frame.f_globals
            if _locs_ is None:
                _locs_ = frame.f_locals
            del frame
        elif _locs_ is None:
            _locs_ = _globs_
        exec("""exec _code_ in _globs_, _locs_""")


else:
    exec_ = None


def simplify_exceptions(func):
    # type: (Callable[..., RT]) -> Callable[..., RT]
    """
    To be used with a wrapped function.
    This will simplify the exception traceback by chopping up two levels of it.

    .. code:: python

        >>> from functools import wraps
        >>> from objetto.utils.simplify_exceptions import simplify_exceptions

        >>> def my_decorator(f):
        ...     @wraps(f)
        ...     @simplify_exceptions
        ...     def _wrapped(*args, **kwargs):
        ...         return f(*args, **kwargs)  # will be excluded from the traceback
        ...     return _wrapped
        ...
        >>> @my_decorator
        ... def my_function():
        ...     raise ValueError("oops; something is wrong")
        ...
        >>> my_function()
        Traceback (most recent call last):
        ValueError: oops; something is wrong

    :param func: Function to be decorated.
    :type func: function

    :return: Decorated function.
    :rtype: function
    """

    @wraps(func)
    def _decorated(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            exc_type, exc_value, exc_traceback = exc_info()

            # Re-raise without change if exception has custom arguments.
            try:
                args = inspect.getfullargspec(exc_type.__init__).args  # type: ignore
            except AttributeError:
                try:
                    # noinspection PyDeprecation
                    args = inspect.getargspec(exc_type.__init__).args  # type: ignore
                except TypeError:
                    args = ["self"]
            if len(args) != 1:
                raise

            # Chop the traceback and remove the decorated bits.
            try:
                exc_traceback = exc_traceback.tb_next
                exc_traceback = exc_traceback.tb_next
            except Exception:
                pass

            # Re-raise exception with the chopped traceback.
            if PY2:
                assert exec_ is not None
                exec_("""raise exc_type, exc_value, exc_traceback""")
            else:
                if exc.__traceback__ is not exc_traceback:
                    raise exc.with_traceback(exc_traceback)
                else:
                    raise exc

    return _decorated
