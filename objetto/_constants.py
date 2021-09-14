# -*- coding: utf-8 -*-

from enum import Enum, unique

from .utils.base import final

__all__ = ["Phase"]


@final
@unique
class Phase(Enum):
    PRE = "PRE"
    POST = "POST"
