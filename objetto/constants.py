# -*- coding: utf-8 -*-
"""Constants."""

from ._objects import DELETED
from ._applications import Phase

__all__ = ["DELETED", "PRE", "POST"]


PRE = Phase.PRE
"""Phase before the changes are applied."""

POST = Phase.POST
"""Phase after the changes are applied."""
