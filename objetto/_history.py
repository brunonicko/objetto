# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING

from ._bases import final
from ._changes import BaseChange
from .factories import Integer
from .objects import (
    Object,
    attribute,
    protected_attribute_pair,
    protected_list_attribute_pair,
)

if TYPE_CHECKING:
    pass

__all__ = ["HistoryObject"]


class HistoryError(Exception):
    pass


# noinspection PyAbstractClass
@final
class BatchChanges(Object):

    change = attribute(BaseChange, subtypes=True, child=False, changeable=False)

    __changes__, changes = protected_list_attribute_pair(
        (BaseChange, "BatchChanges"), subtypes=True, data=False
    )

    __closed__, closed = protected_attribute_pair(bool, default=False, child=False)

    name = attribute(str, delegated=True, child=False, dependencies=(change,))

    @name.getter  # type: ignore
    def name(self):
        return self.change.name

    def format_changes(self):
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
        for change in reversed(self.changes):
            change.__undo__(change)

    def __redo__(self, _):
        for change in self.changes:
            change.__redo__(change)


# noinspection PyAbstractClass
@final
class HistoryObject(Object):
    __slots__ = ()

    size = attribute(
        (int, type(None)),
        default=None,
        factory=Integer(minimum=0, accepts_none=True),
        changeable=False,
        child=False,
    )

    __executing, executing = protected_attribute_pair(bool, default=False, child=False)

    __undoing, undoing = protected_attribute_pair(bool, default=False, child=False)

    __redoing, redoing = protected_attribute_pair(bool, default=False, child=False)

    __index, index = protected_attribute_pair(int, default=0, child=False)

    __changes, changes = protected_list_attribute_pair(
        (BaseChange, BatchChanges, type(None)),
        subtypes=True,
        default=(None,),
        data=False,
    )

    def set_index(self, index):
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
        with self.app.write_context():
            if self.__executing:
                error = "can't redo while executing"
                raise HistoryError(error)
            if self.__index < len(self.changes) - 1:
                change = self.changes[self.__index + 1]
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
        with self.app.write_context():
            if self.__executing:
                error = "can't undo while executing"
                raise HistoryError(error)

            if self.__index > 0:
                change = self.changes[self.index]
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
        with self.app.write_context():
            if self.__executing:
                error = "can't flush history while executing"
                raise HistoryError(error)
            if len(self.changes) > 1:
                with self._batch_context("Flush"):
                    self.__index = 0
                    del self.__changes[1:]

    def flush_redo(self):
        with self.app.write_context():
            if self.__executing:
                error = "can't flush history while executing"
                raise HistoryError(error)
            if len(self.changes) > 1:
                if self.__index < len(self.changes) - 1:
                    with self._batch_context("Flush Redo"):
                        del self.__changes[self.__index + 1 :]

    def in_batch(self):
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
        with self.app.write_context():
            if self.__executing:
                return
            with self._batch_context("Enter Batch", batch=batch):
                self.flush_redo()
                changes = self.__changes
                while changes and isinstance(changes[-1], BatchChanges):
                    if changes[-1].closed:
                        break
                    changes = changes[-1].__changes__
                changes.append(BatchChanges(self.app, change=batch))
                if changes is self.__changes:
                    if self.size is not None and len(self.changes) > self.size + 1:
                        del self.__changes[1:2]
                    else:
                        self.__index += 1

    def __push_change__(self, change):
        with self.app.write_context():
            if self.__executing:
                return
            with self._batch_context("Push Change", change=change):
                self.flush_redo()
                changes = self.__changes
                while changes and isinstance(changes[-1], BatchChanges):
                    if changes[-1].closed:
                        break
                    changes = changes[-1].__changes__
                changes.append(change)
                if changes is self.__changes:
                    if self.size is not None and len(self.changes) > self.size + 1:
                        del self.__changes[1:2]
                    else:
                        self.__index += 1

    def __exit_batch__(self, batch):
        with self.app.write_context():
            if self.__executing:
                return
            with self._batch_context("Exit Batch", batch=batch):
                changes = self.__changes
                while changes and isinstance(changes[-1], BatchChanges):
                    if changes[-1].change is batch:
                        changes[-1].__closed__ = True
                        break
                    changes = changes[-1].__changes__
