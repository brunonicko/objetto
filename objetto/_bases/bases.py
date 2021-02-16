# -*- coding: utf-8 -*-
"""Base classes and metaclasses."""

from abc import abstractmethod
from contextlib import contextmanager
from inspect import getmro
from typing import TYPE_CHECKING, Callable, Generic, Type, TypeVar, cast

try:
    from types import new_class
except ImportError:
    new_class = None  # type: ignore

try:
    from typing import final
except ImportError:
    final = lambda f: f  # type: ignore

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
    SlottedCollection,
    SlottedContainer,
    SlottedHashable,
    SlottedIterable,
    SlottedSized,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        Dict,
        FrozenSet,
        Iterable,
        Iterator,
        List,
        Mapping,
        MutableMapping,
        Optional,
        Set,
        Union,
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
    "AbstractMemberMeta",
    "AbstractMember",
    "abstract_member",
    "Generic",
    "BaseHashable",
    "BaseSized",
    "BaseIterable",
    "BaseContainer",
    "BaseCollection",
    "BaseProtectedCollection",
    "BaseInteractiveCollection",
    "BaseMutableCollection",
]

# noinspection PyTypeChecker
F = TypeVar("F", Callable, Type)  # Callable type.
T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.
T_co = TypeVar("T_co", covariant=True)  # Any type covariant containers.
VT_co = TypeVar("VT_co", covariant=True)  # Value type covariant containers.

MISSING = type("MISSING", (object,), {"__slots__": ()})()
ABSTRACT_TAG = "__isabstractmethod__"
FINAL_CLASS_TAG = "__isfinalclass__"
FINAL_METHOD_TAG = "__isfinalmethod__"
INITIALIZING_TAG = "__isinitializing__"

__final = final
__base_cls_cache = WeakValueDictionary()  # type: MutableMapping[str, Type[Base]]


class _GenericMeta(SlottedABCMeta):
    """Workaround for 'Generic' class having a metaclass in older versions of typing."""

    def __getitem__(cls, _):
        return cls


type.__setattr__(_GenericMeta, "__name__", "SlottedABCMeta")
if hasattr(SlottedABCMeta, "__qualname__"):
    type.__setattr__(_GenericMeta, "__qualname__", "SlottedABCMeta")
type.__setattr__(_GenericMeta, "__module__", SlottedABCMeta.__module__)
try:
    type.__setattr__(_GenericMeta, "__doc__", SlottedABCMeta.__doc__)
except AttributeError:
    pass


class _Generic(with_metaclass(_GenericMeta, SlottedABC)):
    pass


type.__setattr__(_Generic, "__name__", "Generic")
if hasattr(Generic, "__qualname__"):
    type.__setattr__(_Generic, "__qualname__", "Generic")
type.__setattr__(_Generic, "__module__", Generic.__module__)
try:
    type.__setattr__(_Generic, "__doc__", Generic.__doc__)
except AttributeError:
    pass

globals()["SlottedABCMeta"] = _GenericMeta
globals()["Generic"] = _Generic


def _final(obj):
    # type: (F) -> F
    """
    Decorator based on :func:`typing.final` that enables runtime checking for
    :class:`objetto.bases.Base` classes.

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

    :param obj: Method function or class.
    :type obj: function or type

    :return: Decorated method function or class.
    :rtype: function or type
    """
    if isinstance(obj, type):
        type.__setattr__(obj, FINAL_CLASS_TAG, True)
        return __final(obj)
    else:

        @decorator
        def final_(obj_, *args, **kwargs):
            """Decorator for final methods."""
            return obj_(*args, **kwargs)

        decorated = final_(obj)
        object.__setattr__(decorated, FINAL_METHOD_TAG, True)
        return __final(decorated)


# Replace typing.final with our custom decorator for runtime checking.
globals()["final"] = _final


def simplify_member_names(names):
    # type: (Iterable[str]) -> Iterator[str]
    """
    Iterate over member names and only yield the simplified ones.

    :param names: Input names.
    :type names: str

    :return: Simplified names iterator.
    :rtype: collections.abc.Iterator[str]
    """
    return (n for n in names if not ("__" in n and n.startswith("_")))


@contextmanager
def init_context(obj, flag=True):
    # type: (Base, bool) -> Iterator
    """
    Context manager that sets the initializing tag for :class:`objetto.bases.Base`
    objects.

    .. code:: python

        >>> from objetto.bases import init_context

        >>> class MyClass(Base):
        ...     def __init__(self):  # initialization tag is implicitly set
        ...         print(("__init__", self._initializing))
        ...
        ...     def init(self):
        ...         with init_context(self):
        ...             print(("init (inside of context)", self._initializing))
        ...         print(("init (outside of context)", self._initializing))
        ...
        >>> my_obj = MyClass()
        ('__init__', True)
        >>> my_obj.init()
        ('init (inside of context)', True)
        ('init (outside of context)', False)

    :param obj: Instance of :class:`objetto.bases.Base`.
    :type obj: objetto.bases.Base

    :param flag: Whether to set initialization flag to True of False.
    :type flag: bool

    :return: Context manager.
    :rtype: contextlib.AbstractContextManager
    """
    previous = getattr(obj, INITIALIZING_TAG, False)
    # noinspection PyCallByClass
    object.__setattr__(obj, INITIALIZING_TAG, bool(flag))
    try:
        yield
    finally:
        # noinspection PyCallByClass
        object.__setattr__(obj, INITIALIZING_TAG, previous)


@decorator
def init(func, *args, **kwargs):
    # type: (F, Any, Any) -> F
    """
    Method decorator that sets the initializing tag for :class:`objetto.bases.Base`
    objects.

    .. code:: python

        >>> from objetto.bases import init

        >>> class MyClass(Base):
        ...     def __init__(self):  # initialization tag is implicitly set
        ...         print(("__init__", self._initializing))
        ...
        ...     @init
        ...     def init(self):
        ...         print(("init", self._initializing))
        ...
        ...     def not_init(self):
        ...         print(("not_init", self._initializing))
        ...
        >>> my_obj = MyClass()
        ('__init__', True)
        >>> my_obj.init()
        ('init', True)
        >>> my_obj.not_init()
        ('not_init', False)

    :param func: Method function.
    :type func: function

    :return: Decorated method function.
    :rtype: function
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
    Make a subclass of :class:`objetto.bases.Base` on the fly.

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
        if type(self).__dict__.get("__base_cls_uuid__", None) == uuid:
            return _make_base_instance, (
                _base,
                qual_name,
                module,
                state,
                dct_copy,
                uuid,
            )
        else:
            return _make_base_subclass_instance, (type(self), state)

    # Fallback qualified name property for python 2.7.
    if not hasattr(object, "__qualname__"):

        class QualNameClsProperty(object):
            __slots__ = ()

            def __get__(self, instance, owner):
                if owner is None:
                    return self
                if instance is not None:
                    owner = type(instance)
                if owner.__dict__.get("__qualname__", None) is not self:
                    error = "type object '{}' has no attribute '__qualname__'".format(
                        owner.__name__,
                    )
                    raise AttributeError(error)
                return qual_name

        __qualname__ = QualNameClsProperty()  # type: Union[str, QualNameClsProperty]
    else:
        __qualname__ = qual_name

    # Assemble class dict by copying dct once again.
    cls_dct = dct_copy.copy()  # type: Dict[str, Any]
    cls_dct_update = {
        "__base_cls_uuid__": uuid,
        "__reduce__": __reduce__,
        "__qualname__": __qualname__,
        "__module__": module,
    }  # type: Dict[str, Any]
    cls_dct.update(cls_dct_update)

    # Make new subclass and cache it by UUID.
    if new_class is not None:

        def exec_body(ns):
            for k, v in iteritems(cls_dct):
                ns[k] = v
            return ns

        cls = cast(
            "Type[_B]", new_class(name, (_base,), {"metaclass": BaseMeta}, exec_body)
        )
    else:
        cls = mcs(name, (_base,), cls_dct)

    __base_cls_cache[uuid] = cls

    return cls


def _make_base_subclass_instance(
    cls,  # type: Type[_B]
    state,  # type: Dict[str, Any]
):
    # type: (...) -> _B
    """
    Make an instance of a subclass of a generated :class:`objetto.bases.Base`.

    :param cls: Base subclass.
    :param state: Pickled state.
    :return: Generated instance.
    """
    self = cast("_B", cls.__new__(cls))
    self.__setstate__(state or {})
    return self


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
    Make an instance of a subclass of :class:`objetto.bases.Base` on the fly.

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
    Make a subclass of :class:`objetto.bases.Base` on the fly.

    :param base: Base class.
    :type base: type[objetto.bases.Base]

    :param qual_name: Qualified name.
    :type qual_name: str or None

    :param module: Module.
    :type module: str or None

    :param dct: Members dictionary.
    :param dct: dict[str, Any] or None

    :return: Generated subclass.
    :rtype: type[objetto.bases.Base]
    """
    return _make_base_cls(base, qual_name, module, dct=dct)


class BaseMeta(SlottedABCMeta):
    """
    Metaclass for :class:`objetto.bases.Base`.

    Inherits from:
      - :class:`slotted.SlottedABCMeta`

    Inherited by:
      - :class:`objetto.bases.BaseStructureMeta`
      - :class:`objetto.bases.BaseAttributeMeta`
      - :class:`objetto.applications.ApplicationMeta`

    Features:
      - Forces the use of `__slots__`.
      - Forces `__hash__` to be declared if `__eq__` was declared.
      - Decorates `__init__` methods to update the initializing tag.
      - Prevents base class attributes from changing.
      - Runtime checking for `final` decorated classes/methods.
      - Implements `__fullname__` class property for backporting qualified name.
    """

    __open_attributes = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[Type, FrozenSet[str]]

    @staticmethod
    def __new__(mcs, name, bases, dct):
        """Make `BaseMeta` class."""
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
        Get class representation.

        :return: Class representation.
        :rtype: str
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
        Get a simplified list of class member names.

        :return: List of class member names.
        :rtype: list[str]
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
        Prevent setting read-only class attributes.

        :param name: Name.
        :str name: str

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
        Prevent deleting read-only class attributes.

        :param name: Name.
        :type name: str

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
        :rtype: str
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
    Base class for all `Objetto` types.

    Metaclass:
      - :class:`objetto.bases.BaseMeta`

    Inherits from:
      - :class:`slotted.SlottedABC`

    Inherited By:
      - :class:`objetto.bases.BaseHashable`
      - :class:`objetto.bases.BaseSized`
      - :class:`objetto.bases.BaseIterable`
      - :class:`objetto.bases.BaseContainer`
      - :class:`objetto.bases.BaseReaction`
      - :class:`objetto.bases.BaseFactory`
      - :class:`objetto.bases.AbstractMember`
      - :class:`objetto.objects.UniqueDescriptor`
      - :class:`objetto.applications.Application`
      - :class:`objetto.applications.ApplicationSnapshot`
      - :class:`objetto.applications.ApplicationRoot`
      - :class:`objetto.applications.ApplicationProperty`

    Features:
      - Forces the use of `__slots__`.
      - Forces `__hash__` to be declared if `__eq__` was declared.
      - Property that tells whether instance is initializing or not.
      - Default implementation of `__copy__` raises an error.
      - Default implementation of `__ne__` returns the opposite of `__eq__`.
      - Prevents base class attributes from changing.
      - Runtime checking for `final` decorated classes/methods.
      - Simplified `__dir__` result that shows only relevant members for client code.
      - Implements `__fullname__` class property for backporting qualified name.
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

    def __repr__(self):
        # type: () -> str
        """
        Get representation using class' full name if possible.

        :return: Representation.
        :rtype: str
        """
        return "<{} at {}>".format(type(self).__fullname__, hex(id(self)))

    def __ne__(self, other):
        # type: (object) -> bool
        """
        Compare for inequality by negating the result of `__eq__`.
        This is a backport of the default python 3 behavior to python 2.

        :param other: Another object.

        :return: True if not equal.
        :rtype: bool or NotImplemented
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
        :rtype: list[str]
        """
        member_names = set()  # type: Set[str]
        for base in reversed(getmro(type(self))):
            if base is object or base is type:
                continue
            member_names.update(simplify_member_names(base.__dict__))
        return sorted(member_names)

    @property
    @final
    def _initializing(self):
        # type: () -> bool
        """
        Whether `__init__` (or any other initialization method) is running.

        :rtype: bool
        """
        return getattr(self, INITIALIZING_TAG, False)


@final
class AbstractMemberMeta(BaseMeta):
    """
    Metaclass for :class:`objetto.bases.AbstractMember`.

    Inherits from:
      - :class:`objetto.bases.BaseMeta`

    Features:
      - Enforces abstract tag.
    """

    @staticmethod
    def __new__(mcs, name, bases, dct):
        """Make `AbstractMember` class."""
        dct[ABSTRACT_TAG] = True
        return super(AbstractMemberMeta, mcs).__new__(mcs, name, bases, dct)

    def __call__(cls, *args, **kwargs):
        """
        Prevent instantiation.

        :raises TypeError: Always raised.
        """
        error = "'{}' can't be instantiated".format(cls.__name__)
        raise TypeError(error)

    def __repr__(cls):
        # type: () -> str
        """
        Get class representation.

        :return: Class representation.
        :rtype: str
        """
        return "<abstract>"


@final
class AbstractMember(with_metaclass(AbstractMemberMeta, Base)):
    """
    Abstract member for classes.

    .. note::
        Do not use this class directly. Use the helper function
        :func:`objetto.bases.abstract_member` instead.

    Metaclass:
      - :class:`objetto.bases.AbstractMemberMeta`

    Inherits from:
      - :class:`objetto.bases.Base`

    Features:
      - Prevents class from instantiating if not overriden by a concrete member.
    """

    __slots__ = ()

    @staticmethod
    def __new__(cls, *args, **kwargs):
        """
        Prevent instantiation.

        :raises TypeError: Always raised.
        """
        error = "'{}' can't be instantiated".format(cls.__name__)
        raise TypeError(error)


def abstract_member(types=()):
    # type: (Union[Type[T], Iterable[Type[T]]]) -> Union[Type[AbstractMember], T]
    """
    Used to indicate an abstract attribute member in a class.

    .. code:: python

        >>> from objetto.bases import Base, abstract_member

        >>> class AbstractClass(Base):
        ...     some_attribute = abstract_member(int)  # will prevent instatiation
        ...
        >>> obj = AbstractClass()
        Traceback (most recent call last):
        TypeError: Can't instantiate abstract class AbstractClass with abstract \
method...

        >>> class ConcreteClass(AbstractClass):
        ...     some_attribute = 3  # concrete
        >>> obj = ConcreteClass()

    :param types: Type(s) for static type checking.
    :type types: type or tuple[type]

    :return: Abstract member.
    :rtype: type[objetto.bases.AbstractMember]
    """
    if False and types:  # for PyCharm
        pass
    return AbstractMember


class BaseHashable(Base, SlottedHashable):
    """
    Base hashable.

    Inherits from:
      - :class:`objetto.bases.Base`
      - :class:`slotted.SlottedHashable`

    Inherited By:
      - :class:`objetto.bases.BaseState`
      - :class:`objetto.bases.BaseStructure`
      - :class:`objetto.bases.BaseRelationship`
      - :class:`objetto.bases.KeyRelationship`
      - :class:`objetto.bases.BaseAttribute`
      - :class:`objetto.history.HistoryDescriptor`

    Features:
      - Forces implementation of `__hash__` method.
    """

    __slots__ = ()

    @abstractmethod
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        :rtype: int

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


class BaseSized(Base, SlottedSized):
    """
    Base sized.

    Inherits from:
      - :class:`objetto.bases.Base`
      - :class:`slotted.SlottedSized`

    Inherited By:
      - :class:`objetto.bases.BaseCollection`

    Features:
      - Has a length (count).
    """

    __slots__ = ()

    @abstractmethod
    def __len__(self):
        # type: () -> int
        """
        Get count.

        :return: Count.
        :rtype: int

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


class BaseIterable(Base, SlottedIterable, Generic[T_co]):
    """
    Base iterable.

    Inherits from:
      - :class:`objetto.bases.Base`
      - :class:`slotted.SlottedIterable`
      - :class:`typing.Generic`

    Inherited By:
      - :class:`objetto.bases.BaseCollection`

    Features:
      - Can be iterated over.
    """

    __slots__ = ()

    @abstractmethod
    def __iter__(self):
        # type: () -> Iterator
        """
        Iterate over.

        :return: Iterator.
        :rtype: collections.abc.Iterator

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


class BaseContainer(Base, SlottedContainer, Generic[T_co]):
    """
    Base container.

    Inherits from:
      - :class:`objetto.bases.Base`
      - :class:`slotted.SlottedContainer`
      - :class:`typing.Generic`

    Inherited By:
      - :class:`objetto.bases.BaseCollection`

    Features:
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
        :rtype: bool

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# Trick mypy.
_SlottedCollection = SlottedCollection
if _SlottedCollection is None:
    globals()["_SlottedCollection"] = object


class BaseCollection(
    BaseSized, BaseIterable[T_co], BaseContainer[T_co], _SlottedCollection
):
    """
    Base collection.

    Inherits from:
      - :class:`objetto.bases.BaseSized`
      - :class:`objetto.bases.BaseIterable`
      - :class:`objetto.bases.BaseContainer`
      - :class:`slotted.SlottedCollection`

    Inherited By:
      - :class:`objetto.bases.BaseProtectedCollection`

    Features:
      - Method to find content that matches attribute values.
    """

    __slots__ = ()

    @abstractmethod
    def find_with_attributes(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.

        :return: Value that has matching attributes.

        :raises ValueError: No attributes provided or no match found.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BPC = TypeVar("_BPC", bound="BaseProtectedCollection")


class BaseProtectedCollection(BaseCollection[T]):
    """
    Base protected collection.

    Inherits from:
      - :class:`objetto.bases.BaseCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveCollection`
      - :class:`objetto.bases.BaseMutableCollection`
      - :class:`objetto.bases.BaseProtectedDict`
      - :class:`objetto.bases.BaseProtectedList`
      - :class:`objetto.bases.BaseProtectedSet`

    Features:
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
        :rtype: objetto.bases.BaseProtectedCollection

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BIC = TypeVar("_BIC", bound="BaseInteractiveCollection")


# noinspection PyAbstractClass
class BaseInteractiveCollection(BaseProtectedCollection[T]):
    """
    Base interactive collection.

    Inherits from:
      - :class:`objetto.bases.BaseProtectedCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveDict`
      - :class:`objetto.bases.BaseInteractiveList`
      - :class:`objetto.bases.BaseInteractiveSet`
      - :class:`objetto.bases.BaseState`
      - :class:`objetto.bases.BaseInteractiveStructure`

    Features:
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
        :rtype: objetto.bases.BaseInteractiveCollection
        """
        return self._clear()


# noinspection PyAbstractClass
class BaseMutableCollection(BaseProtectedCollection[T]):
    """
    Base mutable collection.

    Inherits from:
      - :class:`objetto.bases.BaseProtectedCollection`

    Inherited By:
      - :class:`objetto.bases.BaseMutableDict`
      - :class:`objetto.bases.BaseMutableList`
      - :class:`objetto.bases.BaseMutableSet`
      - :class:`objetto.bases.BaseMutableStructure`
      - :class:`objetto.bases.BaseProxyObject`

    Features:
      - Has public mutable transformation and magic methods.
    """

    __slots__ = ()

    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()
