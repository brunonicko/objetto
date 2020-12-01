# -*- coding: utf-8 -*-
"""Constants."""

from ._applications import Phase
from ._objects import DELETED

__all__ = ["DELETED", "PRE", "POST"]


PRE = Phase.PRE
"""Phase before the changes are applied."""

POST = Phase.POST
"""Phase after the changes are applied."""
