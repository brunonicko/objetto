# -*- coding: utf-8 -*-
"""Constants."""

from ._base.constants import DEAD_WEAKREF, MISSING, DELETED, SERIALIZED_DOT_PATH_KEY
from ._components.attributes import ATTRIBUTE_NAME_REGEX
from ._components.events import EventPhase

__all__ = [
    "DEAD_WEAKREF",
    "MISSING",
    "DELETED",
    "SERIALIZED_DOT_PATH_KEY",
    "ATTRIBUTE_NAME_REGEX",
    "EventPhase"
]
