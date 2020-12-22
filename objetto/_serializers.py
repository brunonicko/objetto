# -*- coding: utf-8 -*-
"""Serializers."""

from abc import abstractmethod
from typing import TYPE_CHECKING

from ._bases import Base

if TYPE_CHECKING:
    from enum import Enum
    from typing import Any

__all__ = [
    "BaseSerializer",
    "EnumSerializer",
]


class BaseSerializer(Base):
    """
    Base callable serializer object.

    Inherits from:
      - :class:`objetto.bases.Base`

    Inherited By:
      - :class:`objetto.serializers.EnumSerializer`
    """

    __slots__ = ()

    @abstractmethod
    def __call__(self, value, **kwargs):
        # type: (Any, Any) -> Any
        """
        Call with value and optional keyword arguments.

        :param value: Value.

        :param kwargs: Keyword arguments.

        :return: Serialized.
        """
        raise NotImplementedError()


class EnumSerializer(BaseSerializer):
    """
    Serializer for :class:`enum.Enum` values.

    Inherits from:
      - :class:`objetto.bases.BaseSerializer`

    :param by_name: Whether to serialize by name instead of by value.
    :type by_name: bool
    """

    __slots__ = ("__by_name",)

    def __init__(self, by_name=False):
        # type: (bool) -> None
        self.__by_name = bool(by_name)

    def __call__(self, value, **kwargs):
        # type: (Enum, Any) -> Any
        """
        Call with value and optional keyword arguments.

        :param value: Enum value.
        :type value: enum.Enum

        :param kwargs: Keyword arguments.

        :return: Serialized.
        """
        return value.name if self.by_name else value.value

    @property
    def by_name(self):
        # type: () -> bool
        """
        Whether to serialize by name instead of by value.

        :rtype: bool
        """
        return self.__by_name
