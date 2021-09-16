# -*- coding: utf-8 -*-
"""Read-write locks."""

from abc import abstractmethod
from contextlib import contextmanager
from collections import Counter
from threading import Condition, RLock, current_thread
from typing import TYPE_CHECKING

from .base import Base

if TYPE_CHECKING:
    from typing import Iterator, Literal

__all__ = ["AbstractRWLock", "RWLock", "RWThreadingLock"]


class AbstractRWLock(Base):
    """Abstract read-write lock."""
    __slots__ = ()

    @abstractmethod
    def get_current_context(self):
        # type: () -> Literal["read", "write", None]
        raise NotImplementedError()

    @contextmanager
    @abstractmethod
    def read_context(self):
        # type: () -> Iterator
        raise NotImplementedError()

    @contextmanager
    @abstractmethod
    def write_context(self):
        # type: () -> Iterator
        raise NotImplementedError()

    @contextmanager
    def require_context(self):
        # type: () -> Iterator
        context = self.get_current_context()
        if context not in ("read", "write"):
            error = "not in a read/write context"
            raise RuntimeError(error)
        yield

    @contextmanager
    def require_read_context(self):
        # type: () -> Iterator
        context = self.get_current_context()
        if context != "read":
            error = "not in a read context"
            raise RuntimeError(error)
        yield

    @contextmanager
    def require_write_context(self):
        # type: () -> Iterator
        context = self.get_current_context()
        if context != "write":
            error = "not in a write context"
            raise RuntimeError(error)
        yield


class RWLock(AbstractRWLock):
    """Read-write lock (not thread safe)."""

    __slots__ = ("__reading", "__writing")

    def __init__(self):
        self.__reading = False
        self.__writing = False

    def get_current_context(self):
        # type: () -> Literal["read", "write", None]
        if self.__reading:
            return "read"
        elif self.__writing:
            return "write"
        else:
            return None

    @contextmanager
    def read_context(self):
        # type: () -> Iterator
        previous = self.__reading
        self.__reading = True
        try:
            yield
        finally:
            self.__reading = previous

    @contextmanager
    def write_context(self):
        # type: () -> Iterator
        if self.__reading:
            error = "can't write while reading"
            raise RuntimeError(error)
        previous = self.__writing
        self.__writing = True
        try:
            yield
        finally:
            self.__writing = previous


class RWThreadingLock(AbstractRWLock):
    """One-writes, many-read threading lock."""

    __slots__ = ("__read_ready", "__readers", "__writer")

    def __init__(self):
        self.__read_ready = Condition(RLock())
        self.__readers = Counter()
        self.__writer = None

    def get_current_context(self):
        # type: () -> Literal["read", "write", None]
        thread = current_thread()
        with self.__read_ready:
            if thread in self.__readers:
                return "read"
            elif thread is self.__writer:
                return "write"
            else:
                return None

    @contextmanager
    def read_context(self):
        # type: () -> Iterator
        thread = current_thread()
        with self.__read_ready:
            self.__readers[thread] += 1
        try:
            yield
        finally:
            with self.__read_ready:
                self.__readers[thread] -= 1
                if not self.__readers[thread]:
                    del self.__readers[thread]
                if not self.__readers:
                    self.__read_ready.notifyAll()

    @contextmanager
    def write_context(self):
        # type: () -> Iterator
        thread = current_thread()
        with self.__read_ready:
            while self.__readers:
                if thread in self.__readers:
                    error = "can't write while reading"
                    raise RuntimeError(error)
                self.__read_ready.wait()
            previous_writer = self.__writer
            assert previous_writer is None or previous_writer is thread
            self.__writer = thread
            try:
                yield
            finally:
                self.__writer = previous_writer

    @contextmanager
    def require_context(self):
        # type: () -> Iterator
        with self.__read_ready:
            with super(RWThreadingLock, self).require_context():
                yield

    @contextmanager
    def require_read_context(self):
        # type: () -> Iterator
        with self.__read_ready:
            with super(RWThreadingLock, self).require_read_context():
                yield

    @contextmanager
    def require_write_context(self):
        # type: () -> Iterator
        with self.__read_ready:
            with super(RWThreadingLock, self).require_write_context():
                yield
