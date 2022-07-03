import dataclasses
from typing import Any, TypeVar, Optional

from .core import Hierarchy, AbstractObject, Event, require_context, objs_only

__all__ = ["ValueObject"]

T = TypeVar("T")


@dataclasses.dataclass(frozen=True)
class ValueChanged(Event[T]):
    old_value: T
    new_value: T


class ValueObject(AbstractObject[T]):
    __slots__ = ("__hierarchy",)

    @classmethod
    def __init_state__(cls, value, hierarchy):
        if hierarchy:
            adoptions = {hierarchy: objs_only((value,))}
        else:
            adoptions = {}
        return value, adoptions

    def __init__(self, value: T, hierarchy: Optional[Hierarchy] = None):
        self.__hierarchy = hierarchy
        super().__init__(value, hierarchy)

    def __repr__(self):
        try:
            with require_context():
                hierarchy_repr = "" if self.__hierarchy is None else f", hierarchy=...)"
                return f"{type(self).__name__}(value={self.value!r}{hierarchy_repr})"
        except Exception:
            return super().__repr__()

    @property
    def value(self) -> T:
        with require_context() as ctx:
            return ctx.get_snapshot().get_state(self)

    @value.setter
    def value(self, value: T) -> None:
        with require_context() as ctx:
            old_value = ctx.get_snapshot().get_state(self)
            event = ValueChanged(old_value=old_value, new_value=value)
            if self.__hierarchy:
                adoptions = {self.__hierarchy: objs_only((value,))}
                releases = {self.__hierarchy: objs_only((old_value,))}
            else:
                adoptions = {}
                releases = {}
            ctx.update(self, value, event, adoptions, releases)
