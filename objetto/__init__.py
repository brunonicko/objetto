# -*- coding: utf-8 -*-

from .applications import Application
from .objects import (
    Object,
    data_relationship,
    data_method,
    attribute,
    dict_attribute,
    dict_cls,
)

__all__ = [
    "Application",
    "Object",
    "data_relationship",
    "data_method",
    "attribute",
    "dict_attribute",
    "dict_cls",
]
