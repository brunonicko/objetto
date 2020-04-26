# -*- coding: utf-8 -*-
"""Command/History implementation."""

from abc import abstractmethod
from contextlib import contextmanager
from six import raise_from
from typing import Optional, ContextManager, Union, Any, List, Tuple, cast
from slotted import Slotted, SlottedABC

from .._base.exceptions import ModeloException, ModeloError
from .._base.events import Event
from .._components.broadcaster import Broadcaster, EventPhase, EventEmitter

__all__ = [
    "HistoryEvent",
    "HistoryCurrentIndexChangeEvent",
    "HistoryInsertEvent",
    "HistoryPopEvent",
    "History",
    "Command",
    "UndoableCommand",
    "BatchCommand",
    "UndoableBatchCommand",
    "HistoryException",
    "HistoryError",
    "WhileRunningError",
    "AlreadyRanError",
    "CannotUndoError",
    "CannotRedoError",
]


class HistoryEvent(Event):
    """Abstract event. Describes a change in a history."""

    __slots__ = ("__history",)

    def __init__(self, history):
        # type: (History) -> None
        """Initialize with history."""
        self.__history = history

    def __eq_id_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should compared using object identity."""
        return ("history",)

    @abstractmethod
    def __eq_equal_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should compared using equality."""
        return ()

    @abstractmethod
    def __repr_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__repr__'."""
        return ()

    @abstractmethod
    def __str_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__str__'."""
        return ("history",)

    @property
    def history(self):
        # type: () -> History
        """History."""
        return self.__history


class HistoryCurrentIndexChangeEvent(HistoryEvent):
    """Emitted when a history's current index changes."""

    __slots__ = ("__old_current_index", "__new_current_index")

    def __init__(
        self,
        history,  # type: History
        old_current_index,  # type: int
        new_current_index,  # type: int
    ):
        # type: (...) -> None
        """Initialize with old index and new index."""
        super(HistoryCurrentIndexChangeEvent, self).__init__(history)
        self.__old_current_index = old_current_index
        self.__new_current_index = new_current_index

    def __eq_equal_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should compared using equality."""
        return super(HistoryCurrentIndexChangeEvent, self).__eq_equal_properties__() + (
            "old_current_index",
            "new_current_index",
        )

    def __repr_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__repr__'."""
        return super(HistoryCurrentIndexChangeEvent, self).__repr_properties__() + (
            "old_current_index",
            "new_current_index",
        )

    def __str_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__str__'."""
        return super(HistoryCurrentIndexChangeEvent, self).__str_properties__() + (
            "old_current_index",
            "new_current_index",
        )

    @property
    def old_current_index(self):
        # type: () -> int
        """Old index."""
        return self.__old_current_index

    @property
    def new_current_index(self):
        # type: () -> int
        """New index."""
        return self.__new_current_index


class HistoryInsertEvent(HistoryCurrentIndexChangeEvent):
    """Emitted when commands are inserted into the history."""

    __slots__ = ("__index", "__last_index", "__new_commands")

    def __init__(
        self,
        history,  # type: History
        old_current_index,  # type: int
        new_current_index,  # type: int
        index,  # type: int
        last_index,  # type: int
        new_commands,  # type: Tuple[Any, ...]
    ):
        # type: (...) -> None
        """Initialize with index, last index, and new commands."""
        super(HistoryInsertEvent, self).__init__(
            history, old_current_index, new_current_index
        )
        self.__index = index
        self.__last_index = last_index
        self.__new_commands = new_commands

    def __eq_equal_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should compared using equality."""
        return super(HistoryInsertEvent, self).__eq_equal_properties__() + (
            "index",
            "last_index",
            "new_commands",
        )

    def __repr_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__repr__'."""
        return super(HistoryInsertEvent, self).__repr_properties__() + (
            "index",
            "last_index",
            "new_commands",
        )

    def __str_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__str__'."""
        return super(HistoryInsertEvent, self).__str_properties__() + (
            "index",
            "last_index",
            "new_commands",
        )

    @property
    def index(self):
        # type: () -> int
        """Index."""
        return self.__index

    @property
    def last_index(self):
        # type: () -> int
        """Last index."""
        return self.__last_index

    @property
    def new_commands(self):
        # type: () -> Tuple[Command, ...]
        """New commands."""
        return self.__new_commands


class HistoryPopEvent(HistoryCurrentIndexChangeEvent):
    """Emitted when commands are popped from the history."""

    __slots__ = ("__index", "__last_index", "__old_commands")

    def __init__(
        self,
        history,  # type: History
        old_current_index,  # type: int
        new_current_index,  # type: int
        index,  # type: int
        last_index,  # type: int
        old_commands,  # type: Tuple[Any, ...]
    ):
        # type: (...) -> None
        """Initialize with index, last index, and old commands."""
        super(HistoryPopEvent, self).__init__(
            history, old_current_index, new_current_index
        )
        self.__index = index
        self.__last_index = last_index
        self.__old_commands = old_commands

    def __eq_equal_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should compared using equality."""
        return super(HistoryPopEvent, self).__eq_equal_properties__() + (
            "index",
            "last_index",
            "old_commands",
        )

    def __repr_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__repr__'."""
        return super(HistoryPopEvent, self).__repr_properties__() + (
            "index",
            "last_index",
            "old_commands",
        )

    def __str_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__str__'."""
        return super(HistoryPopEvent, self).__str_properties__() + (
            "index",
            "last_index",
            "old_commands",
        )

    @property
    def index(self):
        # type: () -> int
        """Index."""
        return self.__index

    @property
    def last_index(self):
        # type: () -> int
        """Last index."""
        return self.__last_index

    @property
    def old_commands(self):
        # type: () -> Tuple[Command, ...]
        """Old commands."""
        return self.__old_commands


class History(Slotted):
    """Keeps track of commands, allowing for undo/redo operations."""

    __slots__ = (
        "__weakref__",
        "__size",
        "__undo_stack",
        "__redo_stack",
        "__running",
        "__batch",
        "__batches",
        "__flush_later",
        "__flush_redo_later",
        "__broadcaster",
    )

    def __init__(self, size=0):
        # type: (int) -> None
        """Initialize with size."""
        size = int(size)
        if size < -1:
            size = -1

        self.__size = size
        self.__undo_stack = []
        self.__redo_stack = []
        self.__running = False
        self.__batch = None
        self.__batches = []
        self.__flush_later = False
        self.__flush_redo_later = False
        self.__broadcaster = Broadcaster()

    def __getitem__(self, item):
        # type: (Union[int, slice]) -> Union[Any, List]
        """Get command/commands at index/slice."""
        return ([None] + (self.__undo_stack + list(reversed(self.__redo_stack))))[item]

    def __len__(self):
        # type: () -> int
        """Get command count."""
        return len(self.__undo_stack) + len(self.__redo_stack) + 1

    @contextmanager
    def _event_context(self, event):
        # type: (HistoryEvent) -> ContextManager
        """Event context."""
        if self.__broadcaster.emit(event, EventPhase.INTERNAL_PRE):
            self.__broadcaster.emit(event, EventPhase.PRE)
            yield
            self.__broadcaster.emit(event, EventPhase.POST)
            self.__broadcaster.emit(event, EventPhase.INTERNAL_POST)
        else:
            raise RuntimeError(
                "internal event rejection not allowed for history events"
            )

    def flush_redo(self):
        # type: () -> None
        """Flush redo stack."""
        if self.__running:
            self.__flush_redo_later = True
            return
        self.__flush_later, self.__flush_redo_later = False, False
        if not self.__redo_stack:
            return

        index = len(self.__undo_stack)
        last_index = index + len(self.__redo_stack) - 1
        old_commands = tuple(reversed(self.__redo_stack))
        event = HistoryPopEvent(
            history=self,
            index=index,
            old_current_index=index,
            new_current_index=index,
            last_index=last_index,
            old_commands=old_commands,
        )

        with self._event_context(event):
            del self.__redo_stack[:]

    def flush(self):
        # type: () -> None
        """Flush entire history."""
        if self.__running:
            self.__flush_later = True
            return
        self.__flush_later, self.__flush_redo_later = False, False
        for batch in self.__batches:
            del batch[1][:]
        if not self.__redo_stack and not self.__undo_stack:
            return

        index = 1
        last_index = len(self)
        old_commands = tuple(self)
        event = HistoryPopEvent(
            history=self,
            index=index,
            old_current_index=len(self.__undo_stack),
            new_current_index=0,
            last_index=last_index,
            old_commands=old_commands,
        )

        with self._event_context(event):
            del self.__redo_stack[:]
            del self.__undo_stack[:]

    def __flush_queued(self):
        # type: () -> None
        """Execute queued flush requests."""
        if self.__running:
            error = "can't flush during execution"
            raise RuntimeError(error)
        if self.__flush_later:
            self.flush()
        elif self.__flush_redo_later:
            self.flush_redo()
        self.__flush_later = False
        self.__flush_redo_later = False

    def __run__(self, command):
        # type: (Command) -> None
        """Run a command and keep track of it."""

        # During execution, run and swallow command
        if self.__running:
            if command.ran:
                raise AlreadyRanError(command)
            command.__flag_ran__()
            command.__redo__()
            return

        # Command already ran
        if command.ran:
            raise AlreadyRanError(command)

        # Not during execution, command is not undoable
        elif not isinstance(command, UndoableCommand):

            # Flag command as 'ran'
            command.__flag_ran__()

            # Set running flag
            self.__running = True

            # Flush entire history
            self.flush()

            # Run redo delegate
            try:
                command.__redo__()

            # Reset execution flag no matter what
            finally:
                self.__running = False
                self.__flush_queued()

        # Command is undoable
        else:

            # Flag command as 'ran' if not in a batch
            if self.__batch is None:
                command.__flag_ran__()

            # Flush redo only
            self.flush_redo()

            # Set running flag
            self.__running = True

            # Run redo delegate
            try:
                command.__redo__()

            # In case anything goes wrong, flush entire history and raise
            except Exception:
                self.__running = False
                self.flush()
                raise

            # Reset execution flag no matter what
            finally:
                self.__running = False
                self.__flush_queued()

            # In a batch
            if self.__batch is not None:

                # Add command to the batch
                self.__batch[1].append(command)

            # Not in a batch and size is different than 0
            elif self.size != 0:

                # Add command to the undo stack
                self.__append_to_undo_stack(command)

                # Adjust stack size
                self.__adjust_stack_size()

    def __append_to_undo_stack(self, command):
        # type: (Command) -> None
        """Append to undo stack."""
        index = last_index = len(self.__undo_stack)
        new_commands = (command,)

        event = HistoryInsertEvent(
            history=self,
            index=index,
            old_current_index=index,
            new_current_index=index + 1,
            last_index=last_index,
            new_commands=new_commands,
        )
        with self._event_context(event):
            self.__undo_stack.append(command)

    def __adjust_stack_size(self):
        # type: () -> None
        """Adjust stack size."""
        if 0 <= self.size < len(self.__undo_stack):
            last_index = len(self.__undo_stack) - self.size - 1
            old_commands = tuple(self.__undo_stack[0 : last_index + 1])

            old_current_index = len(self.__undo_stack)
            new_current_index = old_current_index - (last_index + 1)

            pop_event = HistoryPopEvent(
                history=self,
                index=0,
                old_current_index=old_current_index,
                new_current_index=new_current_index,
                last_index=last_index,
                old_commands=old_commands,
            )
            with self._event_context(pop_event):
                del self.__undo_stack[0 : last_index + 1]

    def undo_all(self):
        # type: () -> None
        """Undo all."""
        while self.current_index > 0:
            self.current_index -= 1

    def redo_all(self):
        # type: () -> None
        """Redo all."""
        while self.current_index < len(self.__undo_stack) + len(self.__redo_stack):
            self.current_index += 1

    def undo(self):
        # type: () -> None
        """Undo."""
        try:
            self.current_index -= 1
        except IndexError:
            exc = CannotUndoError("can't undo")
            raise_from(exc, None)
            raise exc

    def redo(self):
        # type: () -> None
        """Redo."""
        try:
            self.current_index += 1
        except IndexError:
            exc = CannotRedoError("can't redo")
            raise_from(exc, None)
            raise exc

    @contextmanager
    def batch_context(self, name):
        # type: (str) -> ContextManager
        """Start a new batch context."""

        # Already running
        if self.__running:
            yield

        # Store previous batch and start a new one
        else:
            previous_batch = self.__batch
            self.__batch = name, []
            self.__batches.append(self.__batch)

            # noinspection PyBroadException
            try:
                yield
            except Exception:
                if previous_batch is not None:
                    self.flush()
                    raise
            else:

                # If we have commands in the resulting batch
                if self.__batch[1]:

                    # Make batch command
                    commands = self.__batch[1]
                    for command in commands:
                        if not isinstance(command, UndoableCommand):
                            batch_cls = BatchCommand
                            undoable = False
                            break
                    else:
                        batch_cls = UndoableBatchCommand
                        undoable = True

                    batch = batch_cls(self.__batch[0], *self.__batch[1])

                    # We have a previous batch, add command to it
                    if previous_batch is not None:
                        previous_batch[1].append(batch)

                    # No previous batch
                    else:

                        # Flag batch command as 'ran'
                        batch.__flag_ran__()

                        # One or more commands are not undoable, flush history
                        if not undoable:
                            self.flush()

                        # If all commands are undoable and size is different than 0
                        elif self.size != 0:

                            # Flush redo
                            self.flush_redo()

                            # Add batch command to the undo stack
                            self.__append_to_undo_stack(batch)

                            # Adjust stack size
                            self.__adjust_stack_size()

            # Close batch (and restore previous batch if there was one)
            finally:
                if previous_batch is None:
                    del self.__batches[:]
                self.__batch = previous_batch

    @property
    def size(self):
        # type: () -> int
        """How many commands to remember."""
        return self.__size

    @size.setter
    def size(self, size):
        # type: (int) -> None
        """How many commands to remember."""

        # Error, can't change while running
        if self.__running:
            error = "can't change history size while running a command"
            raise WhileRunningError(error)
        if self.__batch is not None:
            error = "can't change history size within a batch context"
            raise WhileRunningError(error)

        # Format size
        size = int(size)
        if size < -1:
            size = -1

        # Store value
        old_size = self.size
        self.__size = size

        # Flush history if shrinking
        if self.size != -1 and self.size < old_size:
            self.flush()

    @property
    def current_index(self):
        # type: () -> int
        """Current index."""
        return len(self.__undo_stack)

    @current_index.setter
    def current_index(self, current_index):
        # type: (int) -> None
        """Current index."""

        # Error, can't change while running
        if self.__running:
            error = "can't change history index while running a command"
            raise WhileRunningError(error)
        if self.__batch is not None:
            error = "can't change history index within a batch context"
            raise WhileRunningError(error)

        # Check for invalid index
        if (
            current_index < 0
            or current_index >= len(self.__undo_stack) + len(self.__redo_stack) + 1
        ):
            raise IndexError(current_index)

        # Continuously run redo or undo until we reach the desired index
        while self.current_index != current_index:
            self.__running = True
            try:
                if current_index > self.current_index:
                    event = HistoryCurrentIndexChangeEvent(
                        history=self,
                        old_current_index=self.current_index,
                        new_current_index=self.current_index + 1,
                    )
                    with self._event_context(event):
                        command = self.__redo_stack.pop()
                        command.__redo__()
                        self.__undo_stack.append(command)
                elif current_index < self.current_index:
                    event = HistoryCurrentIndexChangeEvent(
                        history=self,
                        old_current_index=self.current_index,
                        new_current_index=self.current_index - 1,
                    )
                    with self._event_context(event):
                        command = self.__undo_stack.pop()
                        command.__undo__()
                        self.__redo_stack.append(command)
            except Exception:
                self.__running = False
                self.flush()
                raise
            finally:
                self.__running = False
                self.__flush_queued()

    @property
    def running(self):
        # type: () -> bool
        """Whether currently running a command."""
        return self.__running

    @property
    def current_batch(self):
        # type: () -> Optional[str]
        """Current batch context name."""
        if self.__batch is not None:
            return self.__batch[0]

    @property
    def in_batch(self):
        # type: () -> bool
        """Whether in a batch."""
        return self.__batch is not None

    @property
    def commands(self):
        # type: () -> Tuple[Optional[Command], ...]
        """Get commands."""
        return tuple([None] + (self.__undo_stack + list(reversed(self.__redo_stack))))

    @property
    def flattened_commands(self):
        # type: () -> Tuple[Optional[Command], ...]
        """Get commands (flatten batch commands)."""
        flattened_commands = []
        for command in self.commands:
            if isinstance(command, BatchCommand):
                flattened_commands.extend(command.flattened_commands)
            else:
                flattened_commands.append(command)
        return tuple(flattened_commands)

    @property
    def can_redo(self):
        # type: () -> bool
        """Whether can redo."""
        return self.current_index < len(self) - 1

    @property
    def can_undo(self):
        # type: () -> bool
        """Whether can undo."""
        return self.current_index > 0

    @property
    def events(self):
        # type: () -> EventEmitter
        """Event emitter."""
        return self.__broadcaster.emitter


class Command(SlottedABC):
    """Contains a delegate function and the necessary data to run it."""

    __slots__ = ("__name", "__ran")

    def __init__(self, name):
        # type: (str) -> None
        """Initialize with name."""
        self.__name = str(name)
        self.__ran = False

    def __flag_ran__(self):
        # type: () -> None
        """Flag this command as 'ran'."""
        if self.__ran:
            raise AlreadyRanError(self)
        self.__ran = True

    @abstractmethod
    def __redo__(self):
        # type: () -> None
        """Redo delegate."""
        raise NotImplementedError()

    @property
    def name(self):
        # type: () -> str
        """Command name."""
        return self.__name

    @property
    def ran(self):
        # type: () -> bool
        """Whether this command already ran."""
        return self.__ran


class UndoableCommand(Command):
    """Special type of command that also contains a delegate to undo its changes."""

    __slots__ = ()

    @abstractmethod
    def __undo__(self):
        # type: () -> None
        """Undo delegate."""
        raise NotImplementedError()


class BatchCommand(Command):
    """Concatenates multiple commands into one."""

    __slots__ = ("__weakref__", "__commands")

    def __init__(self, name, *commands):
        # type: (str, Tuple[Command, ...]) -> None
        """Initialize with name and commands."""
        super(BatchCommand, self).__init__(name)
        for command in commands:
            command.__flag_ran__()
        self.__commands = commands

    def __redo__(self):
        # type: () -> None
        """Redo delegate."""
        for command in self.commands:
            command.__redo__()

    @property
    def commands(self):
        # type: () -> Tuple[Optional[Command], ...]
        """Get commands."""
        return self.__commands

    @property
    def flattened_commands(self):
        # type: () -> Tuple[Command, ...]
        """Get commands (flatten batch commands)."""
        flattened_commands = []
        for command in self.commands:
            if isinstance(command, BatchCommand):
                flattened_commands.extend(command.flattened_commands)
            else:
                flattened_commands.append(command)
        return tuple(flattened_commands)


class UndoableBatchCommand(BatchCommand, UndoableCommand):
    """Concatenates multiple undoable commands into one."""

    __slots__ = ()

    def __init__(self, name, *commands):
        # type: (str, Tuple[UndoableCommand, ...]) -> None
        """Initialize with name and undoable commands."""
        for command in commands:
            if not isinstance(command, UndoableCommand):
                error = "command {} is not undoable".format(command)
                raise TypeError(error)
        super(UndoableBatchCommand, self).__init__(name, *commands)

    def __undo__(self):
        # type: () -> None
        """Undo delegate."""
        for command in reversed(self.commands):
            cast(UndoableCommand, command).__undo__()


class HistoryException(ModeloException):
    """History exception."""


class HistoryError(ModeloError, HistoryException):
    """History error."""


class WhileRunningError(HistoryError):
    """Raised when trying to perform an operation during an ongoing execution."""


class AlreadyRanError(HistoryError):
    """Raised when trying to run a command that has already been used before."""


class CannotUndoError(HistoryError):
    """Raised when trying to undo but no more commands are available."""


class CannotRedoError(HistoryError):
    """Raised when trying to redo but no more commands are available."""
