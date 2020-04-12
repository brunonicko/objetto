# -*- coding: utf-8 -*-
"""Command runner component."""

from abc import abstractmethod
from contextlib import contextmanager
from weakref import ref
from six import raise_from
from typing import Optional, ContextManager, Union, Any, List
from slotted import SlottedABC, SlottedSequence, SlottedHashable

from ._exceptions import CannotUndoError, CannotRedoError
from ._component import Component, CompositeMixin


class History(SlottedHashable, SlottedSequence):
    """Runs and keeps track of commands."""

    __slots__ = (
        "__weakref__",
        "__size",
        "__undo_stack",
        "__redo_stack",
        "__executing",
        "__batch",
        "__batches",
        "__flush_later",
        "__flush_redo_later",
        "__broadcaster"
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
        self.__executing = False
        self.__batch = None
        self.__batches = []
        self.__flush_later = False
        self.__flush_redo_later = False

    def __hash__(self):
        # type: () -> int
        """Get object hash."""
        return object.__hash__(self)

    def __getitem__(self, item):
        # type: (Union[int, slice]) -> Union[Any, List]
        """Get command/commands at index/slice."""
        return ([None] + (self.__undo_stack + list(reversed(self.__redo_stack))))[item]

    def __len__(self):
        # type: () -> int
        """Get command count."""
        return len(self.__undo_stack) + len(self.__redo_stack) + 1

    def flush_redo(self):
        # type: () -> None
        """Flush redo stack."""
        if self.__executing:
            self.__flush_redo_later = True
            return
        self.__flush_later, self.__flush_redo_later = False, False
        if not self.__redo_stack:
            return

        first_index = len(self.__undo_stack)
        last_index = first_index + len(self.__redo_stack) - 1
        old_values = tuple(reversed(self.__redo_stack))

        del self.__redo_stack[:]

    def flush(self):
        # type: () -> None
        """Flush entire history."""
        if self.__executing:
            self.__flush_later = True
            return
        self.__flush_later, self.__flush_redo_later = False, False
        for batch in self.__batches:
            del batch[1][:]
        if not self.__redo_stack and not self.__undo_stack:
            return
        del self.__redo_stack[:]
        del self.__undo_stack[:]

    def __flush_queued(self):
        # type: () -> None
        """Execute queued flush requests."""
        if self.__executing:
            raise RuntimeError("can't flush during execution")
        if self.__flush_later:
            self.flush()
        elif self.__flush_redo_later:
            self.flush_redo()
        self.__flush_later = False
        self.__flush_redo_later = False

    def __push__(self, command):
        # type: (Command) -> None
        """Run and push a command into the queue."""

        # If during execution
        if self.__executing:
            raise RuntimeError("already executing")

        # Command already attached
        if command.attached:
            raise ValueError("command already utilized")

        # Not during execution, command is not undoable
        elif not isinstance(command, UndoableCommand):

            # Associate command with this history
            command.__attach__(self)

            # Set executing flag
            self.__executing = True

            # Flush entire history
            self.flush()

            # Run redo delegate
            try:
                command.__redo__()

            # Reset execution flag no matter what
            finally:
                self.__executing = False
                self.__flush_queued()

        # Command is undoable
        else:

            # Associate command with this history if not in a batch
            if self.__batch is None:
                command.__attach__(self)

            # Flush redo only
            self.flush_redo()

            # Set executing flag
            self.__executing = True

            # Run redo delegate
            try:
                command.__redo__()

            # In case anything goes wrong, flush entire history and raise
            except Exception:
                self.__executing = False
                self.flush()
                raise

            # Reset execution flag no matter what
            finally:
                self.__executing = False
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
        first_index = last_index = len(self.__undo_stack)
        values = (command,)
        self.__undo_stack.append(command)

    def __adjust_stack_size(self):
        # type: () -> None
        """Adjust stack size."""
        if 0 <= self.size < len(self.__undo_stack):
            first_index = 0
            last_index = len(self.__undo_stack) - self.size - 1
            old_values = self.__undo_stack[first_index : last_index + 1]
            del self.__undo_stack[first_index : last_index + 1]

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
        if self.__executing:
            raise RuntimeError("already executing")

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

                    # Set ownership
                    batch.__attach__(self)

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
        if self.__executing:
            raise RuntimeError("can't set size during execution")
        if self.__batch is not None:
            raise RuntimeError("can't set size within a batch context")

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
        if self.__executing:
            raise RuntimeError("can't set current index during execution")
        if self.__batch is not None:
            raise RuntimeError("can't set current index within a batch context")

        # Check for invalid index
        if (
            current_index < 0
            or current_index >= len(self.__undo_stack) + len(self.__redo_stack) + 1
        ):
            raise IndexError(current_index)

        # Continuously run redo or undo until we reach the desired index
        old_current_index = self.current_index
        try:
            while self.current_index != current_index:
                self.__executing = True
                try:
                    old_index = self.current_index

                    # Change it
                    if current_index > self.current_index:
                        command = self.__redo_stack.pop()
                        command.__redo__()
                        self.__undo_stack.append(command)
                    elif current_index < self.current_index:
                        command = self.__undo_stack.pop()
                        command.__undo__()
                        self.__redo_stack.append(command)

                    # Emit signal for index change
                    new_index = self.current_index
                    if old_index != new_index:
                        pass
                        # self.__emit__(
                        #     HistoryIndexChangedEvent(old_index=old_index, index=new_index),
                        #     EventPhase.SINGLE,
                        # )

                except Exception:
                    self.__executing = False
                    self.flush()
                    raise
                finally:
                    self.__executing = False
                    self.__flush_queued()
        finally:
            if old_current_index != self.current_index:
                pass
                # self.__emit__(
                #     HistoryIndexFinishedChangedEvent(
                #         old_index=old_current_index, index=self.current_index
                #     ),
                #     EventPhase.SINGLE,
                # )

    @property
    def executing(self):
        # type: () -> bool
        """Whether currently executing a command."""
        return self.__executing

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
        return [None] + (self.__undo_stack + list(reversed(self.__redo_stack)))

    @property
    def flattened_commands(self):
        flattened_commands = []
        for command in self.commands:
            if isinstance(command, BatchCommand):
                flattened_commands.extend(command.flattened_commands)
            else:
                flattened_commands.append(command)
        return flattened_commands


class Command(SlottedABC):
    __slots__ = ("__name", "__owner_ref")

    def __init__(self, name):
        self.__name = name
        self.__owner_ref = None

    def __attach__(self, owner):
        if self.__owner_ref is not None:
            raise ValueError("command already utilized")
        self.__owner_ref = ref(owner)

    @abstractmethod
    def __redo__(self):
        raise NotImplementedError()

    @property
    def name(self):
        return self.__name

    @property
    def attached(self):
        return self.__owner_ref is not None


class UndoableCommand(Command):
    __slots__ = ()

    @abstractmethod
    def __undo__(self):
        raise NotImplementedError()


class BatchCommand(Command):
    __slots__ = ("__weakref__", "__commands")

    def __init__(self, name, *commands):
        super(BatchCommand, self).__init__(name)
        for command in commands:
            command.__attach__(self)
        self.__commands = commands

    def __redo__(self):
        for command in self.commands:
            command.__redo__()

    @property
    def commands(self):
        return self.__commands

    @property
    def flattened_commands(self):
        flattened_commands = []
        for command in self.commands:
            if isinstance(command, BatchCommand):
                flattened_commands.extend(command.flattened_commands)
            else:
                flattened_commands.append(command)
        return flattened_commands


class UndoableBatchCommand(BatchCommand, UndoableCommand):
    __slots__ = ()

    def __init__(self, name, *commands):
        for command in commands:
            if not isinstance(command, UndoableCommand):
                raise ValueError("command {} is not undoable".format(command))
        super(UndoableBatchCommand, self).__init__(name, *commands)

    def __undo__(self):
        for command in reversed(self.commands):
            command.__undo__()


class Runner(Component):
    __slots__ = ("__weakref__", "__history", "__executing")

    def __init__(self, obj):
        # type: (CompositeMixin) -> None
        """Initialize."""
        super(Runner, self).__init__(obj)
        self.__history = None
        self.__executing = False

    def run(self, command):
        if self.__executing:
            raise RuntimeError("already executing")
        self.__executing = True
        try:
            if self.__history is None:
                command.__attach__(self)
                command.__redo__()
            else:
                self.__history.__push__(command)
        finally:
            self.__executing = False

    @property
    def history(self):
        return self.__history

    @history.setter
    def history(self, history):
        old_history = self.__history
        if old_history is history:
            return
        if old_history is not None:
            old_history.flush()
        self.__history = history

    @property
    def executing(self):
        return self.__executing
