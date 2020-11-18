# -*- coding: utf-8 -*-
"""Mutable structures coordinated by an application."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, cast, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, iterkeys, itervalues, string_types, with_metaclass

from ._bases import final, init_context
from ._states import DictState, ListState, SetState
from ._structures import (
    MISSING,
    BaseAttribute,
    BaseAttributeMeta,
    BaseAttributeStructure,
    BaseAttributeStructureMeta,
    BaseAuxiliaryStructure,
    BaseAuxiliaryStructureMeta,
    BaseDictStructure,
    BaseDictStructureMeta,
    BaseMutableAttributeStructure,
    BaseMutableAuxiliaryStructure,
    BaseMutableDictStructure,
    BaseMutableListStructure,
    BaseMutableSetStructure,
    BaseMutableStructure,
    BaseListStructure,
    BaseListStructureMeta,
    BaseRelationship,
    BaseSetStructure,
    BaseSetStructureMeta,
    BaseStructure,
    BaseStructureMeta,
    KeyRelationship,
)
from .utils.custom_repr import custom_iterable_repr, custom_mapping_repr
from .utils.type_checking import assert_is_instance

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        ItemsView,
        Iterable,
        Iterator,
        KeysView,
        List,
        Mapping,
        Optional,
        Set,
        Tuple,
        Type,
        Union,
        ValuesView,
    )

    from .utils.factoring import LazyFactory
    from .utils.type_checking import LazyTypes

__all__ = []


T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.

