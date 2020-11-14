# -*- coding: utf-8 -*-
"""Base classes for typing/type checking."""

from typing import TYPE_CHECKING

# bases
from ._bases import (
    Base,
    BaseCollection,
    BaseContainer,
    BaseDict,
    BaseHashable,
    BaseInteractiveCollection,
    BaseInteractiveDict,
    BaseInteractiveList,
    BaseInteractiveSet,
    BaseIterable,
    BaseList,
    BaseMutableCollection,
    BaseMutableDict,
    BaseMutableList,
    BaseMutableSet,
    BaseProtectedCollection,
    BaseProtectedDict,
    BaseProtectedList,
    BaseProtectedSet,
    BaseSet,
    BaseSized,
    ProtectedBase,
    abstract_member,
    final,
)

if TYPE_CHECKING:
    from ._bases import AbstractType
else:
    AbstractType = None

# states
from ._states import BaseState

__all__ = [
    "AbstractType",
    "final",
    "Base",
    "ProtectedBase",
    "abstract_member",
    "BaseHashable",
    "BaseSized",
    "BaseIterable",
    "BaseContainer",
    "BaseCollection",
    "BaseProtectedCollection",
    "BaseInteractiveCollection",
    "BaseMutableCollection",
    "BaseDict",
    "BaseProtectedDict",
    "BaseInteractiveDict",
    "BaseMutableDict",
    "BaseList",
    "BaseProtectedList",
    "BaseInteractiveList",
    "BaseMutableList",
    "BaseSet",
    "BaseProtectedSet",
    "BaseInteractiveSet",
    "BaseMutableSet",
    "BaseState",
]
