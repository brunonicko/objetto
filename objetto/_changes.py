# -*- coding: utf-8 -*-
"""Object changes."""

from typing import TYPE_CHECKING

from six import integer_types, string_types

from ._bases import final
from ._states import BaseState
from .data import (
    Data,
    data_attribute,
    data_dict_attribute,
    data_list_attribute,
    data_set_attribute,
)

if TYPE_CHECKING:
    from typing import Any, Callable, Final

    from ._data import (
        DataAttribute,
        InteractiveDictData,
        InteractiveListData,
        InteractiveSetData,
    )
    from ._objects import BaseObject

__all__ = [
    "BaseChange",
    "Batch",
    "BaseAtomicChange",
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
    """Base change."""

    name = data_attribute(
        string_types, checked=False, abstracted=True
    )  # type: DataAttribute[str]
    """Name describing the change."""

    obj = data_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[BaseObject]]
    """Object being changed."""


@final
class Batch(BaseChange):
    """Batch change."""

    name = data_attribute(
        string_types, checked=False, abstracted=True
    )  # type: DataAttribute[str]
    """Name describing the change."""

    metadata = data_dict_attribute(
        key_types=string_types, key_checked=False
    )  # type: DataAttribute[InteractiveDictData[str, Any]]
    """Metadata."""


class BaseAtomicChange(BaseChange):
    """Base atomic object change."""

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
    """Object state before the change."""

    new_state = data_attribute(
        BaseState, subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[BaseState]]
    """Object state after the change."""

    old_children = data_set_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[InteractiveSetData[BaseObject]]]
    """Children objects being released."""

    new_children = data_set_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[InteractiveSetData[BaseObject]]]
    """Children objects being adopted."""

    history_adopters = data_set_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[InteractiveSetData[BaseObject]]]
    """Objects adopting the history from the object being changed."""


@final
class Update(BaseAtomicChange):
    """Object's attributes have been updated."""

    name = data_attribute(
        string_types, checked=False, default="Update Attributes"
    )  # type: DataAttribute[str]
    """Name describing the change."""

    old_values = data_dict_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveDictData[str, Any]]
    """Old attribute values."""

    new_values = data_dict_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveDictData[str, Any]]
    """New attribute values."""


@final
class DictUpdate(BaseAtomicChange):
    """Dictionary values have been updated."""

    name = data_attribute(
        string_types, checked=False, default="Update Values"
    )  # type: DataAttribute[str]
    """Name describing the change."""

    old_values = data_dict_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveDictData[str, Any]]
    """Old values."""

    new_values = data_dict_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveDictData[str, Any]]
    """New values."""


@final
class ListInsert(BaseAtomicChange):
    """Values have been inserted into the list."""

    name = data_attribute(
        string_types, checked=False, default="Insert Values"
    )  # type: DataAttribute[str]
    """Name describing the change."""

    index = data_attribute(integer_types, checked=False)  # type: DataAttribute[int]
    """Insertion index."""

    last_index = data_attribute(
        integer_types, checked=False
    )  # type: DataAttribute[int]
    """Last inserted value index."""

    stop = data_attribute(integer_types, checked=False)  # type: DataAttribute[int]
    """Stop index."""

    new_values = data_list_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveListData[Any]]
    """New values."""


@final
class ListDelete(BaseAtomicChange):
    """Values have been removed from the list."""

    name = data_attribute(
        string_types, checked=False, default="Remove Values"
    )  # type: DataAttribute[str]
    """Name describing the change."""

    index = data_attribute(integer_types, checked=False)  # type: DataAttribute[int]
    """First removed value index."""

    last_index = data_attribute(
        integer_types, checked=False
    )  # type: DataAttribute[int]
    """Last removed value index."""

    stop = data_attribute(integer_types, checked=False)  # type: DataAttribute[int]
    """Stop index."""

    old_values = data_list_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveListData[Any]]
    """Old values."""


@final
class ListUpdate(BaseAtomicChange):
    """List values have been updated."""

    name = data_attribute(
        string_types, checked=False, default="Update values"
    )  # type: DataAttribute[str]
    """Name describing the change."""

    index = data_attribute(integer_types, checked=False)  # type: DataAttribute[int]
    """First updated value index."""

    last_index = data_attribute(
        integer_types, checked=False
    )  # type: DataAttribute[int]
    """Last updated value index."""

    stop = data_attribute(integer_types, checked=False)  # type: DataAttribute[int]
    """Stop index."""

    old_values = data_list_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveListData[Any]]
    """Old values."""

    new_values = data_list_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveListData[Any]]
    """New values."""


@final
class ListMove(BaseAtomicChange):
    """List values have been moved internally."""

    name = data_attribute(
        string_types, checked=False, default="Move values"
    )  # type: DataAttribute[str]
    """Name describing the change."""

    index = data_attribute(integer_types, checked=False)  # type: DataAttribute[int]
    """First moved value index."""

    last_index = data_attribute(
        integer_types, checked=False
    )  # type: DataAttribute[int]
    """Last moved value index."""

    stop = data_attribute(integer_types, checked=False)  # type: DataAttribute[int]
    """Stop index."""

    target_index = data_attribute(
        integer_types, checked=False
    )  # type: DataAttribute[int]
    """Index where values are being moved to."""

    post_index = data_attribute(
        integer_types, checked=False
    )  # type: DataAttribute[int]
    """First moved value index after the move."""

    post_last_index = data_attribute(
        integer_types, checked=False
    )  # type: DataAttribute[int]
    """Last moved value index after the move."""

    post_stop = data_attribute(integer_types, checked=False)  # type: DataAttribute[int]
    """Stop index after the move."""

    values = data_list_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveListData[Any]]
    """Values being moved."""


@final
class SetUpdate(BaseAtomicChange):
    """Values have been added to the set."""

    name = data_attribute(
        string_types, checked=False, default="Add values"
    )  # type: DataAttribute[str]
    """Name describing the change."""

    new_values = data_set_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveSetData[Any]]
    """Values being added to the set."""


@final
class SetRemove(BaseAtomicChange):
    """Values have been removed from the set."""

    name = data_attribute(
        string_types, checked=False, default="Remove values"
    )  # type: DataAttribute[str]
    """Name describing the change."""

    old_values = data_set_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveSetData[Any]]
    """Values being removed from the set."""
