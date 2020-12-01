# -*- coding: utf-8 -*-
"""Applications."""

from typing import TYPE_CHECKING

from ._applications import BO, Application, ApplicationRoot

if TYPE_CHECKING:
    from typing import Any, Optional, Type

__all__ = ["Application", "root"]


def root(obj_type, priority=None, **kwargs):
    # type: (Type[BO], Optional[int], Any) -> ApplicationRoot[BO]
    """
    Describes a root object that gets initialized with the application.

    :param obj_type: Object type.
    :param priority: Initialization priority.
    :param kwargs: Keyword arguments to be passed to the object's `__init__`.
    :raises ValueError: Used reserved keyword argument.
    :raises TypeError: Invalid object type.
    """
    return ApplicationRoot(obj_type, priority=priority, **kwargs)
