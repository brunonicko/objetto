# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING, overload

import attr

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
    "InitializedChange",
    "StateChange",
    "BatchChange",
    "FrozenChange",
    "Action",
    "Store",
    "Commit",
    "Snapshot",
]


@attr.s(frozen=True)
class ObserverError(object):
    exception_info = attr.ib()  # type: ObserverExceptionInfo
    action = attr.ib()  # type: Action
    phase = attr.ib()  # type: Phase


@attr.s(frozen=True)
class Relationship(object):
    historied = attr.ib()  # type: bool
    serialized = attr.ib()  # type: bool


@attr.s(frozen=True)
class State(object):
    data = attr.ib()  # type: Any
    metadata = attr.ib()  # type: Any
    children_pointers = attr.ib()  # type: PMap[Pointer[AbstractObject], Relationship]


@attr.s(frozen=True)
class AbstractChange(object):
    pass


@attr.s(frozen=True)
class InitializedChange(AbstractChange):
    state = attr.ib()  # type: State


@attr.s(frozen=True)
class StateChange(AbstractChange):
    event = attr.ib()  # type: Any
    undo_event = attr.ib()  # type: Any
    old_state = attr.ib()  # type: State
    new_state = attr.ib()  # type: State
    adoption_pointers = attr.ib()  # type: PSet[Pointer[AbstractObject]]
    release_pointers = attr.ib()  # type: PSet[Pointer[AbstractObject]]


@attr.s(frozen=True)
class BatchChange(AbstractChange):
    name = attr.ib()  # type: str
    kwargs = attr.ib()  # type: PMap[str, Any]


@attr.s(frozen=True)
class FrozenChange(AbstractChange):
    objects = attr.ib()  # type: Tuple[AbstractObject, ...]


@attr.s(frozen=True)
class Action(object):
    uuid = attr.ib()  # type: UUID
    app = attr.ib()  # type: Application
    sender = attr.ib()  # type: Optional[AbstractObject]
    source = attr.ib()  # type: AbstractObject
    change = attr.ib()  # type: AbstractChange
    locations = attr.ib()  # type: Tuple[Hashable, ...]


@attr.s(frozen=True)
class Store(object):
    state = attr.ib()  # type: State
    parent_ref = attr.ib()  # type: Optional[ReferenceType[AbstractObject]]
    history_provider_ref = attr.ib()  # type: Optional[ReferenceType[AbstractObject]]
    last_parent_history_ref = attr.ib(

    )  # type: Optional[ReferenceType[AbstractHistoryObject]]
    history = attr.ib()  # type: Optional[AbstractHistoryObject]
    frozen = attr.ib()  # type: bool


@attr.s(frozen=True)
class Commit(object):
    storage = attr.ib()  # type: Storage[Pointer[AbstractObject], Store]
    action = attr.ib()  # type: Action
    phase = attr.ib()  # type: Phase


@attr.s(frozen=True)
class Snapshot(object):
    storage = attr.ib()  # type: Storage[Pointer[AbstractObject], Store]
