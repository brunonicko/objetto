# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING

from ._bases import final
from ._changes import BaseAtomicChange, Batch
from ._exceptions import BaseObjettoException
from .factories import Integer
from .objects import (
    Object,
    attribute,
    protected_attribute_pair,
    protected_list_attribute_pair,
)

if TYPE_CHECKING:
    from typing import Any, Optional, TypeVar, Union

    from ._objects import (
        Attribute,
        DictObject,
        ListObject,
        MutableDictObject,
        MutableListObject,
        MutableSetObject,
        ProxyDictObject,
        ProxyListObject,
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

__all__ = ["HistoryError", "BatchChanges", "HistoryObject"]


class HistoryError(BaseObjettoException):
    """
    History failed to execute.

    Inherits from:
      - :class:`objetto.bases.BaseObjettoException`
    """


# noinspection PyAbstractClass
@final
class BatchChanges(Object):
    """
    Batch changes.

    Inherits from:
      - :class:`objetto.objects.Object`
    """

    __slots__ = ()

    change = attribute(Batch, checked=False, changeable=False)  # type: Attribute[Batch]
    """
    Batch change with name and metadata.

    :type: objetto.changes.Batch
    """

    name = attribute(str, checked=False, changeable=False)  # type: Attribute[str]
    """
    The batch change name.

    :type: str
    """

    _changes, changes = protected_list_attribute_pair(
        (BaseAtomicChange, "BatchChanges"), subtypes=True, checked=False
    )  # type: PLA[CT], LA[CT]
    """
    Changes executed during the batch.

    :type: objetto.objects.ListObject[objetto.history.BatchChanges or \
 objetto.bases.BaseAtomicChange]
    """

    _closed, closed = protected_attribute_pair(
        bool, checked=False, default=False
    )  # type: Attribute[bool], Attribute[bool]
    """
    Whether the batch has already completed or is still running.

    :type: bool
    """

    def format_changes(self):
        # type: () -> str
        """
        Format changes into readable string.

        :return: Formatted changes.
        :rtype: str
        """
        with self.app.read_context():
            parts = []
            # noinspection PyTypeChecker
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
        # noinspection PyTypeChecker
        for change in reversed(self.changes):
            change.__undo__(change)

    def __redo__(self, _):
        # type: (Any) -> None
        """Redo."""
        # noinspection PyTypeChecker
        for change in self.changes:
            change.__redo__(change)


# noinspection PyAbstractClass
@final
class HistoryObject(Object):
    """
    History object.

    Inherits from:
      - :class:`objetto.objects.Object`
    """

    __slots__ = ()

    size = attribute(
        (int, None),
        checked=False,
        default=None,
        factory=Integer(minimum=0, accepts_none=True),
        changeable=False,
    )  # type: Attribute[int]
    """
    How many changes to remember.

    :type: int
    """

    __executing, executing = protected_attribute_pair(
        bool, checked=False, default=False
    )  # type: Attribute[bool], Attribute[bool]
    """
    Whether the history is undoing or redoing.

    :type: bool
    """

    __undoing, undoing = protected_attribute_pair(
        bool, checked=False, default=False
    )  # type: Attribute[bool], Attribute[bool]
    """
    Whether the history is undoing.

    :type: bool
    """

    __redoing, redoing = protected_attribute_pair(
        bool, checked=False, default=False
    )  # type: Attribute[bool], Attribute[bool]
    """
    Whether the history is redoing.

    :type: bool
    """

    __index, index = protected_attribute_pair(
        int, checked=False, default=0
    )  # type: Attribute[int], Attribute[int]
    """
    The index of the current change.

    :type: int
    """

    __changes, changes = protected_list_attribute_pair(
        (BatchChanges, None),
        subtypes=True,
        checked=False,
        default=(None,),
    )  # type: PLA[Optional[BatchChanges]], LA[Optional[BatchChanges]]
    """
    List of batch changes. The first one is always `None`.

    :type: objetto.objects.ListObject[objetto.history.BatchChanges or None]
    """

    _current_batches, current_batches = protected_list_attribute_pair(
        BatchChanges,
        subtypes=False,
        checked=False,
        child=False,
    )  # type: PLA[BatchChanges], LA[BatchChanges]
    """
    Open batches.

    :type: objetto.objects.ListObject[objetto.history.BatchChanges]
    """

    def set_index(self, index):
        # type: (int) -> None
        """
        Undo/redo until we reach the desired index.

        :param index: Index.
        :type index: int

        :raise IndexError: Invalid index.
        """
        with self.app.write_context():
            if self.__executing:
                error = "can't set index while executing"
                raise HistoryError(error)
            if 0 <= index <= len(self.changes) - 1:
                if index > self.__index:
                    with self._batch_context("Multiple Redo"):
                        while index > self.__index:
                            self.redo()
                elif index < self.__index:
                    with self._batch_context("Multiple Undo"):
                        while index < self.__index:
                            self.undo()
            else:
                raise IndexError(index)

    def undo_all(self):
        # type: () -> None
        """
        Undo all.

        :raises HistoryError: Can't undo all while executing.
        """
        with self.app.write_context():
            if self.__executing:
                error = "can't undo all while executing"
                raise HistoryError(error)
            with self._batch_context("Undo All"):
                while self.__index > 0:
                    self.undo()

    def redo_all(self):
        # type: () -> None
        """
        Redo all.

        :raises HistoryError: Can't redo all while executing.
        """
        with self.app.write_context():
            if self.__executing:
                error = "can't redo all while executing"
                raise HistoryError(error)
            with self._batch_context("Redo All"):
                while self.__index < len(self.changes) - 1:
                    self.redo()

    # noinspection PyTypeChecker
    def redo(self):
        # type: () -> None
        """
        Redo.

        :raises HistoryError: Can't redo while executing.
        """
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

    # noinspection PyTypeChecker
    def undo(self):
        # type: () -> None
        """
        Undo.

        :raises HistoryError: Can't undo while executing.
        """
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
                    # noinspection PyTypeChecker
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
        :rtype: bool

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
        :rtype: str
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
                elif change is not None:
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
                topmost = not self._current_batches
                batch_changes = BatchChanges(self.app, change=batch, name=batch.name)
                if topmost:
                    self.__changes.append(batch_changes)
                    if self.size is not None and len(self.changes) > self.size + 1:
                        del self.__changes[1:2]
                    else:
                        self.__index += 1
                else:
                    self._current_batches[-1]._changes.append(batch_changes)
                self._current_batches.append(batch_changes)

    def __push_change__(self, change):
        # type: (BaseAtomicChange) -> None
        """
        Push change to the current batch.

        :param change: Change.
        :raises RuntimeError: Reaction triggered during history redo/undo.
        """
        with self.app.write_context():

            # Check for inconsistent changes triggered during reactions while executing.
            if self.__executing:
                if isinstance(change, BaseAtomicChange) and change.history is not self:
                    error = "reaction triggered during history redo/undo in {}".format(
                        change.obj
                    )
                    raise RuntimeError(error)
                return

            # We should always be in a batch (the application should make sure of it).
            assert self._current_batches

            # Add to batch.
            with self._batch_context("Push Change", change=change):
                self.flush_redo()
                self._current_batches[-1]._changes.append(change)

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
                assert batch is self._current_batches[-1].change
                self._current_batches[-1]._closed = True
                self._current_batches.pop()
