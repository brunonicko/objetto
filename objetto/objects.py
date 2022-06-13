from typing import TypeVar

from .core import AbstractObject, get_context, filter_objs

__all__ = ["ValueObject"]

T = TypeVar("T")


class ValueObject(AbstractObject[T]):
    __slots__ = ()

    @classmethod
    def __init_state__(cls, value):
        adoptions = filter_objs((value,))
        return value, adoptions

    def __init__(self, value: T):
        super().__init__(value)

    @property
    def value(self) -> T:
        with get_context() as ctx:
            return ctx.get_store().get_state(self)

    @value.setter
    def value(self, value: T) -> None:
        with get_context(frozen=False) as ctx:
            old_value = ctx.get_store().get_state(self)
            adoptions = filter_objs((value,))
            releases = filter_objs((old_value,))
            ctx.evolve(self, value, None, adoptions, releases)
