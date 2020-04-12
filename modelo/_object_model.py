# -*- coding: utf-8 -*-
"""Object model."""

try:
    import collections.abc as coll
except ImportError:
    import collections as coll

from six import with_metaclass, iteritems, raise_from, string_types
from typing import (
    Type,
    Tuple,
    Dict,
    Any,
    Optional,
    Set,
    Callable,
    Iterator,
    Iterable,
    FrozenSet,
    Union,
    AnyStr,
    cast
)
from slotted import (
    Slotted,
    SlottedABC,
    SlottedMapping,
    SlottedMutableMapping,
    SlottedHashable,
)
from collections import Counter, defaultdict

from ._model import ModelMeta, Model
from ._type_checking import UType, assert_is_instance
from ._constants import SpecialValue, AttributeAccessType, EventPhase
from ._broadcaster import EventListenerMixin
from ._events import Event
from ._partial import Partial
from ._events import AttributesUpdateEvent
from ._hierarchy import Hierarchy


def _is_type_parameter_value_valid(value):
    # type: (Optional[Union[UType, Iterable[UType, ...]]]) -> bool
    """Get whether value provided to 'type' parameter is valid."""
    if value is None or isinstance(value, (type,) + string_types):
        return True
    if isinstance(value, coll.Iterable):
        for v in value:
            if not _is_type_parameter_value_valid(v):
                return False
        return True
    return False


def _privatize_name(cls_name, name):
    # type: (str, AnyStr) -> str
    """Privatize an attribute name if necessary."""
    if name.startswith("__") and not name.endswith("__"):
        return "_{}{}".format(cls_name.lstrip("_"), name)
    return name


class AttributeDelegate(Slotted):
    """Attribute fget/fset/fdel delegate."""

    __slots__ = (
        "__owner",
        "__name",
        "__access_type",
        "__func",
        "__gets",
        "__sets",
        "__deletes",
    )

    @classmethod
    def get_decorator(
        cls,
        gets=(),  # type: Iterable[str, ...]
        sets=(),  # type: Iterable[str, ...]
        deletes=(),  # type: Iterable[str, ...]
        reset=True,  # type: bool
    ):
        # type: (...) -> Callable
        """Get a decorator that can be used to decorate a function/another delegate."""

        def decorator(func):
            # type: (Union[Callable, AttributeDelegate]) -> AttributeDelegate
            """Decorate a function/another delegate."""
            if isinstance(func, AttributeDelegate):
                if reset:
                    delegate = cls(func)
                else:
                    delegate = func
                func = delegate.func
            else:
                delegate = cls(func)
            return cls(
                func,
                gets=delegate.gets.union(gets),
                sets=delegate.sets.union(sets),
                deletes=delegate.deletes.union(deletes),
            )

        return decorator

    def __init__(
        self,
        func,  # type: Callable
        gets=(),  # type: Iterable[str, ...]
        sets=(),  # type: Iterable[str, ...]
        deletes=(),  # type: Iterable[str, ...]
    ):
        # type: (...) -> None
        """Initialize with dependencies."""

        # Ownership
        self.__owner = None
        self.__name = None
        self.__access_type = None

        # Make sure 'func' is a callable, but not an AttributeDelegate
        if not callable(func):
            raise TypeError(
                "cannot decorate non-callable object of type '{}' as a "
                "getter/setter/deleter".format(type(func).__name__)
            )
        elif isinstance(func, AttributeDelegate):
            raise TypeError(
                "cannot use a '{}' object as the callable function".format(
                    type(func).__name__
                )
            )

        # Make sure dependencies are iterables of strings
        for param, value in (("gets", gets), ("sets", sets), ("deletes", deletes)):
            if not isinstance(value, coll.Iterable) or any(
                not isinstance(v, string_types) for v in value
            ):
                raise TypeError(
                    "expected an iterable of strings for parameter '{}', got {}".format(
                        param, value
                    )
                )

        self.__func = func
        self.__gets = frozenset(gets)
        self.__sets = frozenset(sets)
        self.__deletes = frozenset(deletes)

    def __call__(self, *args, **kwargs):
        # type: (Tuple[Any, ...], Dict[str, Any]) -> Optional[Any]
        """Call the function."""
        return self.__func(*args, **kwargs)

    def __set_owner__(self, owner, name, access_type):
        # type: (AttributeDescriptor, str, AttributeAccessType) -> None
        """Set owner (attribute descriptor), attribute name, and access type."""

        # Set ownership
        if (
            self.__owner is not None
            and self.__name is not None
            and self.__access_type is not None
        ):
            raise NameError(
                "can't re-use '{}' delegate from attribute '{}.{}' as a '{}' delegate "
                "of '{}.{}'".format(
                    self.__access_type.value,
                    self.__owner.owner.__name__,
                    self.__name,
                    access_type.value,
                    owner.owner.__name__,
                    name,
                )
            )
        if (
            owner is self.__owner
            and name == self.__name
            and access_type is self.__access_type
        ):
            return
        if owner.owner is None:
            raise AssertionError("attribute descriptor is not owned by a class")
        else:
            model_cls = owner.owner
            model_cls_name = model_cls.__name__
        self.__owner = owner
        self.__name = name
        self.__access_type = access_type

        # Privatize names
        self.__gets = frozenset(_privatize_name(model_cls_name, n) for n in self.__gets)
        self.__sets = frozenset(_privatize_name(model_cls_name, n) for n in self.__sets)
        self.__deletes = frozenset(
            _privatize_name(model_cls_name, n) for n in self.__deletes
        )

    @property
    def owner(self):
        # type: () -> Optional[AttributeDescriptor]
        """Owner attribute descriptor."""
        return self.__owner

    @property
    def name(self):
        # type: () -> Optional[str]
        """Attribute name."""
        return self.__name

    @property
    def access_type(self):
        # type: () -> Optional[AttributeAccessType]
        """Access type."""
        return self.__access_type

    @property
    def func(self):
        # type: () -> Callable
        """Function."""
        return self.__func

    @property
    def gets(self):
        # type: () -> FrozenSet[str, ...]
        """Dependencies (get)."""
        return self.__gets

    @property
    def sets(self):
        # type: () -> FrozenSet[str, ...]
        """Dependencies (set)."""
        return self.__sets

    @property
    def deletes(self):
        # type: () -> FrozenSet[str, ...]
        """Dependencies (delete)."""
        return self.__deletes


class AttributeDescriptor(Slotted):
    """Attribute descriptor for models."""

    __slots__ = (
        "__owner",
        "__name",
        "__fget",
        "__fset",
        "__fdel",
        "__public",
        "__magic",
        "__private",
        "__protected",
        "__type",
        "__factory",
        "__exact_type",
        "__accepts_none",
        "__parent",
        "__history",
        "__final",
        "__eq",
        "__pprint",
        "__repr",
        "__property",
    )

    def __init__(
        self,
        type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        factory=None,  # type: Optional[Callable]
        exact_type=None,  # type: Optional[bool]
        accepts_none=None,  # type: Optional[bool]
        parent=None,  # type: Optional[bool]
        history=None,  # type: Optional[bool]
        final=None,  # type: Optional[bool]
        eq=None,  # type: Optional[bool]
        pprint=None,  # type: Optional[bool]
        repr=False,  # type: bool
        property=False,  # type: bool
    ):
        # type: (...) -> None
        """Initialize with parameters."""

        # Ownership
        self.__owner = None
        self.__name = None

        # Exposure type
        self.__public = None
        self.__magic = None
        self.__private = None
        self.__protected = None

        # Delegates
        self.__fget = None
        self.__fset = None
        self.__fdel = None

        # Check and store 'factory'
        if factory is not None and not callable(factory):
            raise TypeError(
                "expected a callable for 'factory', got '{}'".format(
                    type(factory).__name__
                )
            )
        self.__factory = factory

        # Check, collapse, and store 'type', 'exact_type', and 'accepts_none'
        if type is not None and exact_type is not None:
            raise ValueError("cannot specify bot 'type' and 'exact_type' arguments")
        if type is not None:
            if not _is_type_parameter_value_valid(type):
                raise TypeError(
                    "expected valid type(s) and/or dot path(s) for 'type', "
                    "got {}".format(type)
                )
            self.__type = type
            self.__exact_type = None
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else False
            )
        elif exact_type is not None:
            if not _is_type_parameter_value_valid(exact_type):
                raise TypeError(
                    "expected valid type(s) and/or dot path(s) for 'exact_type', "
                    "got {}".format(exact_type)
                )
            self.__type = None
            self.__exact_type = exact_type
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else False
            )
        else:
            self.__type = None
            self.__exact_type = None
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else True
            )

        # Check and store deferred boolean parameters
        self.__parent = bool(parent) if parent is not None else None
        self.__history = bool(history) if history is not None else None
        self.__final = bool(final) if final is not None else None
        self.__eq = bool(eq) if eq is not None else None
        self.__pprint = bool(pprint) if pprint is not None else None

        # Flags: 'property' and 'repr'
        self.__repr = bool(repr)
        self.__property = bool(property)

    def __set_owner__(self, owner, name):
        # type: (Type[ObjectModel], str) -> None
        """Set ownership and name."""

        # Set ownership
        if self.__owner is not None and self.__name is not None:
            if owner is not self.__owner or name != self.__name:
                raise NameError(
                    "can't re-use attribute descriptor '{}.{}' as '{}.{}'".format(
                        self.__owner.__name__, self.__name, owner.__name__, name
                    )
                )
        if owner is self.__owner and name == self.__name:
            return
        if self.__property:
            if self.__fget is None and self.__fset is None and self.__fdel is None:
                raise NotImplementedError(
                    "property attribute '{}.{}' did not implement a "
                    "getter/setter/deleter".format(owner.__name__, name)
                )
        self.__owner = owner
        self.__name = name

        # Set attribute exposure type based on name
        self.__public = False
        self.__private = False
        self.__protected = False
        self.__magic = False

        self.__public = not name.startswith("_")
        if not self.__public:
            self.__magic = name.startswith("__") and name.endswith("__")
            if not self.__magic:
                self.__private = name.startswith("__")
                if not self.__private:
                    self.__protected = True

        # Collapse deferred boolean parameters based on access type
        if self.__parent is None:
            self.__parent = self.__public
        if self.__history is None:
            self.__history = self.__public
        if self.__final is None:
            self.__final = self.__private
        if self.__eq is None:
            self.__eq = self.__public
        if self.__pprint is None:
            self.__pprint = self.__public

        # Take ownership of attribute delegates
        if self.__fget is not None:
            self.__fget.__set_owner__(self, name, AttributeAccessType.GETTER)
        if self.__fset is not None:
            self.__fset.__set_owner__(self, name, AttributeAccessType.SETTER)
        if self.__fdel is not None:
            self.__fdel.__set_owner__(self, name, AttributeAccessType.DELETER)

    def __get__(self, model, model_cls=None):
        # type: (Optional[ObjectModel], Optional[Type[ObjectModel]]) -> Any
        """Descriptor 'get' access."""
        name = self.__name
        if model is None:
            if name is not None and model_cls is not None:
                if name in model_cls.__constants__:
                    return model_cls.__constants__[name]
            return self
        if name is None:
            raise RuntimeError("attribute has no owner")
        try:
            return model[name]
        except KeyError as e:
            exc = AttributeError(e)
            raise_from(exc, None)
            raise exc

    def __set__(self, model, value):
        # type: (ObjectModel, Any) -> None
        """Descriptor 'set' access."""
        name = self.__name
        if name is None:
            raise RuntimeError("attribute has no owner")
        model[name] = value

    def __delete__(self, model):
        # type: (ObjectModel) -> None
        """Descriptor 'delete' access."""
        name = self.__name
        if name is None:
            raise RuntimeError("attribute has no owner")
        try:
            del model[name]
        except KeyError as e:
            exc = AttributeError(e)
            raise_from(exc, None)
            raise exc

    def __factory__(self, value):
        # type: (Any) -> Any
        """Fabricate value."""
        if self.__name is None:
            raise RuntimeError("attribute has no owner")
        if self.__factory is not None:
            value = self.__factory(value)
        try:
            if self.__type is not None:
                assert_is_instance(
                    value,
                    self.__type,
                    optional=self.__accepts_none,
                    exact=False,
                    default_module_name=self.__owner.__module__,
                )
            elif self.__exact_type is not None:
                assert_is_instance(
                    value,
                    self.__exact_type,
                    optional=self.__accepts_none,
                    exact=True,
                    default_module_name=self.__owner.__module__,
                )
            elif not self.__accepts_none and value is None:
                raise TypeError(
                    "attribute '{}' does not accept None as a value".format(self.__name)
                )
        except TypeError as e:
            exc = TypeError(
                "{} while setting attribute '{}.{}'".format(
                    e, self.__owner.__name__, self.__name
                )
            )
            raise_from(exc, None)
            raise exc
        return value

    def getter(self, func):
        # type: (Union[Callable, AttributeDelegate]) -> AttributeDescriptor
        """Assign a 'getter' function/delegate by decorating it."""
        if not self.__property:
            raise RuntimeError("cannot define a getter for a non-property attribute")
        if self.__fget is not None:
            raise RuntimeError("already defined a getter")

        if not isinstance(func, AttributeDelegate):
            fget = AttributeDelegate(func)
        else:
            fget = func

        if fget.sets:
            raise ValueError("getter delegate can't have 'sets' dependencies")
        if fget.deletes:
            raise ValueError("getter delegate can't have 'deletes' dependencies")

        self.__fget = fget
        return self

    def setter(self, func):
        # type: (Callable) -> AttributeDescriptor
        """Assign a 'setter' function/delegate by decorating it."""
        if not self.__property:
            raise RuntimeError("cannot define a setter for a non-property attribute")
        if self.__fset is not None:
            raise RuntimeError("already defined a setter")

        if not isinstance(func, AttributeDelegate):
            fset = AttributeDelegate(func)
        else:
            fset = func

        self.__fset = fset
        return self

    def deleter(self, func):
        # type: (Callable) -> AttributeDescriptor
        """Assign a 'deleter' function/delegate by decorating it."""
        if not self.__property:
            raise RuntimeError("cannot define a deleter for a non-property attribute")
        if self.__fdel is not None:
            raise RuntimeError("already defined a deleter")

        if not isinstance(func, AttributeDelegate):
            fdel = AttributeDelegate(func)
        else:
            fdel = func

        self.__fdel = fdel
        return self

    @property
    def owner(self):
        # type: () -> Optional[Type[ObjectModel]]
        """Owner model class."""
        return self.__owner

    @property
    def name(self):
        # type: () -> Optional[str]
        """Member name in owner class."""
        return self.__name

    @property
    def fget(self):
        # type: () -> Optional[AttributeDelegate]
        """Access delegate (fget)."""
        return self.__fget

    @property
    def fset(self):
        # type: () -> Optional[AttributeDelegate]
        """Access delegate (fset)."""
        return self.__fset

    @property
    def fdel(self):
        # type: () -> Optional[AttributeDelegate]
        """Access delegate (fdel)."""
        return self.__fdel

    @property
    def public(self):
        # type: () -> Optional[bool]
        """Whether attribute access is considered 'public'."""
        return self.__public

    @property
    def magic(self):
        # type: () -> Optional[bool]
        """Whether attribute access is considered 'magic'."""
        return self.__magic

    @property
    def private(self):
        # type: () -> Optional[bool]
        """Whether attribute access is considered 'private'."""
        return self.__private

    @property
    def protected(self):
        # type: () -> Optional[bool]
        """Whether attribute access is considered 'protected'."""
        return self.__protected

    @property
    def readable(self):
        # type: () -> bool
        """Whether this attribute is readable."""
        return not self.__property or self.__fget is not None

    @property
    def settable(self):
        # type: () -> bool
        """Whether this attribute is settable."""
        return not self.__property or self.__fget is not None

    @property
    def deletable(self):
        # type: () -> bool
        """Whether this attribute is deletable."""
        return not self.__property or self.__fget is not None

    @property
    def factory(self):
        # type: () -> Optional[Callable]
        """Value factory."""
        return self.__factory

    @property
    def type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Value type."""
        return self.__type

    @property
    def exact_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Exact value type."""
        return self.__exact_type

    @property
    def accepts_none(self):
        # type: () -> bool
        """Whether None can be accepted as a value."""
        return self.__accepts_none

    @property
    def parent(self):
        # type: () -> Optional[bool]
        """Whether model values should be parented to owner instance."""
        return self.__parent

    @property
    def history(self):
        # type: () -> Optional[bool]
        """Whether model values should adopt owner instance's history."""
        return self.__history

    @property
    def final(self):
        # type: () -> Optional[bool]
        """Whether this attribute cannot be overridden by sub-classes."""
        return self.__final

    @property
    def eq(self):
        # type: () -> Optional[bool]
        """Whether this attribute is included in the model's __eq__ result."""
        return self.__eq

    @property
    def pprint(self):
        # type: () -> Optional[bool]
        """Whether this attribute is included in the model's __pprint__ result."""
        return self.__pprint

    @property
    def repr(self):
        # type: () -> bool
        """Whether this attribute is included in the model's __repr__ result."""
        return self.__repr

    @property
    def property(self):
        # type: () -> bool
        """Whether this attribute has access descriptors (getter/setter/deleter)."""
        return self.__property


class AttributeUpdates(SlottedMapping):
    """Read-only dict-like object that holds attribute updates."""

    __slots__ = ("__updates", "__reverts", "__inverse")

    def __init__(self, updates, reverts):
        # type: (coll.Mapping[str, Any], coll.Mapping[str, Any]) -> None
        """Initialize with update and revert values."""
        self.__updates = updates
        self.__reverts = reverts

    def __repr__(self):
        # type: () -> str
        """Representation."""
        return repr(self.__updates)

    def __str__(self):
        # type: () -> str
        """String representation."""
        return self.__repr__()

    def __getitem__(self, name):
        # type: (str) -> Any
        """Get new value for attribute name."""
        return self.__updates[name]

    def __len__(self):
        # type: () -> int
        """Get number of attributes with new values."""
        return len(self.__updates)

    def __iter__(self):
        # type: () -> Iterator[str, ...]
        """Iterate over changing attribute names."""
        for name in self.__updates:
            yield name

    def __invert__(self):
        # type: () -> AttributeUpdates
        """Get inverse."""
        return type(self)(self.__reverts, self.__updates)


class UpdateState(SlottedMutableMapping):
    """Temporary state for value access during attribute mutation."""

    __slots__ = (
        "__state",
        "__updates",
        "__dirty",
        "__model",
        "__model_cls",
        "__attributes",
        "__dependencies",
    )

    def __init__(self, state, model):
        # type: (coll.Mapping[str, Any], ObjectModel) -> None
        """Initialize with initial state and read dependencies."""
        self.__state = state
        self.__updates = {}
        self.__dirty = set()
        self.__model = model
        self.__model_cls = type(model)
        self.__attributes = self.__model_cls.__attributes__
        self.__dependencies = self.__model_cls.__dependencies__

    def __repr__(self):
        # type: () -> str
        """Representation."""
        return repr(dict(self))

    def __str__(self):
        # type: () -> str
        """String representation."""
        return self.__repr__()

    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """Set value for attribute."""
        self.__updates[name] = value
        if value is self.__state[name]:
            del self.__updates[name]
        self.__dirty.update(self.__dependencies[name])
        self.__dirty.discard(name)

    def __delitem__(self, name):
        # type: (str) -> None
        """Set attribute value to special 'DELETED' value."""
        self.__setitem__(name, SpecialValue.DELETED)

    def __getitem__(self, name):
        # type: (str) -> Any
        """Get attribute value."""
        try:
            return self.__updates[name]
        except KeyError:
            return self.__state[name]

    def __len__(self):
        # type: () -> int
        """Get attribute count."""
        return len(self.__state)

    def __iter__(self):
        # type: () -> Iterator[str, ...]
        """Iterate over attribute names."""
        for name in self.__state:
            yield name

    def __clean_dirty(self, dirty=None):
        # type: (Optional[FrozenSet[str, ...]]) -> None
        """Resolve dirty attributes."""
        if dirty is None:
            dirty = set(self.__dirty)
        while dirty:
            name = dirty.pop()
            attribute = self.__attributes[name]
            gets = attribute.fget.gets
            intersection = gets.intersection(dirty)
            if intersection:
                self.__clean_dirty(intersection)
            if all(
                self[get] not in (SpecialValue.MISSING, SpecialValue.DELETED)
                for get in gets
            ):
                self.__updates[name] = attribute.fget.func(
                    _make_access_object(
                        self,
                        self.__model,
                        attribute,
                        access_type=AttributeAccessType.GETTER,
                    )
                )
            elif (
                name in self.__updates or self.__state[name] is not SpecialValue.MISSING
            ):
                self.__updates[name] = SpecialValue.MISSING

    def get_updates(self):
        # type: () -> AttributeUpdates
        """Get updates only."""
        self.__clean_dirty()
        reverts = dict((k, self.__state[k]) for k in self.__updates)
        return AttributeUpdates(self.__updates, reverts)


def _make_access_object(
    state,  # type: coll.MutableMapping[str, Any]
    model,  # type: ObjectModel
    attribute,  # type: AttributeDescriptor
    access_type=AttributeAccessType.GETTER,  # type: AttributeAccessType
):
    # type: (...) -> object
    """Make access object that can be provided to an attribute delegate's function."""

    # Get delegate according to the access type
    if access_type is AttributeAccessType.GETTER:
        delegate = attribute.fget
    elif access_type is AttributeAccessType.SETTER:
        delegate = attribute.fset
    elif access_type is AttributeAccessType.DELETER:
        delegate = attribute.fdel
    else:
        raise ValueError(access_type)

    # Get attributes
    model_cls = type(model)
    attributes = model_cls.__attributes__

    # Build properties' functions according to dependencies declared in the delegate
    properties_functions = {}
    for get in delegate.gets:

        def fget(_, _get=get):
            # type: (object, str) -> Any
            """Property's 'fget' function."""
            get_attribute = attributes[_get]
            if get_attribute.fget is not None:
                get_access = _make_access_object(
                    state, model, get_attribute, access_type=AttributeAccessType.GETTER
                )
                value = get_attribute.fget.func(get_access)
                if value in (SpecialValue.MISSING, SpecialValue.DELETED):
                    raise ValueError(
                        "getter for attribute '{}' cannot return {}".format(_get, value)
                    )
                state[_get] = value
            else:
                value = state[_get]
                if value is SpecialValue.MISSING:
                    raise AttributeError("attribute '{}' not initialized".format(_get))
                if value is SpecialValue.DELETED:
                    raise AttributeError("attribute '{}' was deleted".format(name))
            return value

        properties_functions.setdefault(get, {})["fget"] = fget

    for set_ in delegate.sets:

        def fset(_, value, _set=set_):
            # type: (object, Any, str) -> None
            """Property's 'fset' function."""
            if value in (SpecialValue.MISSING, SpecialValue.DELETED):
                raise ValueError("cannot set attribute value to {}".format(value))
            set_attribute = attributes[_set]
            value = set_attribute.__factory__(value)
            if set_attribute.fset is not None:
                set_access = _make_access_object(
                    state, model, set_attribute, access_type=AttributeAccessType.SETTER
                )
                set_attribute.fset.func(set_access)
            else:
                state[_set] = value

        properties_functions.setdefault(set_, {})["fset"] = fset

    for delete in delegate.deletes:

        def fdel(_, _delete=delete):
            # type: (object, str) -> None
            """Property's 'fdel' function."""
            delete_attribute = attributes[_delete]
            if delete_attribute.fdel is not None:
                delete_access = _make_access_object(
                    state,
                    model,
                    delete_attribute,
                    access_type=AttributeAccessType.DELETER,
                )
                delete_attribute.fdel.func(delete_access)
            else:
                state[_delete] = SpecialValue.DELETED

        properties_functions.setdefault(delete, {})["fdel"] = fdel

    dct = {}
    for name, members in iteritems(properties_functions):
        dct[name] = property(
            fget=members.get("fget"), fset=members.get("fset"), fdel=members.get("fdel")
        )

    return type("{}AttributeAccess".format(model_cls.__name__), (Slotted,), dct)()


def _is_attribute_constant(
    attribute_name,  # type: str
    attributes,  # type: Dict[str, AttributeDescriptor]
):
    # type: (...) -> bool
    """Get whether an attribute is a constant or not."""
    attribute = attributes[attribute_name]
    if attribute.fget is not None:
        if not attribute.fget.gets:
            return True
        else:
            return bool(
                all(_is_attribute_constant(g, attributes) for g in attribute.fget.gets)
            )
    return False


def _make_constant_access_object(
    state,  # type: coll.MutableMapping[str, Any]
    model_cls,  # type: Type[ObjectModel]
    attribute,  # type: AttributeDescriptor
):
    # type: (...) -> object
    """Make access object that can be provided to a constant attribute fget function."""
    dct = {}

    # Get attributes
    attributes = model_cls.__attributes__

    # Build properties
    for get in attribute.fget.gets:

        def fget(_, _get=get):
            # type: (object, str) -> Any
            """Property's 'fget' function."""
            get_attribute = attributes[_get]
            if get_attribute.fget is not None:
                get_access = _make_constant_access_object(
                    state, model_cls, get_attribute
                )
                value = get_attribute.fget.func(get_access)
                if value in (SpecialValue.MISSING, SpecialValue.DELETED):
                    raise ValueError(
                        "getter for attribute '{}' cannot return {}".format(_get, value)
                    )
                state[_get] = value
            else:
                value = state[_get]
            return value

        dct[get] = property(fget=fget)

    return type("{}ConstantAccess".format(model_cls.__name__), (Slotted,), dct)()


def _assemble_tree(name, dependencies, all_dependencies=None):
    # type: (str, Dict[str, Set[str, ...]], Optional[Set[str, ...]]) -> Set[str, ...]
    """Assemble attribute dependency tree."""
    if all_dependencies is None:
        all_dependencies = set()
    for dependency in dependencies.get(name, ()):
        all_dependencies.add(dependency)
        _assemble_tree(dependency, dependencies, all_dependencies)
    return all_dependencies


def _invert_tree(tree):
    # type: (Dict[str, Set[str, ...]]) -> Dict[str, Set[str, ...]]
    """Invert attribute dependency tree."""
    new_tree = {}
    for key, val in iteritems(tree):
        for dependency in val:
            new_tree.setdefault(dependency, set()).add(key)
    return new_tree


def _make_model_class(mcs, name, bases, dct):
    # type: (Type[ObjectModelMeta], str, Tuple[Type, ...], Dict[str, Any]) -> ObjectModelMeta
    """Make model class/subclass."""
    dct = dict(dct)

    # Prepare dictionaries
    attributes = dct["__attributes__"] = {}
    dependencies = dct["__dependencies__"] = {}
    constants = dct["__constants__"] = {}

    # Make class
    cls = super(ObjectModelMeta, mcs).__new__(mcs, name, bases, dct)

    # Collect attribute descriptors
    for base in reversed(cls.__mro__):
        for member_name, member in iteritems(base.__dict__):
            if base is cls and attributes:
                if getattr(attributes.get(member_name, None), "final", False):
                    raise TypeError(
                        "can't override final attribute '{}'".format(member_name)
                    )
            if isinstance(member, AttributeDescriptor) and isinstance(
                cls, ObjectModelMeta
            ):
                attributes[member_name] = member
                if base is cls:
                    if member_name == "self":
                        raise NameError("attribute can't be named 'self'")
                    member.__set_owner__(cls, member_name)
            elif member_name in attributes:
                raise TypeError(
                    "can't override attribute '{}' with a non-attribute".format(
                        member_name
                    )
                )

    # Check dependencies
    for attribute_name, attribute in iteritems(attributes):
        if not attribute.property:
            continue

        get_dependencies = set()
        set_dependencies = set()
        delete_dependencies = set()

        if attribute.fget is not None:
            if not attribute.fget.gets:
                if attribute.parent:
                    raise ValueError(
                        "the 'fget' delegate for attribute '{}' does not declare any"
                        "'get' dependencies (constant), so its 'parent' parameter "
                        "can't be set to True".format(attribute_name)
                    )
                if attribute.history:
                    raise ValueError(
                        "the 'fget' delegate for attribute '{}' does not declare any"
                        "'get' dependencies (constant), so its 'history' parameter "
                        "can't be set to True".format(attribute_name)
                    )
            get_dependencies.update(attribute.fget.gets)

        if attribute.fset is None and attribute.fdel is None:
            for parameter in ("type", "exact_type", "factory"):
                if getattr(attribute, parameter) is not None:
                    raise ValueError(
                        "neither 'fset' or 'fdel' delegates were declared for "
                        "attribute '{}', so the '{}' parameter shouldn't be "
                        "provided".format(attribute_name, parameter)
                    )
            if not attribute.accepts_none:
                raise ValueError(
                    "neither 'fset' or 'fdel' delegates were declared for attribute "
                    "'{}', so the 'accepts_none' parameter can't be set to "
                    "False".format(attribute_name)
                )

        if attribute.fset is not None:
            get_dependencies.update(attribute.fset.gets)
            set_dependencies.update(attribute.fset.sets)
            delete_dependencies.update(attribute.fset.deletes)

        if attribute.fdel is not None:
            get_dependencies.update(attribute.fdel.gets)
            set_dependencies.update(attribute.fdel.sets)
            delete_dependencies.update(attribute.fdel.deletes)

        for get_dependency in get_dependencies:
            if get_dependency not in attributes:
                raise NameError(
                    "attribute '{}' declares '{}' as a 'get' dependency, "
                    "but it's not present in the class '{}'".format(
                        attribute_name, get_dependency, cls.__name__
                    )
                )
            if not attributes[get_dependency].readable:
                raise ValueError(
                    "attribute '{}' declares '{}' as a 'get' dependency, "
                    "but it's not readable".format(attribute_name, get_dependency)
                )
        for set_dependency in set_dependencies:
            if set_dependency not in attributes:
                raise NameError(
                    "attribute '{}' declares '{}' as a 'set' dependency, "
                    "but it's not present in the class '{}'".format(
                        attribute_name, set_dependency, cls.__name__
                    )
                )
            if not attributes[set_dependency].settable:
                raise ValueError(
                    "attribute '{}' declares '{}' as a 'set' dependency, "
                    "but it's not settable".format(attribute_name, set_dependency)
                )
        for delete_dependency in set_dependencies:
            if delete_dependency not in attributes:
                raise NameError(
                    "attribute '{}' declares '{}' as a 'delete' dependency, "
                    "but it's not present in the class '{}'".format(
                        attribute_name, delete_dependency, cls.__name__
                    )
                )
            if not attributes[delete_dependency].settable:
                raise ValueError(
                    "attribute '{}' declares '{}' as a 'delete' dependency, "
                    "but it's not deletable".format(attribute_name, delete_dependency)
                )

    # Build fget 'gets' dependency tree
    dependency_tree = {}
    for attribute_name, attribute in iteritems(attributes):
        dependencies[attribute_name] = set()
        attribute_dependencies = set()
        if attribute.fget is not None:
            attribute_dependencies.update(attribute.fget.gets)
        dependency_tree[attribute_name] = attribute_dependencies
    inverse_flat_dependencies = {}
    for member_name in dependency_tree:
        inverse_flat_dependencies[member_name] = _assemble_tree(
            member_name, dependency_tree
        )
    dependencies.update(_invert_tree(inverse_flat_dependencies))

    # Populate 'constants' state
    for attribute_name, attribute in iteritems(attributes):
        if _is_attribute_constant(attribute_name, attributes):
            constants[attribute_name] = attribute.fget.func(
                _make_constant_access_object(constants, cls, attribute)
            )

    return cls


class ObjectModelMeta(ModelMeta):
    """Metaclass for 'ObjectModel'."""

    __new__ = staticmethod(_make_model_class)

    def __setattr__(cls, name, value):
        # type: (str, Any) -> None
        """Prevent class attribute setting."""
        if name not in SlottedABC.__dict__:
            raise AttributeError(
                "'{}' class attributes are read-only".format(cls.__name__)
            )
        super(ObjectModelMeta, cls).__setattr__(name, value)

    def __delattr__(cls, name):
        # type: (str) -> None
        """Prevent class attribute deleting."""
        if name not in SlottedABC.__dict__:
            raise AttributeError(
                "'{}' class attributes are read-only".format(cls.__name__)
            )
        super(ObjectModelMeta, cls).__delattr__(name)


class ObjectModel(
    with_metaclass(ObjectModelMeta, EventListenerMixin, SlottedHashable, Model)
):
    """Model described by attributes."""

    __slots__ = ("___state",)
    __attributes__ = {}  # type: Dict[str, AttributeDescriptor]
    __dependencies__ = {}  # type: Dict[str, Set[str, ...]]
    __constants__ = {}  # type: Dict[str, Any]
    __event_types__ = frozenset({AttributesUpdateEvent})

    def __hash__(self):
        # type: () -> int
        """Get object hash."""
        return object.__hash__(self)

    def __getitem__(self, name):
        # type: (str) -> Any
        """Get attribute value."""
        attribute = type(self).__attributes__[name]
        if not attribute.readable:
            raise KeyError("attribute '{}' is not readable".format(name))
        value = self.__state[name]
        if value is SpecialValue.MISSING:
            if attribute.fget is not None:
                gets = attribute.fget.gets
                missing_gets = sorted(
                    get
                    for get in gets
                    if self.__state[get] in (SpecialValue.MISSING, SpecialValue.DELETED)
                )
                raise KeyError(
                    "getter's dependenc{} {} (for attribute '{}') {} no value".format(
                        "ies" if len(missing_gets) > 1 else "y",
                        ", ".join("'{}'".format(n) for n in missing_gets),
                        name,
                        "have" if len(missing_gets) > 1 else "has",
                    )
                )
            raise KeyError("attribute '{}' not initialized".format(name))
        if value is SpecialValue.DELETED:
            raise KeyError("attribute '{}' was deleted".format(name))
        return value

    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """Set attribute value."""
        self.update((name, value))

    def __delitem__(self, name):
        # type: (str) -> None
        """Delete attribute."""
        self.__getitem__(name)
        self.update((name, SpecialValue.DELETED))

    def __react__(self, model, event, phase):
        # type: (Model, Event, EventPhase) -> None
        """React to an event."""
        pass

    def __prepare_attribute_updates(self, name_value_pairs):
        # type: (Tuple[Tuple[str, Any], ...]) -> AttributeUpdates
        """Prepare attribute updates based on input values."""

        # Get attributes
        cls = type(self)
        attributes = cls.__attributes__

        # Create a temporary update state based on the current state
        update_state = UpdateState(self.__state, self)

        # Set values respecting order
        for name, value in name_value_pairs:
            attribute = attributes[name]

            # Delete
            if value is SpecialValue.DELETED:
                if not attribute.deletable:
                    raise AttributeError("attribute '{}' is not deletable".format(name))
                if attribute.fdel is not None:
                    attribute.fdel.func(
                        _make_access_object(
                            update_state,
                            self,
                            attribute,
                            access_type=AttributeAccessType.DELETER,
                        )
                    )
                else:
                    update_state[name] = value

            # Set
            else:
                if not attribute.settable:
                    raise AttributeError("attribute '{}' is not settable".format(name))
                value = attribute.__factory__(value)
                if attribute.fset is not None:
                    attribute.fset.func(
                        _make_access_object(
                            update_state,
                            self,
                            attribute,
                            access_type=AttributeAccessType.SETTER,
                        ),
                        value,
                    )
                else:
                    update_state[name] = value

        return update_state.get_updates()

    def keys(self):
        # type: () -> Iterable[str, ...]
        """Get/iterate over attribute names."""
        return type(self).__attributes__.keys()

    def update(self, *name_value_pairs):
        # type: (Tuple[Tuple[str, Any], ...]) -> None
        """Update attribute values in one operation."""
        if not name_value_pairs:
            return

        # Get attribute descriptors
        cls = type(self)
        attributes = cls.__attributes__

        # Check for invalid names and values
        invalid_names = set()
        for name, value in name_value_pairs:
            if name not in attributes:
                invalid_names.add(name)
            if value is SpecialValue.MISSING:
                raise ValueError("cannot set attribute value to {}".format(value))
        if invalid_names:
            raise KeyError(
                "'{}' object has no attribute descriptor{} '{}'".format(
                    type(self).__name__,
                    "s" if len(invalid_names) > 1 else "",
                    ", ".join("'{}'".format(n) for n in sorted(invalid_names)),
                )
            )

        # Prepare updates
        redo_updates = self.__prepare_attribute_updates(name_value_pairs)
        if not redo_updates:
            return
        undo_updates = ~redo_updates

        # Prepare children
        child_count = Counter()
        for name, value in iteritems(redo_updates):
            attribute = attributes[name]
            if attribute.parent:
                old_value = undo_updates[name]
                if isinstance(old_value, Model):
                    child_count[old_value] -= 1
                if isinstance(value, Model):
                    child_count[value] += 1
        hierarchy = cast(Hierarchy, self.__get_component__(Hierarchy))

        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create partials and events
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            self.__state.update, redo_updates
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            self.__state.update, undo_updates
        )
        redo_event = AttributesUpdateEvent(
            redo_children, undo_children, redo_updates, undo_updates
        )
        undo_event = AttributesUpdateEvent(
            undo_children, redo_children, undo_updates, redo_updates
        )

        # Dispatch
        self.__dispatch__("Update Attributes", redo, redo_event, undo, undo_event)

    @property
    def __state(self):
        # type: () -> Dict[str, Any]
        """Internal state."""
        try:
            state = self.___state
        except AttributeError:
            state = self.___state = defaultdict(lambda: SpecialValue.MISSING)
            state.update(type(self).__constants__)
        return state
