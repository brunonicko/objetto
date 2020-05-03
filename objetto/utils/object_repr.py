# -*- coding: utf-8 -*-
"""Object representation."""

from six import iteritems
from typing import Dict, Any

__all__ = ["object_repr"]


def object_repr(**attributes):
    # type: (Dict[str, Any]) -> str
    """Get object representation (using 'repr')."""
    parts = []
    for name, value in sorted(iteritems(attributes), key=lambda p: p[0]):
        part = "{}={}".format(name, repr(value))
        parts.append(part)
    return ", ".join(parts)
