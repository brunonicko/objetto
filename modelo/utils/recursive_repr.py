from threading import local
from typing import Callable

__all__ = ["recursive_repr"]

_local = local()
_local.reprs = set()


def recursive_repr(func):
    # type: (Callable) -> Callable
    """Decorate a '__repr__' method and prevents a recursive loop."""

    def decorated(self, *args, **kwargs):
        """Decorated """
        self_id = id(self)
        try:
            reprs = _local.reprs
        except AttributeError:
            reprs = _local.reprs = set()
        if self_id in reprs:
            return "(...)"
        else:
            try:
                reprs.add(self_id)
                return func(self, *args, **kwargs)
            finally:
                reprs.remove(self_id)

    return decorated
