# -*- coding: utf-8 -*-
"""Constants."""

from six import integer_types, string_types, text_type

__all__ = [
    "TEXT_TYPE",
    "BASE_STRING_TYPES",
    "STRING_TYPES",
    "INTEGER_TYPES",
]


TEXT_TYPE = text_type
"""
Text type.

:type: type
"""

BASE_STRING_TYPES = string_types
"""
Base string types.

:type: tuple[type]
"""

STRING_TYPES = tuple({str, TEXT_TYPE})
"""
All string types.

:type: tuple[type]
"""

INTEGER_TYPES = integer_types
"""
Integer type.

:type: tuple[type]
"""
