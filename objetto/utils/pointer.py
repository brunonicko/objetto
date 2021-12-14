from typing import Generic, TypeVar

from basicco.utils.weak_reference import UniqueHashWeakReference

__all__ = ["Pointer"]

_T = TypeVar("_T")


class Pointer(UniqueHashWeakReference, Generic[_T]):
    __slots__ = ()

    @property
    def obj(self):
        # type: () -> _T
        obj = self()
        if obj is None:
            error = "object is no longer alive"
            raise ReferenceError(error)
        return obj
