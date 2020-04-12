# -*- coding: utf-8 -*-
"""Constants."""

from ._constants import SpecialValue as _SpecialValue
from ._constants import PACKAGE_LOADER_DOT_PATH_ENV_VAR

__all__ = ["MISSING", "DELETED", "PACKAGE_LOADER_DOT_PATH_ENV_VAR"]

MISSING = _SpecialValue.MISSING
DELETED = _SpecialValue.DELETED
