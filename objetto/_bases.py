# -*- coding: utf-8 -*-
"""Base class and metaclass."""

from weakref import WeakKeyDictionary, WeakValueDictionary
from inspect import getmro
from contextlib import contextmanager
from uuid import uuid4
from typing import TYPE_CHECKING, final, cast

from qualname import qualname  # type: ignore
from decorator import decorator
from six import with_metaclass, iteritems
from slotted import SlottedABCMeta, SlottedABC

from .utils.immutable import ImmutableSet

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        TypeVar,
        Iterator,
        Set,
        Optional,
        Type,
        List,
        Iterable,
        Mapping,
        MutableMapping,
    )

    _T = TypeVar("_T")
    AbstractType = Type["AbstractMember"]
else:
    AbstractType = None

__all__ = [
    "ABSTRACT_TAG",
    "FINAL_CLASS_TAG",
    "FINAL_METHOD_TAG",
    "INITIALIZING_TAG",
    "final",
    "init_context",
    "init",
    "simplify_member_names",
    "make_base_cls",
    "BaseMeta",
    "Base",
    "ProtectedBase",
    "abstract_member",
    "AbstractType",
]


ABSTRACT_TAG = "__isabstractmethod__"
FINAL_CLASS_TAG = "__isfinalclass__"
FINAL_METHOD_TAG = "__isfinalmethod__"
INITIALIZING_TAG = "__isinitializing__"

__final = final
__base_cls_cache = WeakValueDictionary()  # type: MutableMapping[str, Type[Base]]


def _final(obj):
    # type: (_T) -> _T
    """
    Final decorator that enables runtime checking for :class:`Base` classes.

    .. code:: python

        >>> from objetto.bases import Base, final

        >>> @final
        ... class FinalClass(Base):  # final class
        ...     pass
        ...

        >>> class Class(Base):
        ...     @final
        ...     def final_method(self):  # final method
        ...         pass
        ...

    :param obj: Method or class.
    :return: Decorated method or class.
    """
    if isinstance(obj, type):
        type.__setattr__(obj, FINAL_CLASS_TAG, True)
    else:
        object.__setattr__(cast(object, obj), FINAL_METHOD_TAG, True)
    return __final(obj)


# Replace typing.final with our custom decorator for runtime checking.
globals()["final"] = _final


def simplify_member_names(names):
    # type: (Iterable[str]) -> Iterator[str]
    """
    Iterate over member names and only yield the simplified ones.

    :param names: Input names.
    :return: Simplified names iterator.
    """
    return (n for n in names if not ("__" in n and n.startswith("_")))


@contextmanager
def init_context(obj):
    # type: (Base) -> Iterator
    """
    Context manager that sets the initializing tag for :class:`Base` objects.

    :param obj: Instance of :class:`Base`.
    :return: Context manager.
    """
    previous = getattr(obj, INITIALIZING_TAG, False)
    object.__setattr__(obj, INITIALIZING_TAG, True)
    try:
        yield
    finally:
        object.__setattr__(obj, INITIALIZING_TAG, previous)


@decorator
def init(func, *args, **kwargs):
    # type: (_T, Any, Any) -> _T
    """
    Method decorator that sets the initializing tag for :class:`Base` objects.

    :param func: Method function.
    :return: Decorated method function.
    """
    self = args[0]
    with init_context(self):
        result = func(*args, **kwargs)
    return result


def _make_base_cls(
    base=None,  # type: Optional[Type[Base]]
    qual_name=None,  # type: Optional[str]
    module=None,  # type: Optional[str]
    dct=None,  # type: Optional[Mapping[str, Any]]
    uuid=None,  # type: Optional[str]
):
    # type: (...) -> Type[Base]
    """
    Make a subclass of :class:`Base` on the fly.

    :param base: Base class.
    :param qual_name: Qualified name.
    :param module: Module.
    :param dct: Members dictionary.
    :param uuid: UUID used for caching.
    :return: Generated subclass.
    """

    # Get base.
    if base is None:
        base = Base

    # Get name.
    qual_name = qual_name or base.__fullname__
    name = qual_name.split(".")[-1]

    # Get module.
    module = module or base.__module__

    # Get metaclass and uuid.
    mcs = type(base)
    uuid = str(uuid4()) if uuid is None else uuid

    # Copy dct.
    dct_copy = dict(dct or {})  # type: Dict[str, Any]

    # Define reduce method for pickling instances of the subclass.
    def __reduce__(self):
        state = self.__getstate__()
        return _make_base_instance, (base, qual_name, module, state, dct_copy, uuid)

    # Assemble class dict by copying dct once again.
    cls_dct = dct_copy.copy()  # type: Dict[str, Any]
    cls_dct_update = {
        "__reduce__": __reduce__,
        "__qualname__": qual_name,
        "__module__": module,
    }  # type: Dict[str, Any]
    cls_dct.update(cls_dct_update)

    # Make new subclass and cache it by UUID.
    cls = __base_cls_cache[uuid] = cast("BaseMeta", mcs)(name, (base,), cls_dct)
    return cls


def _make_base_instance(
    base=None,  # type: Optional[Type[Base]]
    qual_name=None,  # type: Optional[str]
    module=None,  # type: Optional[str]
    state=None,  # type: Optional[Dict[str, Any]]
    dct=None,  # type: Optional[Mapping[str, Any]]
    uuid=None,  # type: Optional[str]
):
    # type: (...) -> Base
    """
    Make an instance of a subclass of :class:`Base` on the fly.

    :param base: Base class.
    :param qual_name: Qualified name.
    :param module: Module.
    :param state: Pickled state.
    :param dct: Members dictionary.
    :param uuid: UUID used for caching.
    :return: Generated instance.
    """

    # Try to get class from cache using UUID.
    try:
        if uuid is None:
            raise KeyError()
        cls = __base_cls_cache[uuid]

    # Not cached, make a new subclass and use it.
    except KeyError:
        cls = _make_base_cls(
            base=base,
            qual_name=qual_name,
            module=module,
            dct=dct,
            uuid=uuid,
        )

    # Make new instance and unpickle its state.
    self = cast("Base", cls.__new__(cls))
    self.__setstate__(state)

    return self


def make_base_cls(
    base=None,  # type: Optional[Type[Base]]
    qual_name=None,  # type: Optional[str]
    module=None,  # type: Optional[str]
    dct=None,  # type: Optional[Mapping[str, Any]]
):
    # type: (...) -> Type[Base]
    """
    Make a subclass of :class:`Base` on the fly.

    :param base: Base class.
    :param qual_name: Qualified name.
    :param module: Module.
    :param dct: Members dictionary.
    :return: Generated subclass.
    """
    return _make_base_cls(base, qual_name, module, dct=dct)


class BaseMeta(SlottedABCMeta):
    """
    Metaclass for :class:`Base`.

      - Forces the use of `__slots__`.
      - Forces `__hash__` to be declared if `__eq__` was declared.
      - Decorates `__init__` methods to update the initializing tag.
      - Prevents class attributes owned by :class:`BaseMeta` bases from being changed.
      - Runtime checking for `final` decorated classes/methods.
    """

    __open_attributes = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[Type, ImmutableSet[str]]

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
        required_bases = list(reversed(getmro(SlottedABC)))  # type: List[Type]
        seen_bases = []  # type: List[Type]
        open_attributes = set()  # type: Set[str]
        for base in reversed(getmro(cls)):

            # Check bases for valid resolution order.
            expected_base = seen_bases[-1] if seen_bases else object
            if not issubclass(base, expected_base):
                error = (
                    "invalid resolution order when defining '{}'; "
                    "base '{}' does not inherit from '{}'"
                ).format(
                    name, base.__name__, expected_base.__name__
                )
                raise TypeError(error)
            elif required_bases and base is required_bases[-1]:
                seen_bases.append(required_bases.pop())

            # Get open class attributes if non-Base, start requiring Base otherwise.
            if not isinstance(base, BaseMeta):
                open_attributes.update(base.__dict__)
            elif not required_bases:
                required_bases.append(base)

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

        # Store open class attributes.
        type(cls).__open_attributes[cls] = ImmutableSet(open_attributes)

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
        """
        Get a simplified list of member names.

        :return: List of member names.
        """
        member_names = set()  # type: Set[str]
        for base in reversed(getmro(type(cls))):
            if base is object or base is type:
                continue
            member_names.update(simplify_member_names(base.__dict__))
        for base in reversed(getmro(cls)):
            if base is object or base is type:
                continue
            member_names.update(simplify_member_names(base.__dict__))
        return sorted(member_names)

    def __setattr__(cls, name, value):
        # type: (str, Any) -> None
        """
        Set class attribute.

        :param name: Name.
        :param value: Value.
        :raises AttributeError: Read-only attribute.
        """
        open_attributes = type(cls).__open_attributes.get(cls)
        if open_attributes is not None and name not in open_attributes:
            error = "class attribute '{}' is read-only".format(name)
            raise AttributeError(error)
        super(BaseMeta, cls).__setattr__(name, value)

    def __delattr__(cls, name):
        # type: (str) -> None
        """
        Delete class attribute.

        :param name: Name.
        :raises AttributeError: Read-only attribute.
        """
        open_attributes = type(cls).__open_attributes.get(cls)
        if open_attributes is not None and name not in open_attributes:
            error = "class attribute '{}' is read-only".format(name)
            raise AttributeError(error)
        super(BaseMeta, cls).__delattr__(name)

    @property
    @final
    def __fullname__(cls):
        # type: () -> Optional[str]
        """
        Get qualified class name if possible, fall back to class name otherwise.

        :return: Full class name.
        """
        try:
            name = qualname(cls)
            if not name:
                raise AttributeError()
        except AttributeError:
            name = cls.__name__
        return name


class Base(with_metaclass(BaseMeta, SlottedABC)):
    """
    Base class.

      - Forces the use of `__slots__`.
      - Forces `__hash__` to be declared if `__eq__` was declared.
      - Property that tells whether instance is initializing or not.
      - Default implementation of `__copy__` raises an error.
      - Default implementation of `__ne__` returns the opposite of `__eq__`.
      - Prevents class attributes owned by :class:`BaseMeta` bases from being changed.
      - Runtime checking for `final` decorated classes/methods.
      - Simplified `__dir__` result that shows only relevant members for client code.
    """

    __slots__ = (INITIALIZING_TAG,)

    def __copy__(self):
        # type: () -> None
        """
        Prevents shallow copy by default.

        :raises RuntimeError: Always raised.
        """
        error = "'{}' object can't be shallow copied".format(type(self).__fullname__)
        raise RuntimeError(error)

    def __ne__(self, other):
        # type: (Any) -> bool
        """
        Compare with another object for inequality.

        :param other: Another object.
        :return: True if not equal.
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def __dir__(self):
        # type: () -> List[str]
        """
        Get a simplified list of member names.

        :return: List of member names.
        """
        member_names = set()  # type: Set[str]
        for base in reversed(getmro(type(self))):
            if base is object or base is type:
                continue
            member_names.update(simplify_member_names(base.__dict__))
        return sorted(member_names)


class ProtectedBase(Base):
    """
    Protected base class.

      - Prevents setting public instance attributes when not initializing.
    """
    __slots__ = ()

    def __setattr__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute.

        :param name: Name.
        :param value: Value.
        :raises AttributeError: Read-only attribute.
        """
        if not getattr(self, INITIALIZING_TAG, False) and not name.startswith("_"):
            error = "attribute '{}' is read-only".format(name)
            raise AttributeError(error)
        super(ProtectedBase, self).__setattr__(name, value)

    def __delattr__(self, name):
        # type: (str) -> None
        """
        Set attribute.

        :param name: Name.
        :raises AttributeError: Read-only attribute.
        """
        if not getattr(self, INITIALIZING_TAG, False) and not name.startswith("_"):
            error = "attribute '{}' is read-only".format(name)
            raise AttributeError(error)
        super(ProtectedBase, self).__delattr__(name)


@final
class AbstractMemberMeta(BaseMeta):
    """Metaclass for :class:`AbstractMember`."""

    @staticmethod
    def __new__(mcs, name, bases, dct):
        """Make :class:`AbstractMember` class."""
        dct[ABSTRACT_TAG] = True
        return super(AbstractMemberMeta, mcs).__new__(mcs, name, bases, dct)


@final
class AbstractMember(with_metaclass(AbstractMemberMeta, Base)):
    """Abstract member for classes."""

    __slots__ = ()

    @staticmethod
    def __new__(cls, *args, **kwargs):
        """
        Prevent instantiation.

        :raises TypeError: Always raised.
        """
        error = "'{}' can't be instantiated".format(cls.__name__)
        raise TypeError(error)

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return "<abstract>"

    def __str__(self):
        # type: () -> str
        """
        Get string representation.

        :return: String representation.
        """
        return self.__repr__()


def abstract_member():
    """
    Used to indicate an abstract attribute member in a class.

    .. code:: python

        >>> from objetto.bases import Base, abstract_member

        >>> class AbstractClass(Base):
        ...     some_attribute = abstract_member()  # abstract
        ...
        >>> obj = AbstractClass()
        Traceback (most recent call last):
        TypeError: Can't instantiate abstract class AbstractClass with abstract \
methods some_attribute

        >>> class ConcreteClass(AbstractClass):
        ...     some_attribute = (1, 2, 3)  # concrete
        >>> obj = ConcreteClass()

    :return: Abstract member.
    """
    return AbstractMember
