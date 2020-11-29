# -*- coding: utf-8 -*-
"""Applications."""

from typing import TYPE_CHECKING

from ._applications import BO, ApplicationRoot, Application

if TYPE_CHECKING:
    from typing import Type, Optional, Any

__all__ = ["root", "Application"]


def root(obj_type, priority=None, **kwargs):
    # type: (Type[BO], Optional[int], Any) -> ApplicationRoot[BO]
    """
    Describes a root object that gets initialized with the application.

    :param obj_type: Object type.
    :param priority: Initialization priority.
    :param kwargs: Keyword arguments to be passed to object's '__init__'.
    :raises ValueError: Used reserved keyword argument.
    :raises TypeError: Invalid object type.
    """
    return ApplicationRoot(obj_type, priority=priority, **kwargs)
