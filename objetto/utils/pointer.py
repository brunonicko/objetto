"""Weak object pointer."""

from weakref import ref, WeakValueDictionary
from typing import TYPE_CHECKING, TypeVar

from .base import GenericBase, final

if TYPE_CHECKING:
    from typing import Optional, Type

T = TypeVar("T")

__all__ = ["Pointer"]


def _pointer_reducer(cls, obj):
    # type: (Type[Pointer[T]], Optional[T]) -> Pointer[T]
    if obj is None:
        self = super(Pointer, cls).__new__(cls)
        self._obj_ref = None
    else:
        self = cls(obj)
    return self


@final
class Pointer(GenericBase[T]):
    """Stores a weak reference to an object."""

    __slots__ = ("__weakref__", "_obj_ref")

    _CACHE = WeakValueDictionary()  # type: WeakValueDictionary[int, Pointer]

    @staticmethod
    def __new__(cls, obj):
        # type: (Type[Pointer[T]], T) -> Pointer[T]
        obj_id = id(obj)
        try:
            self = Pointer._CACHE[obj_id]
        except KeyError:
            pass
        else:
            try:
                if self.obj is obj:
                    return self
            except ReferenceError:
                pass
        self = Pointer._CACHE[obj_id] = super(Pointer, cls).__new__(cls)
        return self

    def __init__(self, obj):
        # type: (T) -> None
        self._obj_ref = ref(obj)

    def __reduce__(self):
        return _pointer_reducer, (type(self), self._obj,)

    @property
    def _obj(self):
        # type: () -> Optional[T]
        obj_ref = self._obj_ref
        if obj_ref is None:
            obj = None
        else:
            obj = obj_ref()
        return obj

    @property
    def obj(self):
        # type: () -> T
        """Object."""
        obj = self._obj
        if obj is None:
            error = "object is no longer in memory"
            raise ReferenceError(error)
        return obj
