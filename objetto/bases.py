# -*- coding: utf-8 -*-
"""Base classes for typing/type checking."""

from typing import TYPE_CHECKING

# bases
from ._bases import (
    final,
    Base,
    ProtectedBase,
    abstract_member,
    BaseHashable,
    BaseSized,
    BaseIterable,
    BaseContainer,
    BaseCollection,
    BaseProtectedCollection,
    BaseInteractiveCollection,
    BaseMutableCollection,
    BaseDict,
    BaseProtectedDict,
    BaseInteractiveDict,
    BaseMutableDict,
    BaseList,
    BaseProtectedList,
    BaseInteractiveList,
    BaseMutableList,
    BaseSet,
    BaseProtectedSet,
    BaseInteractiveSet,
    BaseMutableSet,
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
