# -*- coding: utf-8 -*-
"""Object changes."""

from typing import TYPE_CHECKING

from six import string_types

from ._bases import final
from ._states import BaseState
from .data import Data, SetData, data_attribute, data_dict_attribute, data_set_attribute

if TYPE_CHECKING:
    from typing import Any, Callable, Final

    from ._data import DataAttribute, InteractiveDictData
    from ._objects import BaseObject

__all__ = ["BaseChange", "Batch", "BaseAtomicChange", "ObjectUpdate"]


class BaseChange(Data):
    name = data_attribute(
        string_types, checked=False, abstracted=True
    )  # type: DataAttribute[str]

    obj = data_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[BaseObject]]


@final
class Batch(BaseChange):
    name = data_attribute(
        string_types, checked=False, abstracted=True
    )  # type: DataAttribute[str]

    metadata = data_dict_attribute(
        key_types=string_types, key_checked=False
    )  # type: DataAttribute[InteractiveDictData[str, Any]]


class BaseAtomicChange(BaseChange):
    __redo__ = data_attribute(
        finalized=True, compared=False, serialized=False, represented=False
    )  # type: Final[DataAttribute[Callable]]

    __undo__ = data_attribute(
        finalized=True, compared=False, serialized=False, represented=False
    )  # type: Final[DataAttribute[Callable]]

    old_state = data_attribute(
        BaseState, subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[BaseState]]

    new_state = data_attribute(
        BaseState, subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[BaseState]]

    old_children = data_set_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[SetData[BaseObject]]]

    new_children = data_set_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[SetData[BaseObject]]]

    history_adopters = data_set_attribute(
        ".._objects|BaseObject", subtypes=True, checked=False, finalized=True
    )  # type: Final[DataAttribute[SetData[BaseObject]]]


@final
class ObjectUpdate(BaseAtomicChange):
    name = data_attribute(
        string_types, checked=False, default="Update Attributes"
    )  # type: DataAttribute[str]

    old_values = data_dict_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveDictData[str, Any]]

    new_values = data_dict_attribute(
        checked=False
    )  # type: DataAttribute[InteractiveDictData[str, Any]]
