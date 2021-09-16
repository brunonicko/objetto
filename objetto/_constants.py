# -*- coding: utf-8 -*-

from weakref import ref
from enum import Enum, unique

from .utils.base import final

__all__ = ["Phase", "DEAD_REF"]


@final
@unique
class Phase(Enum):
    PRE = "PRE"
    POST = "POST"


DEAD_REF = ref(type("Dead", (object,), {"__slots__": ("__weakref__",)})())
