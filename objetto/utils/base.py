# -*- coding: utf-8 -*-
"""
Classes & metaclasses that offer validation, compatibility, and protection features:
  - Forced explicit declaration of `__hash__` method when `__eq__` method is declared.
  - Prevention of class members overlapping class properties defined in the metaclass.
  - Runtime-checked version of the `typing.final` decorator.
  - Mocked version of `typing.Generic` which works around metaclass issue for python 2.
  - Locked/immutable class attributes after class initialization.
  - Private & dedicated `__namespace__` member for every subclass.
  - Backport of `__qualname__` functionality through the `__fullname__` class property.
  - Pickle-compatible `__reduce__` method that leverages `__fullname__`.
  - Backport of default `__ne__` behavior (negates the result of `__eq__`).
"""

from inspect import getmro
from threading import RLock
from contextlib import contextmanager
from weakref import WeakSet
from typing import TYPE_CHECKING
from typing import Generic as GenericBase
try:
    from typing import final
except ImportError:
    final = lambda f: f

from slotted import SlottedABCMeta, SlottedABC
from decorator import decorator
from six import with_metaclass, iteritems
from qualname import qualname  # type: ignore

from .lazy_import import lazy_import, get_import_path
from .namespace import Namespace

if TYPE_CHECKING:
    from typing import Any, Dict, Type, Optional, Set, Iterator

__all__ = [
    "BaseMeta", "Base", "GenericBaseMeta", "GenericBase", "final", "unlock_context"
]


_FINAL_CLASS_TAG = "__isfinalclass__"
_FINAL_METHOD_TAG = "__isfinalmethod__"
_ABC_PREFIX = "_abc_"


# Replace `typing.final` with custom decorator to enable runtime checking.
__final = final


def _final(obj):
    if isinstance(obj, type):
        type.__setattr__(obj, _FINAL_CLASS_TAG, True)
        return __final(obj)
    else:

        @decorator
        def final_decorator(obj_, *args, **kwargs):
            return obj_(*args, **kwargs)

        decorated = final_decorator(obj)
        object.__setattr__(decorated, _FINAL_METHOD_TAG, True)
        return __final(decorated)


globals()["final"] = _final


# Keep track of locked bases.
_locked_bases_lock = RLock()
_locked_bases = WeakSet()  # type: WeakSet[BaseMeta]


@contextmanager
def unlock_context(cls):
    # type: (BaseMeta) -> Iterator
    with _locked_bases_lock:
        locked = cls in _locked_bases
        _locked_bases.discard(cls)
        try:
            yield
        finally:
            if locked:
                _locked_bases.add(cls)


class BaseMeta(SlottedABCMeta):
    """Metaclass for :class:Base."""

    @staticmethod
    def __new__(mcs, name, bases, dct, **kwargs):

        # Prevent members with '_abc_' prefix from being declared.
        for member_name in dct:
            if member_name.startswith(_ABC_PREFIX):
                error = (
                    "can't have class member '{}.{}' prefixed with '{}'"
                ).format(name, member_name, _ABC_PREFIX)
                raise TypeError(error)

        with _locked_bases_lock:

            # noinspection PyArgumentList
            cls = super(BaseMeta, mcs).__new__(mcs, name, bases, dct, **kwargs)

            # Force '__hash__' to be declared when '__eq__' is declared (be explicit).
            if "__eq__" in cls.__dict__ and "__hash__" not in dct:
                error = (
                    "declared '__eq__' in '{}', but didn't declare '__hash__'"
                ).format(name)
                raise TypeError(error)

            # Create new namespace private to this class only.
            cls.__namespace = Namespace()

            # Lock class members.
            _locked_bases.add(cls)

        return cls

    def __init__(cls, name, bases, dct, **kwargs):

        # noinspection PyArgumentList
        super(BaseMeta, cls).__init__(name, bases, dct, **kwargs)

        # Iterate over mro.
        mcs = type(cls)
        final_method_names = set()  # type: Set[str]
        final_cls = None  # type: Optional[Type]
        for base in reversed(getmro(cls)):

            # Prevent subclassing final classes.
            if getattr(base, _FINAL_CLASS_TAG, False) is True:
                if final_cls is not None:
                    error = "can't subclass final class '{}'".format(final_cls.__name__)
                    raise TypeError(error)
                final_cls = base

            # Prevent overriding final members and class properties.
            for member_name, member in iteritems(base.__dict__):

                # Can't override final methods.
                if member_name in final_method_names:
                    error = "can't override final member '{}'".format(member_name)
                    raise TypeError(error)

                # Can't have name overlap with class property defined in the metaclass.
                if hasattr(mcs, member_name):
                    if isinstance(getattr(mcs, member_name), property):
                        error = "member name overlap with class property '{}'".format(
                            member_name
                        )
                        raise TypeError(error)

                # Is a descriptor and has the final method tag directly on it.
                is_descriptor = hasattr(member, "__get__")
                if is_descriptor and getattr(member, _FINAL_METHOD_TAG, False):
                    is_final = True

                # Is a descriptor and has a 'fget' getter (property-like).
                elif is_descriptor and hasattr(member, "fget"):
                    is_final = getattr(member.fget, _FINAL_METHOD_TAG, False) is True

                # Is a static or class method.
                elif isinstance(member, (staticmethod, classmethod)):
                    is_final = getattr(
                        member.__func__, _FINAL_METHOD_TAG, False
                    ) is True

                # Is a method.
                elif callable(member):
                    is_final = getattr(member, _FINAL_METHOD_TAG, False) is True

                # None of the above, can't be runtime checked for final.
                else:
                    is_final = False

                if is_final:
                    final_method_names.add(member_name)

    def __repr__(cls):
        # type: () -> str
        module = cls.__module__
        name = cls.__fullname__
        return "<class{space}{quote}{module}{name}{quote}>".format(
            space=" " if module or name else "",
            quote="'" if module or name else "",
            module=module + "." if module else "",
            name=name if name else "",
        )

    def __setattr__(cls, name, value):
        # type: (str, Any) -> None
        with _locked_bases_lock:
            if cls not in _locked_bases or name.startswith(_ABC_PREFIX):
                super(BaseMeta, cls).__setattr__(name, value)
            else:
                error = (
                    "can't change '{}' member after class '{}' has been defined"
                ).format(name, cls.__fullname__)
                raise AttributeError(error)

    def __delattr__(cls, name):
        # type: (str) -> None
        with _locked_bases_lock:
            if cls not in _locked_bases or name.startswith(_ABC_PREFIX):
                super(BaseMeta, cls).__delattr__(name)
            else:
                error = (
                    "can't delete '{}' member after class '{}' has been defined"
                ).format(name, cls.__fullname__)
                raise AttributeError(error)

    @property
    @final
    def __fullname__(cls):
        # type: () -> str
        try:
            name = qualname(cls)
            if not name:
                raise AttributeError()
        except AttributeError:
            name = cls.__name__
        return name

    @property
    @final
    def __namespace__(cls):
        # type: () -> Namespace
        return cls.__namespace  # type: ignore


class Base(with_metaclass(BaseMeta, SlottedABC)):

    __slots__ = ()

    def __repr__(self):
        # type: () -> str
        return "<{} at {}>".format(type(self).__fullname__, hex(id(self)))

    def __str__(self):
        # type: () -> str
        return self.__repr__()

    def __hash__(self):
        return object.__hash__(self)

    def __eq__(self, other):
        # type: (object) -> bool
        return self is other

    def __ne__(self, other):
        # type: (object) -> bool
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def __reduce__(self):
        return _base_reducer, (get_import_path(type(self)), self.__getstate__())


def _base_reducer(import_path, state):
    # type: (str, Dict[str, Any]) -> Base
    cls = lazy_import(import_path)
    obj = cls.__new__(cls)
    obj.__setstate__(state)
    return obj


GenericBaseMeta = type


class _GenericBaseMeta(BaseMeta):

    def __getitem__(cls, _):
        return cls


class _GenericBase(with_metaclass(_GenericBaseMeta, Base)):
    __slots__ = ()


globals()["GenericBaseMeta"] = _GenericBaseMeta
globals()["GenericBase"] = _GenericBase
