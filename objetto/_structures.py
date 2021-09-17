# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING

from pyrsistent import PClass, field

if TYPE_CHECKING:
    from uuid import UUID
    from weakref import ReferenceType
    from typing import Any, Optional, Tuple, Hashable

    from pyrsistent.typing import PMap, PSet

    from .utils.pointer import Pointer
    from .utils.storage import Storage
    from .utils.subject_observer import ObserverExceptionInfo
    from ._application import Application
    from ._constants import Phase
    from ._objects import AbstractObject, AbstractHistoryObject

__all__ = [
    "ObserverError",
    "Relationship",
    "State",
    "AbstractChange",
    "InitializedChange",
    "StateChange",
    "BatchChange",
    "Action",
    "AbstractStore",
    "FrozenStore",
    "Store",
    "Commit",
    "Snapshot",
]


class ObserverError(PClass):
    exception_info = field(mandatory=True)  # type: ObserverExceptionInfo
    action = field(mandatory=True)  # type: Action
    phase = field(mandatory=True)  # type: Phase


class Relationship(PClass):
    historical = field(mandatory=True)  # type: bool
    serializable = field(mandatory=True)  # type: bool
    freezable = field(mandatory=True)  # type: bool


class State(PClass):
    data = field(mandatory=True)  # type: Any
    metadata = field(mandatory=True)  # type: Any
    children_pointers = field(
        mandatory=True
    )  # type: PMap[Pointer[AbstractObject], Relationship]


class AbstractChange(PClass):
    pass


class InitializedChange(AbstractChange):
    state = field(mandatory=True)  # type: State


class StateChange(AbstractChange):
    event = field(mandatory=True)  # type: Any
    undo_event = field(mandatory=True)  # type: Any
    old_state = field(mandatory=True)  # type: State
    new_state = field(mandatory=True)  # type: State
    adoption_pointers = field(mandatory=True)  # type: PSet[Pointer[AbstractObject]]
    release_pointers = field(mandatory=True)  # type: PSet[Pointer[AbstractObject]]


class BatchChange(AbstractChange):
    name = field(mandatory=True)  # type: str
    kwargs = field(mandatory=True)  # type: PMap[str, Any]


class Action(PClass):
    uuid = field(mandatory=True)  # type: UUID
    app = field(mandatory=True)  # type: Application
    sender = field(mandatory=True)  # type: Optional[AbstractObject]
    source = field(mandatory=True)  # type: AbstractObject
    change = field(mandatory=True)  # type: AbstractChange
    locations = field(mandatory=True)  # type: Tuple[Hashable, ...]


class AbstractStore(PClass):
    state = field(mandatory=True)  # type: State
    parent_ref = field(mandatory=True)  # type: Optional[ReferenceType[AbstractObject]]


class FrozenStore(AbstractStore):
    pass


class Store(AbstractStore):
    history_provider_ref = field(
        mandatory=True
    )  # type: Optional[ReferenceType[AbstractObject]]
    last_parent_history_ref = field(
        mandatory=True
    )  # type: Optional[ReferenceType[AbstractHistoryObject]]
    history = field(mandatory=True)  # type: Optional[AbstractHistoryObject]


class Commit(PClass):
    storage = field(mandatory=True)  # type: Storage[Pointer[AbstractObject], Store]
    action = field(mandatory=True)  # type: Action
    phase = field(mandatory=True)  # type: Phase


class Snapshot(PClass):
    storage = field(mandatory=True)  # type: Storage[Pointer[AbstractObject], Store]
