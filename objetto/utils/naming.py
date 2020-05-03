# -*- coding: utf-8 -*-
"""Naming utilities."""

from typing import AnyStr

__all__ = ["privatize_name"]


def privatize_name(cls_name, name):
    # type: (str, AnyStr) -> str
    """Privatize an attribute name if necessary."""
    if name.startswith("__") and not name.endswith("__"):
        return "_{}{}".format(cls_name.lstrip("_"), name)
    return name
