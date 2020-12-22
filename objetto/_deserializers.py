# -*- coding: utf-8 -*-
"""Deserializers."""

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from six import string_types

from ._bases import Base
from .utils.reraise_context import ReraiseContext
from .utils.type_checking import assert_is_subclass

if TYPE_CHECKING:
    from typing import Any, Type

__all__ = [
    "BaseDeserializer",
    "EnumDeserializer",
]


class BaseDeserializer(Base):
    """
    Base callable deserializer object.

    Inherits from:
      - :class:`objetto.bases.Base`

    Inherited By:
      - :class:`objetto.deserializers.EnumDeserializer`
    """

    __slots__ = ()

    @abstractmethod
    def __call__(self, serialized, **kwargs):
        # type: (Any, Any) -> Any
        """
        Call with value and optional keyword arguments.

        :param serialized: Serialized.

        :param kwargs: Keyword arguments.

        :return: Value.
        """
        raise NotImplementedError()


class EnumDeserializer(BaseDeserializer):
    """
    Deserializer for :class:`enum.Enum` values.

    Inherits from:
      - :class:`objetto.bases.BaseDeserializer`

    :param enum: Enum class.
    :type enum: type[enum.Enum]

    :param by_name: Whether to deserialize by name instead of by value.
    :type by_name: bool

    :raises TypeError: Provided wrong paramater type.
    """

    __slots__ = ("__enum", "__by_name")

    def __init__(self, enum, by_name=False):
        # type: (Type[Enum], bool) -> None

        with ReraiseContext(TypeError, "'enum' parameter"):
            assert_is_subclass(enum, Enum)

        self.__enum = enum
        self.__by_name = bool(by_name)

    def __call__(self, serialized, **kwargs):
        # type: (Enum, Any) -> Any
        """
        Call with value and optional keyword arguments.

        :param serialized: Serialized.

        :param kwargs: Keyword arguments.

        :return: Enum value.
        :rtype: enum.Enum

        :raises TypeError: Deserializing by name but serialized is not a string.
        """
        if self.by_name:
            if not isinstance(serialized, string_types):
                error = (
                    "can't deserialize '{}' by name as serialized value is not a string"
                ).format(type(self.enum).__name__)
                raise TypeError(error)
            return self.enum[serialized]
        else:
            return self.enum(serialized)

    @property
    def enum(self):
        # type: () -> Type[Enum]
        """
        Enum class.

        :rtype: type[enum.Enum]
        """
        return self.__enum

    @property
    def by_name(self):
        # type: () -> bool
        """
        Whether to deserialize by name instead of by value.

        :rtype: bool
        """
        return self.__by_name
