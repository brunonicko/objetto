# -*- coding: utf-8 -*-
"""Base classes and metaclasses."""

from abc import abstractmethod
from contextlib import contextmanager
from inspect import getmro
from typing import TYPE_CHECKING, Callable, Generic, TypeVar, cast, final, overload
from uuid import uuid4
from weakref import WeakKeyDictionary, WeakValueDictionary

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from decorator import decorator
from qualname import qualname  # type: ignore
from six import iteritems, with_metaclass
from slotted import (
    SlottedABC,
    SlottedABCMeta,
    SlottedContainer,
    SlottedHashable,
    SlottedIterable,
    SlottedMapping,
    SlottedMutableMapping,
    SlottedMutableSequence,
    SlottedMutableSet,
    SlottedSequence,
    SlottedSet,
    SlottedSized,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        FrozenSet,
        ItemsView,
        Iterable,
        Iterator,
        KeysView,
        List,
        Mapping,
        MutableMapping,
        MutableSequence,
        Optional,
        Sequence,
        Set,
        AbstractSet,
        Tuple,
        Type,
        Union,
        ValuesView,
    )

__all__ = [
    "MISSING",
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
    "abstract_member",
    "BaseHashable",
    "BaseSized",
    "BaseIterable",
    "BaseContainer",
    "BaseCollection",
    "BaseProtectedCollection",
    "BaseInteractiveCollection",
    "BaseMutableCollection",
    "BaseDict",
    "BaseProtectedDict",
    "BaseInteractiveDict",
    "BaseMutableDict",
    "BaseList",
    "BaseProtectedList",
    "BaseInteractiveList",
    "BaseMutableList",
    "BaseSet",
    "BaseProtectedSet",
    "BaseInteractiveSet",
    "BaseMutableSet",
]

F = TypeVar("F", bound=Callable)  # Callable type.
T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.
T_co = TypeVar("T_co", covariant=True)  # Any type covariant containers.
VT_co = TypeVar("VT_co", covariant=True)  # Value type covariant containers.

MISSING = object()
ABSTRACT_TAG = "__isabstractmethod__"
FINAL_CLASS_TAG = "__isfinalclass__"
FINAL_METHOD_TAG = "__isfinalmethod__"
INITIALIZING_TAG = "__isinitializing__"

__final = final
__base_cls_cache = WeakValueDictionary()  # type: MutableMapping[str, Type[Base]]


def _final(obj):
    # type: (F) -> F
    """
    Decorator based on :func:`typing.final` that enables runtime checking for
    :class:`Base` classes.

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
    # type: (F, Any, Any) -> F
    """
    Method decorator that sets the initializing tag for :class:`Base` objects.

    :param func: Method function.
    :return: Decorated method function.
    """
    self = args[0]
    with init_context(self):
        result = func(*args, **kwargs)
    return result


# noinspection PyTypeChecker
_B = TypeVar("_B", bound="Base")


def _make_base_cls(
    base=None,  # type: Optional[Type[_B]]
    qual_name=None,  # type: Optional[str]
    module=None,  # type: Optional[str]
    dct=None,  # type: Optional[Mapping[str, Any]]
    uuid=None,  # type: Optional[str]
):
    # type: (...) -> Type[_B]
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
        _base = Base
    else:
        _base = cast("Type[_B]", base)

    # Get name.
    qual_name = qual_name or _base.__fullname__ or _base.__name__ or ""
    name = qual_name.split(".")[-1]

    # Get module.
    module = module or _base.__module__

    # Get metaclass and uuid.
    mcs = type(_base)
    uuid = str(uuid4()) if uuid is None else uuid

    # Copy dct.
    dct_copy = dict(dct or {})  # type: Dict[str, Any]

    # Define reduce method for pickling instances of the subclass.
    def __reduce__(self):
        state = self.__getstate__()
        return _make_base_instance, (_base, qual_name, module, state, dct_copy, uuid)

    # Assemble class dict by copying dct once again.
    cls_dct = dct_copy.copy()  # type: Dict[str, Any]
    cls_dct_update = {
        "__reduce__": __reduce__,
        "__qualname__": qual_name,
        "__module__": module,
    }  # type: Dict[str, Any]
    cls_dct.update(cls_dct_update)

    # Make new subclass and cache it by UUID.
    cls = __base_cls_cache[uuid] = cast("BaseMeta", mcs)(name, (_base,), cls_dct)
    return cls


def _make_base_instance(
    base=None,  # type: Optional[Type[_B]]
    qual_name=None,  # type: Optional[str]
    module=None,  # type: Optional[str]
    state=None,  # type: Optional[Dict[str, Any]]
    dct=None,  # type: Optional[Mapping[str, Any]]
    uuid=None,  # type: Optional[str]
):
    # type: (...) -> _B
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
    self = cast("_B", cls.__new__(cls))
    self.__setstate__(state or {})

    return self


def make_base_cls(
    base=None,  # type: Optional[Type[_B]]
    qual_name=None,  # type: Optional[str]
    module=None,  # type: Optional[str]
    dct=None,  # type: Optional[Mapping[str, Any]]
):
    # type: (...) -> Type[_B]
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
    )  # type: MutableMapping[Type, FrozenSet[str]]

    @staticmethod
    def __new__(mcs, name, bases, dct):
        """Make :class:`BaseMeta` class."""
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
                ).format(name, base.__name__, expected_base.__name__)
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
        type(cls).__open_attributes[cls] = frozenset(open_attributes)

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

    @final
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

    @final
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
        # type: () -> str
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
        # type: () -> Any
        """
        Prevents shallow copy by default.

        :raises RuntimeError: Always raised.
        """
        error = "'{}' object can't be shallow copied".format(type(self).__fullname__)
        raise RuntimeError(error)

    @final
    def __ne__(self, other):
        # type: (object) -> bool
        """
        Compare for inequality.

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
    # type: () -> Type[AbstractMember]
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


class BaseHashable(Base, SlottedHashable):
    """
    Base hashable.

      - Forces implementation of `__hash__` method.
    """

    __slots__ = ()

    @abstractmethod
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()


class BaseSized(Base, SlottedSized):
    """
    Base sized.

      - Has a length (count).
    """

    __slots__ = ()

    @abstractmethod
    def __len__(self):
        # type: () -> int
        """
        Get count.

        :return: Count.
        """
        raise NotImplementedError()


class BaseIterable(Base, SlottedIterable, Generic[T_co]):
    """
    Base iterable.

      - Can be iterated over.
    """

    __slots__ = ()

    @abstractmethod
    def __iter__(self):
        # type: () -> Iterator
        """
        Iterate over.

        :return: Iterator.
        """
        raise NotImplementedError()


class BaseContainer(Base, SlottedContainer, Generic[T_co]):
    """
    Base container.

      - Contains values.
    """

    __slots__ = ()

    @abstractmethod
    def __contains__(self, content):
        # type: (Any) -> bool
        """
        Get whether content is present.

        :param content: Content.
        :return: True if contains.
        """
        raise NotImplementedError()


class BaseCollection(BaseSized, BaseIterable[T_co], BaseContainer[T_co]):
    """
    Base collection.

      - Has a length (count).
      - Can be iterated over.
      - Contains values.
    """

    __slots__ = ()

    @abstractmethod
    def find_with_attributes(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.
        :return: Value.
        :raises ValueError: No attributes provided or no match found.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BPC = TypeVar("_BPC", bound="BaseProtectedCollection")


class BaseProtectedCollection(BaseCollection[T]):
    """
    Base protected collection.

      - Has protected transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()

    @abstractmethod
    def _clear(self):
        # type: (_BPC) -> _BPC
        """
        Clear.

        :return: Transformed.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BIC = TypeVar("_BIC", bound="BaseInteractiveCollection")


# noinspection PyAbstractClass
class BaseInteractiveCollection(BaseProtectedCollection[T]):
    """
    Base interactive collection.

      - Has public transformation methods.
      - Transformations return a transformed version (immutable) or self (mutable).
    """

    __slots__ = ()

    @final
    def clear(self):
        # type: (_BIC) -> _BIC
        """
        Clear.

        :return: Transformed.
        """
        return self._clear()


# noinspection PyAbstractClass
class BaseMutableCollection(BaseProtectedCollection[T]):
    """
    Base mutable collection.

      - Has public mutable transformation and magic methods.
      - Transformations return self (mutable).
    """

    __slots__ = ()

    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()


class BaseDict(BaseCollection[KT], SlottedMapping, Generic[KT, VT_co]):
    """Base dictionary collection."""

    __slots__ = ()

    @abstractmethod
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    @abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()

    @abstractmethod
    def __reversed__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        """
        raise NotImplementedError()

    @abstractmethod
    def __getitem__(self, key):
        # type: (KT) -> VT_co
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Key is not present.
        """
        raise NotImplementedError()

    @abstractmethod
    def get(self, key, fallback=None):
        # type: (KT, Any) -> Union[VT_co, Any]
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        raise NotImplementedError()

    @abstractmethod
    def iteritems(self):
        # type: () -> Iterator[Tuple[KT, VT_co]]
        """
        Iterate over items.

        :return: Items iterator.
        """
        raise NotImplementedError()

    @abstractmethod
    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        raise NotImplementedError()

    @abstractmethod
    def itervalues(self):
        # type: () -> Iterator[VT_co]
        """
        Iterate over values.

        :return: Values iterator.
        """
        raise NotImplementedError()

    @abstractmethod
    def items(self):
        # type: () -> ItemsView[KT, VT_co]
        """
        Get items.

        :return: Items.
        """
        raise NotImplementedError()

    @abstractmethod
    def keys(self):
        # type: () -> KeysView[KT]
        """
        Get keys.

        :return: Keys.
        """
        raise NotImplementedError()

    @abstractmethod
    def values(self):
        # type: () -> ValuesView[VT_co]
        """
        Get values.

        :return: Values.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BPD = TypeVar("_BPD", bound="BaseProtectedDict")


class BaseProtectedDict(BaseDict[KT, VT], BaseProtectedCollection[KT]):
    """Base protected dictionary collection."""

    __slots__ = ()

    @abstractmethod
    def _discard(self, key):
        # type: (_BPD, KT) -> _BPD
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abstractmethod
    def _remove(self, key):
        # type: (_BPD, KT) -> _BPD
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        raise NotImplementedError()

    @abstractmethod
    def _set(self, key, value):
        # type: (_BPD, KT, VT) -> _BPD
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        raise NotImplementedError()

    @overload
    @abstractmethod
    def _update(self, __m, **kwargs):
        # type: (_BPD, Mapping[KT, VT], VT) -> _BPD
        pass

    @overload
    @abstractmethod
    def _update(self, __m, **kwargs):
        # type: (_BPD, Iterable[Tuple[KT, VT]], VT) -> _BPD
        pass

    @overload
    @abstractmethod
    def _update(self, **kwargs):
        # type: (_BPD, VT) -> _BPD
        pass

    @abstractmethod
    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BID = TypeVar("_BID", bound="BaseInteractiveDict")


# noinspection PyAbstractClass
class BaseInteractiveDict(BaseProtectedDict[KT, VT], BaseInteractiveCollection[KT]):
    """Base interactive dictionary collection."""

    __slots__ = ()

    @final
    def discard(self, key):
        # type: (_BID, KT) -> _BID
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        return self._discard(key)

    @final
    def remove(self, key):
        # type: (_BID, KT) -> _BID
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._remove(key)

    @final
    def set(self, key, value):
        # type: (_BID, KT, VT) -> _BID
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        return self._set(key, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (_BID, Mapping[KT, VT], VT) -> _BID
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (_BID, Iterable[Tuple[KT, VT]], VT) -> _BID
        pass

    @overload
    def update(self, **kwargs):
        # type: (_BID, VT) -> _BID
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        return self._update(*args, **kwargs)


class BaseMutableDict(
    SlottedMutableMapping, BaseProtectedDict[KT, VT], BaseMutableCollection[KT]
):
    """Base mutable dictionary collection."""

    __slots__ = ()

    @abstractmethod
    def __setitem__(self, key, value):
        # type: (KT, VT) -> None
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        """
        raise NotImplementedError()

    @abstractmethod
    def __delitem__(self, key):
        # type: (KT) -> None
        """
        Delete key.

        :param key: Key.
        :raises KeyError: Key is not preset.
        """
        raise NotImplementedError()

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()

    @abstractmethod
    def pop(self, key, fallback=MISSING):
        # type: (KT, Any) -> Union[VT, Any]
        """
        Get value for key and remove it, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        :raises KeyError: Key is not present and fallback value not provided.
        """
        raise NotImplementedError()

    @abstractmethod
    def popitem(self):
        # type: () -> Tuple[KT, VT]
        """
        Get item and discard key.

        :return: Item.
        """
        raise NotImplementedError()

    @abstractmethod
    def setdefault(self, key, default=None):
        # type: (KT, VT) -> VT
        """
        Get the value for the specified key, insert key with default if not present.

        :param key: Key.
        :param default: Default value.
        :return: Existing or default value.
        """
        raise NotImplementedError()

    @final
    def discard(self, key):
        # type: (KT) -> None
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        self._discard(key)

    @final
    def remove(self, key):
        # type: (KT) -> None
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        self._remove(key)

    @final
    def set(self, key, value):
        # type: (KT, VT) -> None
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        self._set(key, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (Mapping[KT, VT], VT) -> None
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (Iterable[Tuple[KT, VT]], VT) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (VT) -> None
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.
        """
        self._update(*args, **kwargs)


class BaseList(BaseCollection[T_co], SlottedSequence):
    """Base list collection."""

    __slots__ = ()

    @abstractmethod
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    @abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()

    @abstractmethod
    def __reversed__(self):
        # type: () -> Iterator[T_co]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        raise NotImplementedError()

    @overload
    @abstractmethod
    def __getitem__(self, index):
        # type: (int) -> T_co
        pass

    @overload
    @abstractmethod
    def __getitem__(self, index):
        # type: (slice) -> Sequence[T_co]
        pass

    @abstractmethod
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        raise NotImplementedError()

    @abstractmethod
    def count(self, value):
        # type: (Any) -> int
        """
        Count number of occurrences of a value.

        :return: Number of occurrences.
        """
        raise NotImplementedError()

    @abstractmethod
    def index(self, value, start=None, stop=None):
        # type: (Any, Optional[int], Optional[int]) -> int
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :return: Index of value.
        :raises ValueError: Provided stop but did not provide start.
        """
        raise NotImplementedError()

    @abstractmethod
    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        raise NotImplementedError()

    @abstractmethod
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BPL = TypeVar("_BPL", bound="BaseProtectedList")


class BaseProtectedList(BaseList[T], BaseProtectedCollection[T]):
    """Base protected list collection."""

    __slots__ = ()

    @abstractmethod
    def _insert(self, index, *values):
        # type: (_BPL, int, T) -> _BPL
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        raise NotImplementedError()

    @abstractmethod
    def _append(self, value):
        # type: (_BPL, T) -> _BPL
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abstractmethod
    def _extend(self, iterable):
        # type: (_BPL, Iterable[T]) -> _BPL
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abstractmethod
    def _remove(self, value):
        # type: (_BPL, T) -> _BPL
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        raise NotImplementedError()

    @abstractmethod
    def _reverse(self):
        # type: (_BPL) -> _BPL
        """
        Reverse values.

        :return: Transformed.
        """
        raise NotImplementedError()

    @abstractmethod
    def _move(self, item, target_index):
        # type: (_BPL, Union[slice, int], int) -> _BPL
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abstractmethod
    def _change(self, index, *values):
        # type: (_BPL, int, T) -> _BPL
        """
        Change value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BIL = TypeVar("_BIL", bound="BaseInteractiveList")


# noinspection PyAbstractClass
class BaseInteractiveList(BaseProtectedList[T], BaseInteractiveCollection[T]):
    """Base interactive list collection."""

    __slots__ = ()

    @final
    def insert(self, index, *values):
        # type: (_BIL, int, T) -> _BIL
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._insert(index, *values)

    @final
    def append(self, value):
        # type: (_BIL, T) -> _BIL
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        return self._append(value)

    @final
    def extend(self, iterable):
        # type: (_BIL, Iterable[T]) -> _BIL
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._extend(iterable)

    @final
    def remove(self, value):
        # type: (_BIL, T) -> _BIL
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return self._remove(value)

    @final
    def reverse(self):
        # type: (_BIL) -> _BIL
        """
        Reverse values.

        :return: Transformed.
        """
        return self._reverse()

    @final
    def move(self, item, target_index):
        # type: (_BPL, Union[slice, int], int) -> _BPL
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        return self._move(item, target_index)

    @final
    def change(self, index, *values):
        # type: (_BIL, int, T) -> _BIL
        """
        Change value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._change(index, *values)


class BaseMutableList(
    SlottedMutableSequence, BaseProtectedList[T], BaseMutableCollection[T]
):
    """Base mutable list collection."""

    __slots__ = ()

    @abstractmethod
    def __iadd__(self, iterable):
        # type: (Iterable[T_co]) -> MutableSequence[T_co]
        """
        In place addition.

        :param iterable: Another iterable.
        :return: Added list.
        """
        raise NotImplementedError()

    @overload
    @abstractmethod
    def __getitem__(self, index):
        # type: (int) -> T_co
        pass

    @overload
    @abstractmethod
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T_co]
        pass

    @abstractmethod
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        raise NotImplementedError()

    @overload
    @abstractmethod
    def __setitem__(self, index, value):
        # type: (int, T) -> None
        pass

    @overload
    @abstractmethod
    def __setitem__(self, slc, values):
        # type: (slice, Iterable[T]) -> None
        pass

    @abstractmethod
    def __setitem__(self, item, value):
        # type: (Union[int, slice], Union[T, Iterable[T]]) -> None
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :raises IndexError: Slice is noncontinuous.
        """
        raise NotImplementedError()

    @overload
    @abstractmethod
    def __delitem__(self, index):
        # type: (int) -> None
        pass

    @overload
    @abstractmethod
    def __delitem__(self, slc):
        # type: (slice) -> None
        pass

    @abstractmethod
    def __delitem__(self, item):
        # type: (Union[int, slice]) -> None
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :raises IndexError: Slice is noncontinuous.
        """
        raise NotImplementedError()

    @abstractmethod
    def pop(self, index=-1):
        # type: (int) -> T
        """
        Pop value from index.

        :param index: Index.
        :return: Value.
        """
        raise NotImplementedError()

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()

    @final
    def insert(self, index, *values):
        # type: (int, T) -> None
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :raises ValueError: No values provided.
        """
        self._insert(index, *values)

    @final
    def append(self, value):
        # type: (T) -> None
        """
        Append value at the end.

        :param value: Value.
        """
        self._append(value)

    @final
    def extend(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        """
        self._extend(iterable)

    @final
    def remove(self, value):
        # type: (T) -> None
        """
        Remove first occurrence of value.

        :param value: Value.
        :raises ValueError: Value is not present.
        """
        self._remove(value)

    @final
    def reverse(self):
        # type: () -> None
        """Reverse values."""
        self._reverse()

    @final
    def move(self, item, target_index):
        # type: (Union[slice, int], int) -> None
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        """
        self._move(item, target_index)

    @final
    def change(self, index, *values):
        # type: (int, T) -> None
        """
        Change value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :raises ValueError: No values provided.
        """
        self._change(index, *values)


class BaseSet(SlottedSet, BaseCollection[T_co], Generic[T_co]):
    """Base set collection."""

    __slots__ = ()

    @abstractmethod
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    @final
    def __le__(self, other):
        # type: (AbstractSet) -> bool
        """
        Less equal operator (self <= other).

        :param other: Another set or any object.
        :return: True if considered less equal.
        """
        if not isinstance(other, collections_abc.Set):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__le__(other)

    @final
    def __lt__(self, other):
        # type: (AbstractSet) -> bool
        """
        Less than operator: `self < other`.

        :param other: Another set or any object.
        :return: True if considered less than.
        """
        if not isinstance(other, collections_abc.Set):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__lt__(other)

    @final
    def __gt__(self, other):
        # type: (AbstractSet) -> bool
        """
        Greater than operator: `self > other`.

        :param other: Another set or any object.
        :return: True if considered greater than.
        """
        if not isinstance(other, collections_abc.Set):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__gt__(other)

    @final
    def __ge__(self, other):
        # type: (AbstractSet) -> bool
        """
        Greater equal operator: `self >= other`.

        :param other: Another set or any object.
        :return: True if considered greater equal.
        """
        if not isinstance(other, collections_abc.Set):
            return NotImplemented
        if type(other) not in (set, frozenset):
            other = set(other)
        return set(self).__ge__(other)

    @final
    def __and__(self, other):
        """
        Get intersection: `self & other`.

        :param other: Iterable or any other object.
        :return: Intersection or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, collections_abc.Iterable):
            return NotImplemented
        return self.intersection(other)

    @final
    def __rand__(self, other):
        """
        Get intersection: `other & self`.

        :param other: Iterable or any other object.
        :return: Intersection or `NotImplemented` if not an iterable.
        """
        return self.__and__(other)

    @final
    def __sub__(self, other):
        """
        Get difference: `self - other`.

        :param other: Iterable or any other object.
        :return: Difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, collections_abc.Iterable):
            return NotImplemented
        return self.difference(other)

    @final
    def __rsub__(self, other):
        """
        Get inverse difference: `other - self`.

        :param other: Iterable or any other object.
        :return: Inverse difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, collections_abc.Iterable):
            return NotImplemented
        return self.inverse_difference(other)

    @final
    def __or__(self, other):
        """
        Get union: `self | other`.

        :param other: Iterable or any other object.
        :return: Union or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, collections_abc.Iterable):
            return NotImplemented
        return self.union(other)

    @final
    def __ror__(self, other):
        """
        Get union: `other | self`.

        :param other: Iterable or any other object.
        :return: Union or `NotImplemented` if not an iterable.
        """
        return self.__or__(other)

    @final
    def __xor__(self, other):
        """
        Get symmetric difference: `self ^ other`.

        :param other: Iterable or any other object.
        :return: Symmetric difference or `NotImplemented` if not an iterable.
        """
        if not isinstance(other, collections_abc.Iterable):
            return NotImplemented
        return self.symmetric_difference(other)

    @final
    def __rxor__(self, other):
        """
        Get symmetric difference: `other ^ self`.

        :param other: Iterable or any other object.
        :return: Symmetric difference or `NotImplemented` if not an iterable.
        """
        return self.__xor__(other)

    @abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _from_iterable(cls, iterable):
        # type: (Iterable) -> BaseSet
        """
        Make set from iterable.

        :param iterable: Iterable.
        :return: Set.
        """
        raise NotImplementedError()

    @abstractmethod
    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    @abstractmethod
    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        raise NotImplementedError()

    @abstractmethod
    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        raise NotImplementedError()

    @abstractmethod
    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        raise NotImplementedError()

    @abstractmethod
    def intersection(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        raise NotImplementedError()

    @abstractmethod
    def symmetric_difference(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        raise NotImplementedError()

    @abstractmethod
    def union(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        raise NotImplementedError()

    @abstractmethod
    def difference(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        raise NotImplementedError()

    @abstractmethod
    def inverse_difference(self, iterable):
        # type: (Iterable) -> BaseSet
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BPS = TypeVar("_BPS", bound="BaseProtectedSet")


class BaseProtectedSet(BaseSet[T], BaseProtectedCollection[T]):
    """Base protected set collection."""

    __slots__ = ()

    @abstractmethod
    def _add(self, value):
        # type: (_BPS, T) -> _BPS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abstractmethod
    def _discard(self, *values):
        # type: (_BPS, T) -> _BPS
        """
        Discard value(s).

        :param value: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        raise NotImplementedError()

    @abstractmethod
    def _remove(self, *values):
        # type: (_BPS, T) -> _BPS
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        raise NotImplementedError()

    @abstractmethod
    def _replace(self, value, new_value):
        # type: (_BPS, T, T) -> _BPS
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :param new_value: New value.
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        raise NotImplementedError()

    @abstractmethod
    def _update(self, iterable):
        # type: (_BPS, Iterable[T]) -> _BPS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BIS = TypeVar("_BIS", bound="BaseInteractiveSet")


# noinspection PyAbstractClass
class BaseInteractiveSet(BaseProtectedSet[T], BaseInteractiveCollection[T]):
    """Base interactive set collection."""

    __slots__ = ()

    @final
    def add(self, value):
        # type: (_BIS, T) -> _BIS
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        return self._add(value)

    @final
    def discard(self, *values):
        # type: (_BIS, T) -> _BIS
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._discard(*values)

    @final
    def remove(self, *values):
        # type: (_BIS, T) -> _BIS
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        return self._remove(*values)

    @final
    def replace(self, value, new_value):
        # type: (_BIS, T, T) -> _BIS
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :param new_value: New value.
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        return self._replace(value, new_value)

    @final
    def update(self, iterable):
        # type: (_BIS, Iterable[T]) -> _BIS
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._update(iterable)


class BaseMutableSet(SlottedMutableSet, BaseProtectedSet[T], BaseMutableCollection[T]):
    """Base mutable set collection."""

    __slots__ = ()

    @final
    def __iand__(self, iterable):
        """
        Intersect in place: `self &= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.intersection_update(iterable)
        return self

    @final
    def __isub__(self, iterable):
        """
        Difference in place: `self -= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.difference(iterable)
        return self

    @final
    def __ior__(self, iterable):
        """
        Update in place: `self |= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        self.update(iterable)
        return self

    @final
    def __ixor__(self, iterable):
        """
        Symmetric difference in place: `self ^= iterable`.

        :param iterable: Iterable.
        :return: This mutable set.
        """
        if iterable is self:
            self.clear()
        else:
            self.symmetric_difference_update(iterable)
        return self

    @abstractmethod
    def pop(self):
        # type: () -> T
        """
        Pop value.

        :return: Value.
        """
        raise NotImplementedError()

    @abstractmethod
    def intersection_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Intersect.

        :param iterable: Iterable.
        """
        raise NotImplementedError()

    @abstractmethod
    def symmetric_difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Symmetric difference.

        :param iterable: Iterable.
        """
        raise NotImplementedError()

    @abstractmethod
    def difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Difference.

        :param iterable: Iterable.
        """
        raise NotImplementedError()

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()

    @final
    def add(self, value):
        # type: (T) -> None
        """
        Add value.

        :param value: Value.
        """
        self._add(value)

    @final
    def discard(self, *values):
        # type: (T) -> None
        """
        Discard value(s).

        :param values: Value(s).
        :raises ValueError: No values provided.
        """
        self._discard(*values)

    @final
    def remove(self, *values):
        # type: (T) -> None
        """
        Remove existing value(s).

        :param values: Value(s).
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        self._remove(*values)

    @final
    def replace(self, value, new_value):
        # type: (T, T) -> None
        """
        Replace existing value with a new one.

        :param value: Existing value.
        :param new_value: New value.
        """
        self._replace(value, new_value)

    @final
    def update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Update with iterable.

        :param iterable: Iterable.
        """
        self._update(iterable)
