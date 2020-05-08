# -*- coding: utf-8 -*-
"""Serializable object mix-in."""

from abc import abstractmethod
from typing import Dict, Any

from .._base.constants import SERIALIZED_DOT_PATH_KEY
from ..utils.type_checking import resolve_dot_path

__all__ = ["SerializableObjectMixin"]


class SerializableObjectMixin(object):
    """Serializable object mix-in."""

    __slots__ = ()

    @abstractmethod
    def _serialize(self):
        # type: () -> Dict[str, Any]
        """Serialize."""
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _create(cls, serialized):
        """Create from serialized."""
        raise NotImplementedError()

    def serialize(self):
        # type: () -> Dict[str, Any]
        """Serialize."""
        serialized = self._serialize()
        serialized.update(
            {
                SERIALIZED_DOT_PATH_KEY: type(self).__module__
                + "."
                + type(self).__name__,
            }
        )
        return serialized

    @classmethod
    def create(cls, serialized):
        """Create from serialized."""
        class_dot_path = serialized[SERIALIZED_DOT_PATH_KEY]
        actual_cls = resolve_dot_path(class_dot_path)
        if (
            actual_cls is not cls
            and not issubclass(cls, actual_cls)
            and not issubclass(actual_cls, cls)
        ):
            error = (
                "serialized object's class is '{}', cannot be deserialized by "
                "'{}.create'"
            ).format(actual_cls.__name__, cls.__name__)
            raise TypeError(error)
        return actual_cls._create(serialized)
