from typing import TYPE_CHECKING, overload

from pyrsistent import PClass, field

if TYPE_CHECKING:
    from typing import Any, Optional, Callable, Type, Tuple

    from pyrsistent.typing import PMap

    from ._structures import Action
    from ._constants import Phase
    from ._objects import AbstractObject, AbstractHistoryObject

__all__ = [
    "ReactionDescriptor",
    "HistoryDescriptor",
    "HashDescriptor",
]


class ReactionDescriptor(PClass):
    func = field(
        mandatory=True
    )  # type: Callable[[AbstractObject, Action, Phase], None]
    priority = field(mandatory=True)  # type: Optional[int]

    @overload
    def __get__(
        self,
        instance,  # type: None
        owner,  # type: Type[AbstractObject]
    ):
        # type: (...) -> Callable[[AbstractObject, Action, Phase], None]
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
            return self.func
        else:
            return lambda action, phase: self.func(instance, action, phase)


class HistoryDescriptor(PClass):
    type = field(mandatory=True)  # type: Type[AbstractHistoryObject]
    args = field(mandatory=True)  # type: Tuple[Any, ...]
    kwargs = field(mandatory=True)  # type: PMap[str, Any]

    @overload
    def __get__(self, instance, owner):
        # type: (None, Optional[Type[AbstractObject]]) -> HistoryDescriptor
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


class HashDescriptor(PClass):

    @overload
    def __get__(self, instance, owner):
        # type: (None, Type[AbstractObject]) -> None
        pass

    @overload
    def __get__(
        self,
        instance,  # type: AbstractObject
        owner,  # type: Type[AbstractObject]
    ):
        # type: (...) -> Optional[Callable[[], int]]
        pass

    def __get__(self, instance, owner):
        if instance is None or not instance._is_frozen:
            return None
        else:
            return lambda: instance._get_hash()
