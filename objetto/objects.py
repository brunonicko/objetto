from typing import TypeVar

from ._core3 import AbstractObject, require_context, objs_only

__all__ = ["ValueObject"]

T = TypeVar("T")


class ValueObject(AbstractObject[T]):
    __slots__ = ()

    @classmethod
    def __init_state__(cls, value):
        adoptions = {}
        return value, adoptions

    def __init__(self, value: T):
        super().__init__(value)

    @property
    def value(self) -> T:
        with require_context() as ctx:
            return ctx.get_snapshot().get_state(self)

    @value.setter
    def value(self, value: T) -> None:
        with require_context() as ctx:
            old_value = ctx.get_snapshot().get_state(self)
            adoptions = objs_only((value,))
            releases = objs_only((old_value,))
            ctx.evolve(self, value, None, adoptions, releases)
