# -*- coding: utf-8 -*-
"""
An :class:`objetto.applications.Application` oversees all
:class:`objetto.bases.BaseObject` objects that are meant to work together.
It provides different contexts for managing and keeping track of their changes.

Objects that are part of different applications see each other as regular values and
can never be part of the same hierarchy.

An application can have root objects defined by :func:`objetto.applications.root`,
which are always available at the top of the hierarchy, and cannot be parented under
other objects.
"""

from typing import TYPE_CHECKING

from ._applications import (
    BO,
    Application,
    ApplicationMeta,
    ApplicationProperty,
    ApplicationRoot,
    ApplicationSnapshot,
)

if TYPE_CHECKING:
    from typing import Any, Optional, Type

__all__ = [
    "ApplicationMeta",
    "Application",
    "ApplicationProperty",
    "ApplicationSnapshot",
    "root",
]


def root(obj_type, priority=None, **kwargs):
    # type: (Type[BO], Optional[int], Any) -> ApplicationRoot[BO]
    """
    Describes a root object that gets initialized with the application.

    .. code:: python

        >>> from objetto import Application, Object, attribute, root

        >>> class MyObject(Object):
        ...     name = attribute(str)
        ...
        >>> class MyApplication(Application):  # subclass for adding roots
        ...     root_a = root(MyObject, name="Root A")  # describe root
        ...     root_b = root(MyObject, name="Root B")  # describe root
        ...
        >>> app = MyApplication()  # instantiate the application
        >>> app.root_a  # access a root object
        MyObject(name='Root A')

    :param obj_type: Object type.
    :type obj_type: type[objetto.bases.BaseObject]

    :param priority: Initialization priority.
    :type priority: int or None

    :param kwargs: Keyword arguments to be passed to the object's `__init__`.

    :return: Application root descriptor.
    :rtype: objetto.applications.ApplicationRoot

    :raises ValueError: Used reserved keyword argument.
    :raises TypeError: Invalid object type.
    """
    return ApplicationRoot(obj_type, priority=priority, **kwargs)
