# -*- coding: utf-8 -*-
"""Object changes."""

from typing import TYPE_CHECKING

from ._bases import final
from ._constants import INTEGER_TYPES, STRING_TYPES
from ._states import BaseState
from .data import (
    Data,
    data_attribute,
    data_constant_attribute,
    data_protected_dict_attribute,
    data_protected_list_attribute,
    data_protected_set_attribute,
)

if TYPE_CHECKING:
    from typing import Any, Callable, Final, Optional

    from ._data import DataAttribute, DictData, ListData, SetData
    from ._history import HistoryObject
    from ._objects import BaseObject

__all__ = [
    "BaseChange",
    "BaseAtomicChange",
    "Batch",
    "Update",
    "DictUpdate",
    "ListInsert",
    "ListDelete",
    "ListUpdate",
    "ListMove",
    "SetUpdate",
    "SetRemove",
]


class BaseChange(Data):
    """
    Base change.

    Inherits from:
      - :class:`objetto.data.Data`

    Inherited By:
      - :class:`objetto.bases.BaseAtomicChange`
      - :class:`objetto.changes.Batch`
    """

    name = data_attribute(
        STRING_TYPES, checked=False, abstracted=True
    )  # type: DataAttribute[str]
    """
    Name describing the change.

    :type: str
    """

    obj = data_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[BaseObject]]
    """
    Object being changed.

    :type: objetto.bases.BaseObject
    """

    is_atomic = data_constant_attribute(
        False, abstracted=True
    )  # type: DataAttribute[bool]
    """
    Whether change is atomic or not.

    :type: bool
    """


class BaseAtomicChange(BaseChange):
    """
    Base atomic change.

    Inherits from:
      - :class:`objetto.bases.BaseChange`

    Inherited By:
      - :class:`objetto.changes.Update`
      - :class:`objetto.changes.DictUpdate`
      - :class:`objetto.changes.ListInsert`
      - :class:`objetto.changes.ListDelete`
      - :class:`objetto.changes.ListUpdate`
      - :class:`objetto.changes.ListMove`
      - :class:`objetto.changes.SetUpdate`
      - :class:`objetto.changes.SetRemove`
    """

    __redo__ = data_attribute(
        finalized=True, compared=False, serialized=False, represented=False
    )  # type: Final[DataAttribute[Callable]]
    """Redo delegate."""

    __undo__ = data_attribute(
        finalized=True, compared=False, serialized=False, represented=False
    )  # type: Final[DataAttribute[Callable]]
    """Undo delegate."""

    old_state = data_attribute(
        BaseState, subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[BaseState]]
    """
    Object state before the change.

    :type: objetto.bases.BaseState
    """

    new_state = data_attribute(
        BaseState, subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[BaseState]]
    """
    Object state after the change.

    :type: objetto.bases.BaseState
    """

    old_children = data_protected_set_attribute(
        ".._objects|BaseObject",
        subtypes=True,
        checked=False,
        finalized=True,
    )  # type: Final[DataAttribute[SetData[BaseObject]]]
    """
    Children objects being released.

    :type: objetto.data.SetData[objetto.bases.BaseObject]
    """

    new_children = data_protected_set_attribute(
        ".._objects|BaseObject",
        subtypes=True,
        checked=False,
        finalized=True,
    )  # type: Final[DataAttribute[SetData[BaseObject]]]
    """
    Children objects being adopted.

    :type: objetto.data.SetData[objetto.bases.BaseObject]
    """

    history_adopters = data_protected_set_attribute(
        ".._objects|BaseObject",
        subtypes=True,
        checked=False,
        finalized=True,
    )  # type: Final[DataAttribute[SetData[BaseObject]]]
    """
    Objects adopting the history from the object being changed.

    :type: objetto.data.SetData[objetto.bases.BaseObject]
    """

    history = data_attribute(
        (".._history|HistoryObject", None),
        subtypes=False,
        checked=False,
        finalized=True,
        default=None,
    )  # type: Final[DataAttribute[Optional[HistoryObject]]]
    """
    History where this changed originated from (result of an redo/undo operation).

    :type: objetto.history.HistoryObject or None
    """

    is_atomic = data_constant_attribute(
        True, finalized=True
    )  # type: DataAttribute[bool]
    """
    Whether change is atomic or not.

    :type: bool
    """


@final
class Batch(BaseChange):
    """
    Batch change.

    Inherits from:
      - :class:`objetto.bases.BaseChange`
    """

    name = data_attribute(STRING_TYPES, checked=False)  # type: DataAttribute[str]
    """
    Name describing the change.

    :type: str
    """

    metadata = data_protected_dict_attribute(
        key_types=STRING_TYPES, checked=False
    )  # type: DataAttribute[DictData[str, Any]]
    """
    Metadata.

    :type: objetto.data.DictData[str, Any]
    """

    is_atomic = data_constant_attribute(
        False, finalized=True
    )  # type: DataAttribute[bool]
    """
    Whether change is atomic or not.

    :type: bool
    """


@final
class Update(BaseAtomicChange):
    """
    Object's attributes have been updated.

    Inherits from:
      - :class:`objetto.bases.BaseAtomicChange`
    """

    name = data_attribute(
        STRING_TYPES, checked=False, default="Update Attributes"
    )  # type: DataAttribute[str]
    """
    Name describing the change.

    :type: str
    """

    old_values = data_protected_dict_attribute(
        checked=False, key_types=STRING_TYPES
    )  # type: DataAttribute[DictData[str, Any]]
    """
    Old attribute values.

    :type: objetto.data.DictData[str, Any]
    """

    new_values = data_protected_dict_attribute(
        checked=False, key_types=STRING_TYPES
    )  # type: DataAttribute[DictData[str, Any]]
    """
    New attribute values.

    :type: objetto.data.DictData[str, Any]
    """


@final
class DictUpdate(BaseAtomicChange):
    """
    Dictionary values have been updated.

    Inherits from:
      - :class:`objetto.bases.BaseAtomicChange`
    """

    name = data_attribute(
        STRING_TYPES, checked=False, default="Update Values"
    )  # type: DataAttribute[str]
    """
    Name describing the change.
    """

    old_values = data_protected_dict_attribute(
        checked=False
    )  # type: DataAttribute[DictData[Any, Any]]
    """
    Old values.

    :type: objetto.data.DictData[collections.abc.Hashable, Any]
    """

    new_values = data_protected_dict_attribute(
        checked=False
    )  # type: DataAttribute[DictData[Any, Any]]
    """
    New values.

    :type: objetto.data.DictData[collections.abc.Hashable, Any]
    """


@final
class ListInsert(BaseAtomicChange):
    """
    Values have been inserted into the list.

    Inherits from:
      - :class:`objetto.bases.BaseAtomicChange`
    """

    name = data_attribute(
        STRING_TYPES, checked=False, default="Insert Values"
    )  # type: DataAttribute[str]
    """
    Name describing the change.

    :type: str
    """

    index = data_attribute(INTEGER_TYPES, checked=False)  # type: DataAttribute[int]
    """
    Insertion index.

    :type: int
    """

    last_index = data_attribute(
        INTEGER_TYPES, checked=False
    )  # type: DataAttribute[int]
    """
    Last inserted value index.

    :type: int
    """

    stop = data_attribute(INTEGER_TYPES, checked=False)  # type: DataAttribute[int]
    """
    Stop index.

    :type: int
    """

    new_values = data_protected_list_attribute(
        checked=False,
    )  # type: DataAttribute[ListData[Any]]
    """
    New values.

    :type: objetto.data.ListData[Any]
    """


@final
class ListDelete(BaseAtomicChange):
    """
    Values have been removed from the list.

    Inherits from:
      - :class:`objetto.bases.BaseAtomicChange`
    """

    name = data_attribute(
        STRING_TYPES, checked=False, default="Remove Values"
    )  # type: DataAttribute[str]
    """
    Name describing the change.

    :type: str
    """

    index = data_attribute(INTEGER_TYPES, checked=False)  # type: DataAttribute[int]
    """
    First removed value index.

    :type: int
    """

    last_index = data_attribute(
        INTEGER_TYPES, checked=False
    )  # type: DataAttribute[int]
    """
    Last removed value index.

    :type: int
    """

    stop = data_attribute(INTEGER_TYPES, checked=False)  # type: DataAttribute[int]
    """
    Stop index.

    :type: int
    """

    old_values = data_protected_list_attribute(
        checked=False,
    )  # type: DataAttribute[ListData[Any]]
    """
    Old values.

    :type: objetto.data.ListData[Any]
    """


@final
class ListUpdate(BaseAtomicChange):
    """
    List values have been updated.

    Inherits from:
      - :class:`objetto.bases.BaseAtomicChange`
    """

    name = data_attribute(
        STRING_TYPES, checked=False, default="Update values"
    )  # type: DataAttribute[str]
    """
    Name describing the change.

    :type: str
    """

    index = data_attribute(INTEGER_TYPES, checked=False)  # type: DataAttribute[int]
    """
    First updated value index.

    :type: int
    """

    last_index = data_attribute(
        INTEGER_TYPES, checked=False
    )  # type: DataAttribute[int]
    """
    Last updated value index.

    :type: int
    """

    stop = data_attribute(INTEGER_TYPES, checked=False)  # type: DataAttribute[int]
    """
    Stop index.

    :type: int
    """

    old_values = data_protected_list_attribute(
        checked=False,
    )  # type: DataAttribute[ListData[Any]]
    """
    Old values.

    :type: objetto.data.ListData[Any]
    """

    new_values = data_protected_list_attribute(
        checked=False,
    )  # type: DataAttribute[ListData[Any]]
    """
    New values.

    :type: objetto.data.ListData[Any]
    """


@final
class ListMove(BaseAtomicChange):
    """
    List values have been moved internally.

    Inherits from:
      - :class:`objetto.bases.BaseAtomicChange`
    """

    name = data_attribute(
        STRING_TYPES, checked=False, default="Move values"
    )  # type: DataAttribute[str]
    """
    Name describing the change.

    :type: str
    """

    index = data_attribute(INTEGER_TYPES, checked=False)  # type: DataAttribute[int]
    """
    First moved value index.

    :type: int
    """

    last_index = data_attribute(
        INTEGER_TYPES, checked=False
    )  # type: DataAttribute[int]
    """
    Last moved value index.

    :type: int
    """

    stop = data_attribute(INTEGER_TYPES, checked=False)  # type: DataAttribute[int]
    """
    Stop index.

    :type: int
    """

    target_index = data_attribute(
        INTEGER_TYPES, checked=False
    )  # type: DataAttribute[int]
    """
    Index where values are being moved to.

    :type: int
    """

    post_index = data_attribute(
        INTEGER_TYPES, checked=False
    )  # type: DataAttribute[int]
    """
    First moved value index after the move.

    :type: int
    """

    post_last_index = data_attribute(
        INTEGER_TYPES, checked=False
    )  # type: DataAttribute[int]
    """
    Last moved value index after the move.

    :type: int
    """

    post_stop = data_attribute(INTEGER_TYPES, checked=False)  # type: DataAttribute[int]
    """
    Stop index after the move.

    :type: int
    """

    values = data_protected_list_attribute(
        checked=False,
    )  # type: DataAttribute[ListData[Any]]
    """
    Values being moved.

    :type: objetto.data.ListData[Any]
    """


@final
class SetUpdate(BaseAtomicChange):
    """
    Values have been added to the set.

    Inherits from:
      - :class:`objetto.bases.BaseAtomicChange`
    """

    name = data_attribute(
        STRING_TYPES, checked=False, default="Add values"
    )  # type: DataAttribute[str]
    """
    Name describing the change.

    :type: str
    """

    new_values = data_protected_set_attribute(
        checked=False
    )  # type: DataAttribute[SetData[Any]]
    """
    Values being added to the set.

    :type: objetto.data.SetData[collections.abc.Hashable]
    """


@final
class SetRemove(BaseAtomicChange):
    """
    Values have been removed from the set.

    Inherits from:
      - :class:`objetto.bases.BaseAtomicChange`
    """

    name = data_attribute(
        STRING_TYPES, checked=False, default="Remove values"
    )  # type: DataAttribute[str]
    """
    Name describing the change.

    :type: str
    """

    old_values = data_protected_set_attribute(
        checked=False
    )  # type: DataAttribute[SetData[Any]]
    """
    Values being removed from the set.

    :type: objetto.data.SetData[collections.abc.Hashable]
    """
