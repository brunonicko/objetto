# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING, overload

import attr

if TYPE_CHECKING:
    from typing import Any, Optional, Callable, Type, Tuple

    from pyrsistent.typing import PMap

    from ._structures import Action
    from ._constants import Phase
    from ._objects import AbstractObject, AbstractHistoryObject

__all__ = [
    "ReactionDescriptor",
    "HistoryDescriptor",
]


@attr.s(frozen=True)
class ReactionDescriptor(object):
    func = attr.ib()  # type: Callable[[AbstractObject, Action, Phase], None]
    priority = attr.ib()  # type: Optional[int]

    @overload
    def __get__(self, instance, owner):
        # type: (None, Type[AbstractObject]) -> ReactionDescriptor
        pass

    @overload
    def __get__(
        self,
        instance,  # type: AbstractObject
        owner,  # type: Type[AbstractObject]
    ):
        # type: (...) -> Callable[[Action, Phase], None]
        pass

    def __get__(self, instance, owner):
        if instance is None:
            if owner is None:
                return self
            else:
                return self.func
        else:
            return lambda action, phase: self.func(instance, action, phase)


@attr.s(frozen=True)
class HistoryDescriptor(object):
    type = attr.ib()  # type: Type[AbstractHistoryObject]
    args = attr.ib()  # type: Tuple[Any, ...]
    kwargs = attr.ib()  # type: PMap[str, Any]

    @overload
    def __get__(self, instance, owner):
        # type: (None, Type[AbstractObject]) -> HistoryDescriptor
        pass

    @overload
    def __get__(
        self,
        instance,  # type: AbstractObject
        owner,  # type: Type[AbstractObject]
    ):
        # type: (...) -> Optional[AbstractHistoryObject]
        pass

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return instance._get_history()
