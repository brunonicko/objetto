# -*- coding: utf-8 -*-
"""Serializable object mix-in."""

from abc import abstractmethod
from typing import Dict, Any

from .._base.constants import SERIALIZED_DOT_PATH_KEY
from ..utils.type_checking import resolve_dot_path

__all__ = ["SerializableMixin", "serialize", "create"]


class SerializableMixin(object):
    """Serializable object mix-in."""

    __slots__ = ()

    @abstractmethod
    def __serialize__(self):
        # type: () -> Dict[str, Any]
        """Serialize."""
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def __create__(cls, serialized):
        """Create from serialized."""
        raise NotImplementedError()


def serialize(obj):
    # type: (SerializableMixin) -> Dict[str, Any]
    """Serialize."""
    serialized = obj.__serialize__()
    serialized.update(
        {
            SERIALIZED_DOT_PATH_KEY: type(obj).__module__
            + "."
            + type(obj).__name__,
        }
    )
    return serialized


def create(serialized):
    """Create from serialized."""
    class_dot_path = serialized[SERIALIZED_DOT_PATH_KEY]
    cls = resolve_dot_path(class_dot_path)
    return cls.__create__(serialized)
