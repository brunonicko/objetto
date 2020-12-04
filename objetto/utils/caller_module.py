# -*- coding: utf-8 -*-
"""Utilities to retrieve the caller's module name."""

from inspect import getmodule, stack
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

__all__ = ["get_caller_module"]


def get_caller_module(frames=0):
    # type: (int) -> Optional[str]
    """
    Get caller module name if possible.

    :param frames: How many frames in the stack to go back relative to the caller.
    :type frames: int

    :return: Module name or `None`.
    :rtype: str or None
    """
    try:
        frame = stack()[2 + frames]
        module = getmodule(frame[0])
    except IndexError:
        return None
    else:
        if module is None:
            return None
        else:
            return module.__name__
