# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING

from ._bases import final
from ._changes import BaseAtomicChange, Batch
from .factories import Integer
from .objects import (
    Object,
    attribute,
    protected_attribute_pair,
    protected_list_attribute_pair,
)

if TYPE_CHECKING:
    from typing import Any, Union, TypeVar, Optional

    from ._objects import (
        Attribute,
        ProxyListObject,
        ListObject,
        DictObject,
        MutableDictObject,
        MutableListObject,
        MutableSetObject,
        Object,
        ProxyDictObject,
        ProxySetObject,
        SetObject,
    )

    T = TypeVar("T")  # Any type.
    KT = TypeVar("KT")  # Any key type.
    VT = TypeVar("VT")  # Any value type.

    MDA = Attribute[MutableDictObject[KT, VT]]
    MLA = Attribute[MutableListObject[T]]
    MSA = Attribute[MutableSetObject[T]]
    DA = Attribute[DictObject[KT, VT]]
    LA = Attribute[ListObject[T]]
    SA = Attribute[SetObject[T]]
    PDA = Attribute[ProxyDictObject[KT, VT]]
    PLA = Attribute[ProxyListObject[T]]
    PSA = Attribute[ProxySetObject[T]]
    CT = Union[BaseAtomicChange, "BatchChanges"]

__all__ = ["HistoryObject"]


class HistoryError(Exception):
    pass


# noinspection PyAbstractClass
@final
class BatchChanges(Object):
    """Batch changes."""

    __slots__ = ()

    change = attribute(
        Batch, subtypes=True, child=False, changeable=False, checked=False
    )  # type: Attribute[Batch]
    """Batch change with name and metadata."""

    name = attribute(
        str, child=False, checked=False, changeable=False
    )  # type: Attribute[str]
    """The batch change name."""

    _changes, changes = protected_list_attribute_pair(
        (BaseAtomicChange, "BatchChanges"), subtypes=True, data=False, checked=False
    )  # type: PLA[CT], LA[CT]
    """Changes executed during the batch."""

    _closed, closed = protected_attribute_pair(
        bool, default=False, child=False, checked=False
    )  # type: Attribute[bool], Attribute[bool]
    """Whether the batch has already completed or is still running."""

    def format_changes(self):
        # type: () -> str
        """
        Format changes into readable string.

        :return: Formatted changes.
        """
        with self.app.read_context():
            parts = []
            for change in self.changes:
                if isinstance(change, BatchChanges):
                    parts.append(
                        "{} (Batch) ({})".format(
                            change.name, type(change.change.obj).__name__
                        )
                    )
                    for part in change.format_changes().split("\n"):
                        parts.append("  {}".format(part))
                else:
                    parts.append(
                        "{} ({})".format(change.name, type(change.obj).__name__)
                    )
            return "\n".join(parts)

    def __undo__(self, _):
        # type: (Any) -> None
        """Undo."""
        for change in reversed(self.changes):
            change.__undo__(change)

    def __redo__(self, _):
        # type: (Any) -> None
        """Redo."""
        for change in self.changes:
            change.__redo__(change)


# noinspection PyAbstractClass
@final
class HistoryObject(Object):
    """History object."""

    __slots__ = ()

    size = attribute(
        (int, type(None)),
        default=None,
        factory=Integer(minimum=0, accepts_none=True),
        changeable=False,
        child=False,
    )  # type: Attribute[int]
    """How many changes to remember."""

    __executing, executing = protected_attribute_pair(
        bool, default=False, child=False
    )  # type: Attribute[bool], Attribute[bool]
    """Whether the history is undoing or redoing."""

    __undoing, undoing = protected_attribute_pair(
        bool, default=False, child=False
    )  # type: Attribute[bool], Attribute[bool]
    """Whether the history is undoing."""

    __redoing, redoing = protected_attribute_pair(
        bool, default=False, child=False
    )  # type: Attribute[bool], Attribute[bool]
    """Whether the history is redoing."""

    __index, index = protected_attribute_pair(
        int, default=0, child=False
    )  # type: Attribute[int], Attribute[int]
    """The index of the current change."""

    __changes, changes = protected_list_attribute_pair(
        (BaseAtomicChange, BatchChanges, type(None)),
        subtypes=True,
        default=(None,),
        data=False,
    )  # type: PLA[Optional[CT]], LA[Optional[CT]]
    """List of changes."""

    def set_index(self, index):
        # type: (int) -> None
        """
        Undo/redo until we reach the desired index.

        :param index: Index.
        """
        with self.app.write_context():
            if 0 <= index < len(self.changes) - 1:
                if index > self.__index:
                    with self._batch_context("Multiple Redo"):
                        while index > self.__index:
                            self.redo()
                elif index < self.__index:
                    with self._batch_context("Multiple Undo"):
                        while index < self.__index:
                            self.undo()
                else:
                    return
            raise IndexError(index)

    def undo_all(self):
        # type: () -> None
        """Undo all."""
        with self.app.write_context():
            with self._batch_context("Undo All"):
                while self.__index > 0:
                    self.undo()

    def redo_all(self):
        # type: () -> None
        """Redo all."""
        with self.app.write_context():
            with self._batch_context("Redo All"):
                while self.__index < len(self.changes) - 1:
                    self.redo()

    def redo(self):
        # type: () -> None
        """Redo."""
        with self.app.write_context():
            if self.__executing:
                error = "can't redo while executing"
                raise HistoryError(error)
            if self.__index < len(self.changes) - 1:
                change = self.changes[self.__index + 1]
                assert change is not None
                with self._batch_context("Redo", change=change):
                    self.__executing = True
                    self.__redoing = True
                    try:
                        change.__redo__(change)
                    finally:
                        self.__executing = False
                        self.__redoing = False
                    self.__index += 1
            else:
                error = "can't redo any further"
                raise HistoryError(error)

    def undo(self):
        # type: () -> None
        """Undo."""
        with self.app.write_context():
            if self.__executing:
                error = "can't undo while executing"
                raise HistoryError(error)

            if self.__index > 0:
                change = self.changes[self.index]
                assert change is not None
                with self._batch_context("Undo", change=change):
                    self.__executing = True
                    self.__undoing = True
                    try:
                        change.__undo__(change)
                    finally:
                        self.__executing = False
                        self.__undoing = False
                    self.__index -= 1
            else:
                error = "can't undo any further"
                raise HistoryError(error)

    def flush(self):
        # type: () -> None
        """
        Flush all changes.

        :raises HistoryError: Can't flush while executing.
        """
        with self.app.write_context():
            if self.__executing:
                error = "can't flush history while executing"
                raise HistoryError(error)
            if len(self.changes) > 1:
                with self._batch_context("Flush"):
                    self.__index = 0
                    del self.__changes[1:]

    def flush_redo(self):
        # type: () -> None
        """
        Flush changes ahead of the current index.

        :raises HistoryError: Can't flush while executing.
        """
        with self.app.write_context():
            if self.__executing:
                error = "can't flush history while executing"
                raise HistoryError(error)
            if len(self.changes) > 1:
                if self.__index < len(self.changes) - 1:
                    with self._batch_context("Flush Redo"):
                        del self.__changes[self.__index + 1 :]

    def in_batch(self):
        # type: () -> bool
        """
        Get whether history is currently in an open batch.

        :return: True if currently in an open batch.
        :raises HistoryError: Can't check while executing.
        """
        with self.app.read_context():
            if self.__executing:
                error = "can't check if in a batch while executing"
                raise HistoryError(error)
            return bool(
                len(self.changes) > 1
                and isinstance(self.changes[-1], BatchChanges)
                and not self.changes[-1].closed
            )

    def format_changes(self):
        # type: () -> str
        """
        Format changes into readable string.

        :return: Formatted changes.
        """
        with self.app.read_context():
            parts = ["--- <-" if self.index == 0 else "---"]
            for i, change in enumerate(self.changes):
                if i == 0:
                    continue
                if isinstance(change, BatchChanges):
                    parts.append(
                        "{} (Batch) ({}) <-".format(
                            change.name, type(change.change.obj).__name__
                        )
                        if self.index == i
                        else "{} (Batch) ({})".format(
                            change.name, type(change.change.obj).__name__
                        )
                    )
                    for part in change.format_changes().split("\n"):
                        parts.append("  {}".format(part))
                else:
                    parts.append(
                        "{} ({}) <-".format(change.name, type(change.obj).__name__)
                        if self.index == i
                        else "{} ({})".format(change.name, type(change.obj).__name__)
                    )
            return "\n".join(parts)

    def __enter_batch__(self, batch):
        # type: (Batch) -> None
        """
        Enter batch context.

        :param batch: Batch.
        """
        with self.app.write_context():
            if self.__executing:
                return
            with self._batch_context("Enter Batch", batch=batch):
                self.flush_redo()
                changes = self.__changes
                while changes and isinstance(changes[-1], BatchChanges):
                    if changes[-1].closed:
                        break
                    changes = changes[-1]._changes
                changes.append(BatchChanges(self.app, change=batch, name=batch.name))
                if changes is self.__changes:
                    if self.size is not None and len(self.changes) > self.size + 1:
                        del self.__changes[1:2]
                    else:
                        self.__index += 1

    def __push_change__(self, change):
        # type: (BaseAtomicChange) -> None
        """
        Push change to the current batch.

        :param change: Change.
        """
        with self.app.write_context():
            if self.__executing:
                return
            with self._batch_context("Push Change", change=change):
                self.flush_redo()
                changes = self.__changes
                while changes and isinstance(changes[-1], BatchChanges):
                    if changes[-1].closed:
                        break
                    changes = changes[-1]._changes
                changes.append(change)
                if changes is self.__changes:
                    if self.size is not None and len(self.changes) > self.size + 1:
                        del self.__changes[1:2]
                    else:
                        self.__index += 1

    def __exit_batch__(self, batch):
        # type: (Batch) -> None
        """
        Exit batch context.

        :param batch: Batch.
        """
        with self.app.write_context():
            if self.__executing:
                return
            with self._batch_context("Exit Batch", batch=batch):
                changes = self.__changes
                while changes and isinstance(changes[-1], BatchChanges):
                    if changes[-1].change is batch:
                        changes[-1]._closed = True
                        break
                    changes = changes[-1]._changes
