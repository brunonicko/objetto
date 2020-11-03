# -*- coding: utf-8 -*-
"""Base class and metaclass."""

from inspect import getmro
from contextlib import contextmanager
from typing import TYPE_CHECKING, final, cast

from qualname import qualname  # type: ignore
from decorator import decorator
from six import with_metaclass, iteritems
from slotted import SlottedABCMeta, SlottedABC

from .utils.immutable import ImmutableDict

if TYPE_CHECKING:
    from typing import Any, TypeVar, Iterator, Set, Optional, Type, List, Iterable

    T = TypeVar("T")

__all__ = ["final", "BaseMeta", "Base", "ProtectedBase"]


ABSTRACT_TAG = "__isabstractmethod__"
FINAL_CLASS_TAG = "__isfinalclass__"
FINAL_METHOD_TAG = "__isfinalmethod__"
INITIALIZING_TAG = "__isinitializing__"

__final = final


def _final(obj):
    # type: (T) -> T
    """Final decorator that enables runtime checking for :class:`Base` classes."""
    if isinstance(obj, type):
        type.__setattr__(obj, FINAL_CLASS_TAG, True)
    else:
        object.__setattr__(cast(object, obj), FINAL_METHOD_TAG, True)
    return __final(obj)


globals()["final"] = _final


def _simplified_member_names(names):
    # type: (Iterable[str]) -> Iterator[str]
    """Iterate over member names and only yield the simplified ones."""
    return (n for n in names if not ("__" in n and n.startswith("_")))


@contextmanager
def init_context(obj):
    # type: (Base) -> Iterator
    """Context manager that sets the initializing tag for :class:`Base` objects."""
    previous = getattr(obj, INITIALIZING_TAG, False)
    object.__setattr__(obj, INITIALIZING_TAG, True)
    try:
        yield
    finally:
        object.__setattr__(obj, INITIALIZING_TAG, previous)


@decorator
def init(func, *args, **kwargs):
    # type: (T, Any, Any) -> T
    """Method decorator that sets the initializing tag for :class:`Base` objects."""
    self = args[0]
    with init_context(self):
        result = func(*args, **kwargs)
    return result


class BaseMeta(SlottedABCMeta):
    """Metaclass for :class:`Base`."""

    @staticmethod
    def __new__(mcs, name, bases, dct):
        dct = dict(dct)

        # Force '__hash__' to be declared if '__eq__' is declared.
        if "__eq__" in dct and "__hash__" not in dct:
            error = "declared '__eq__' in '{}', but didn't declare '__hash__'".format(
                name
            )
            raise TypeError(error)

        # Always decorate '__init__' method with 'init'.
        if "__init__" in dct:
            dct["__init__"] = init(dct["__init__"])

        return super(BaseMeta, mcs).__new__(mcs, name, bases, dct)

    def __init__(cls, name, bases, dct):
        super(BaseMeta, cls).__init__(name, bases, dct)

        # Traverse the MRO from the bottom.
        final_method_names = set()  # type: Set[str]
        final_cls = None  # type: Optional[Type]
        skip_bases = set(getmro(SlottedABC))  # type: Set[Type]
        for base in reversed(getmro(cls)):
            if base in skip_bases:
                continue

            # Disallow non-BaseMeta bases.
            # if not isinstance(base, BaseMeta):
            #     error = (
            #         "can't use base '{}' since its metaclass does not inherit from '{}'"
            #     ).format(base.__name__, BaseMeta.__name__)
            #     raise TypeError(error)

            # Prevent subclassing final classes.
            if getattr(base, FINAL_CLASS_TAG, False) is True:
                if final_cls is not None:
                    error = "can't subclass final class '{}'".format(final_cls.__name__)
                    raise TypeError(error)
                final_cls = base

            # Prevent overriding of final methods.
            for member_name, member in iteritems(base.__dict__):
                if member_name in final_method_names:
                    error = "can't override final member '{}'".format(member_name)
                    raise TypeError(error)

                if isinstance(member, property):
                    is_final = getattr(member.fget, FINAL_METHOD_TAG, False) is True
                elif isinstance(member, (staticmethod, classmethod)):
                    is_final = getattr(member.__func__, FINAL_METHOD_TAG, False) is True
                else:
                    is_final = getattr(member, FINAL_METHOD_TAG, False) is True

                if is_final:
                    final_method_names.add(member_name)

    def __repr__(cls):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        module = cls.__module__
        name = cls.__fullname__
        return "<class{space}{quote}{module}{name}{quote}>".format(
            space=" " if module or name else "",
            quote="'" if module or name else "",
            module=module + "." if module else "",
            name=name if name else "",
        )

    def __dir__(cls):
        # type: () -> List[str]
        """Get a simplified list of member names."""
        member_names = set()  # type: Set[str]
        for base in reversed(getmro(type(cls))):
            if base is object or base is type:
                continue
            member_names.update(_simplified_member_names(base.__dict__))
        for base in reversed(getmro(cls)):
            if base is object or base is type:
                continue
            member_names.update(_simplified_member_names(base.__dict__))
        return sorted(member_names)
    #
    # def __setattr__(cls, name, value):
    #     if not hasattr(SlottedABC, name):
    #         error = "'{}' class attributes are read-only".format(cls.__name__)
    #         raise AttributeError(error)
    #     super(BaseMeta, cls).__setattr__(name, value)
    #
    # def __delattr__(cls, name):
    #     if not hasattr(SlottedABC, name):
    #         error = "'{}' class attributes are read-only".format(cls.__name__)
    #         raise AttributeError(error)
    #     super(BaseMeta, cls).__delattr__(name)

    @property
    @final
    def __fullname__(cls):
        # type: () -> Optional[str]
        """Qualified class name if possible, fall back to class name otherwise."""
        try:
            name = qualname(cls)
            if not name:
                raise AttributeError()
        except AttributeError:
            name = cls.__name__
        return name


class Base(with_metaclass(BaseMeta, SlottedABC)):
    """Base class."""
    __slots__ = (INITIALIZING_TAG,)

    def __copy__(self):
        """Prevents shallow copy by default."""
        error = "'{}' object can't be shallow copied".format(type(self).__fullname__)
        raise RuntimeError(error)

    def __ne__(self, other):
        """Compare with another object for inequality."""
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def __dir__(self):
        # type: () -> List[str]
        """Get a simplified list of member names."""
        member_names = set()  # type: Set[str]
        for base in reversed(getmro(type(self))):
            if base is object or base is type:
                continue
            member_names.update(_simplified_member_names(base.__dict__))
        return sorted(member_names)


class ProtectedBase(Base):
    """Protected base class."""
    __slots__ = ()

    def __setattr__(self, name, value):
        if not getattr(self, INITIALIZING_TAG, False) and not name.startswith("_"):
            error = "read-only object"
            raise AttributeError(error)
        super(ProtectedBase, self).__setattr__(name, value)

    def __delattr__(self, name):
        if not getattr(self, INITIALIZING_TAG, False) and not name.startswith("_"):
            error = "read-only object"
            raise AttributeError(error)
        super(ProtectedBase, self).__delattr__(name)
