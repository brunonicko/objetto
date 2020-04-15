# -*- coding: utf-8 -*-
"""Object state component."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from collections import defaultdict
from componente import CompositeMixin
from enum import Enum
from slotted import SlottedMeta, Slotted, SlottedMapping, SlottedMutableMapping
from six import with_metaclass, iteritems, raise_from, string_types
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Optional,
    Set,
    Tuple,
    Type,
    Union
)

from ...utils.type_checking import UnresolvedType as UType
from ...utils.type_checking import assert_is_instance, assert_is_unresolved_type
from ...utils.wrapped_dict import WrappedDict
from .base import State, StateException, StateError

__all__ = [
    "SpecialValue",
    "ObjectStateMeta",
    "ObjectState",
    "make_object_state_class",
    "Attribute",
    "AttributeDelegate",
    "AttributeUpdates",
    "ObjectStateException",
    "ObjectStateError",
]


class SpecialValue(Enum):
    """Special value."""

    MISSING = "missing"
    DELETED = "deleted"


class AttributeAccessType(Enum):
    """Attribute access type."""

    GETTER = "getter"
    SETTER = "setter"
    DELETER = "deleter"


def _is_attribute_constant(attribute_name, attributes):
    # type: (str, Mapping[str, Attribute]) -> bool
    """Get whether an attribute is a constant or not."""
    attribute = attributes[attribute_name]
    if attribute.fget is not None:
        if not attribute.fget.gets:
            return True
        else:
            return all(
                _is_attribute_constant(g, attributes) for g in attribute.fget.gets
            )
    return False


def _make_constant_access_object(
    constants,  # type: MutableMapping[str, Any]
    attribute_name,  # type: str
    attributes,  # type: Mapping[str, Attribute]
):
    # type: (...) -> object
    """Make access object that can be provided to a constant attribute fget function."""
    attribute = attributes[attribute_name]
    if not attribute.delegated:
        raise ValueError("attribute '{}' is not delegated".format(attribute_name))

    # Build properties
    dct = {"__slots__": ()}
    for get in attribute.fget.gets:

        def fget(_, _get=get):
            # type: (object, str) -> Any
            """Property's 'fget' function."""
            get_attribute = attributes[_get]
            if get_attribute.fget is not None:
                get_access = _make_constant_access_object(constants, _get, attributes)
                value = get_attribute.fget.func(get_access)
                if value in (SpecialValue.MISSING, SpecialValue.DELETED):
                    raise ValueError(
                        "getter for attribute '{}' cannot return {}".format(_get, value)
                    )
                constants[_get] = value
            else:
                value = constants[_get]
            return value

        dct[get] = property(fget=fget)

    return type("ConstantAttributeAccess", (object,), dct)()


def _make_access_object(
    state,  # type: MutableMapping[str, Any]
    attribute_name,  # type: str
    attributes,  # type: Mapping[str, Attribute]
    access_type=AttributeAccessType.GETTER,  # type: Union[str, AttributeAccessType]
):
    # type: (...) -> object
    """Make access object that can be provided to an attribute delegate's function."""
    attribute = attributes[attribute_name]
    if not attribute.delegated:
        raise ValueError("attribute '{}' is not delegated".format(attribute_name))

    # Get delegate according to the access type
    if access_type is AttributeAccessType.GETTER:
        delegate = attribute.fget
    elif access_type is AttributeAccessType.SETTER:
        delegate = attribute.fset
    elif access_type is AttributeAccessType.DELETER:
        delegate = attribute.fdel
    else:
        raise ValueError(access_type)

    # Build properties' functions according to dependencies declared in the delegate
    dct = {"__slots__": ()}
    properties_functions = {}
    for get in delegate.gets:

        def fget(_, _get=get):
            # type: (object, str) -> Any
            """Property's 'fget' function."""
            get_attribute = attributes[_get]
            if get_attribute.fget is not None:
                get_access = _make_access_object(
                    state, _get, attributes, access_type=AttributeAccessType.GETTER
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
            set_attribute = attributes[_set]
            value = set_attribute.__factory__(value)
            if value in (SpecialValue.MISSING, SpecialValue.DELETED):
                raise ValueError("cannot set attribute value to {}".format(value))
            if set_attribute.fset is not None:
                set_access = _make_access_object(
                    state, _set, attributes, access_type=AttributeAccessType.SETTER
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
                    state, _delete, attributes, access_type=AttributeAccessType.DELETER,
                )
                delete_attribute.fdel.func(delete_access)
            else:
                state[_delete] = SpecialValue.DELETED

        properties_functions.setdefault(delete, {})["fdel"] = fdel

    # Populate dct
    for name, members in iteritems(properties_functions):
        dct[name] = property(
            fget=members.get("fget"), fset=members.get("fset"), fdel=members.get("fdel")
        )

    return type("AttributeAccess", (object,), dct)()


def _make_object_state_class(
    mcs,  # type: Type[ObjectStateMeta]
    name,  # type: str
    bases,  # type: Tuple[Type, ...]
    dct,  # type: Dict[str, Any]
):
    # type: (...) -> ObjectStateMeta
    """Make object state class/subclass."""
    dct = dict(dct)

    # Get state attributes and build attributes wrapped dictionary
    state_attributes = frozenset(dct.get("state_attributes", frozenset()))
    attributes = {}
    for attribute in state_attributes:
        if attribute.name in attributes:
            raise ValueError("two or more attributes named '{}'".format(attribute.name))
        attributes[attribute.name] = attribute
    dct["__attributes__"] = WrappedDict(attributes)

    # Prepare wrapped dictionaries for dependencies and constants
    dependencies = {}
    constants = {}
    dct["__dependencies__"] = WrappedDict(dependencies)
    dct["__constants__"] = WrappedDict(constants)

    # Make class
    cls = super(ObjectStateMeta, mcs).__new__(mcs, name, bases, dct)

    # Check delegated attributes' dependencies
    for attribute_name, attribute in iteritems(attributes):

        # Not a delegated attribute, skip
        if not attribute.delegated:
            continue

        # Delegated, but does not define any delegate
        elif (
                attribute.fget is None and
                attribute.fset is None and
                attribute.fdel is None
        ):
            raise ValueError(
                "attribute '{}' is delegated, but no delegates were defined".format(
                    attribute_name
                )
            )

        get_dependencies = set()
        set_dependencies = set()
        delete_dependencies = set()

        if attribute.fget is not None:
            get_dependencies.update(attribute.fget.gets)

        if attribute.fset is None and attribute.fdel is None:
            for parameter in ("value_type", "value_factory", "exact_value_type"):
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
                    "but it's not present in the class".format(
                        attribute_name, get_dependency
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
                    "but it's not present in the class".format(
                        attribute_name, set_dependency
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
                    "but it's not present in the class".format(
                        attribute_name, delete_dependency
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
        dependencies[attribute_name] = frozenset()
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
                _make_constant_access_object(constants, attribute_name, attributes)
            )

    return cls


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
    # type: (Dict[str, Set[str, ...]]) -> Dict[str, FrozenSet[str, ...]]
    """Invert attribute dependency tree."""
    new_tree = {}
    for key, val in iteritems(tree):
        for dependency in val:
            new_tree.setdefault(dependency, set()).add(key)
    frozen_new_tree = {}
    for key, val in iteritems(new_tree):
        frozen_new_tree[key] = frozenset(val)
    return frozen_new_tree


class ObjectStateMeta(SlottedMeta):
    __new__ = staticmethod(_make_object_state_class)

    __attributes__ = {}  # type: Mapping[str, Attribute]
    __dependencies__ = {}  # type: Mapping[str, FrozenSet[str, ...]]
    __constants__ = {}  # type: Mapping[str, Any]

    def __setattr__(cls, name, value):
        # type: (str, Any) -> None
        """Prevent class attribute setting."""
        raise AttributeError("'{}' class attributes are read-only".format(cls.__name__))

    def __delattr__(cls, name):
        # type: (str) -> None
        """Prevent class attribute deleting."""
        raise AttributeError("'{}' class attributes are read-only".format(cls.__name__))

    @property
    def attributes(cls):
        # type: () -> Mapping[str, Attribute]
        """Get attributes mapped by name."""
        return cls.__attributes__

    @property
    def dependencies(cls):
        # type: () -> Mapping[str, FrozenSet[str, ...]]
        """Get dependencies."""
        return cls.__dependencies__

    @property
    def constants(cls):
        # type: () -> Mapping[str, Any]
        """Get constant values."""
        return cls.__constants__


class ObjectState(with_metaclass(ObjectStateMeta, State)):
    """Holds values curated/controlled by attributes."""

    __slots__ = ("__state",)
    state_attributes = frozenset()  # type: FrozenSet[Attribute, ...]

    def __init__(self, obj):
        # type: (CompositeMixin) -> None
        """Initialize."""
        super(ObjectState, self).__init__(obj)
        self.__state = defaultdict(lambda: SpecialValue.MISSING)
        self.__state.update(type(self).constants)

    # TODO: __repr__
    # TODO: __str__
    # TODO: __eq__
    # TODO: __ne__
    # TODO: __reduce__

    def get(self, name):
        # type: (str) -> Any
        """Get attribute value."""
        cls = type(self)
        attributes = cls.attributes

        try:
            attribute = attributes[name]
        except KeyError:
            exc = AttributeError(
                "'{}' object has no attribute '{}'".format(
                    type(self.obj).__name__, name
                )
            )
            raise_from(exc, None)
            raise exc

        if not attribute.readable:
            raise AttributeError(
                "attribute '{}.{}' is not readable".format(
                    type(self.obj).__name__, name
                )
            )

        value = self.__state[name]
        if value is SpecialValue.MISSING:
            if attribute.fget is not None:
                gets = attribute.fget.gets
                missing_gets = sorted(
                    get
                    for get in gets
                    if self.__state[get] in (SpecialValue.MISSING, SpecialValue.DELETED)
                )
                raise AttributeError(
                    "getter's dependenc{} {} (for attribute '{}') {} no value".format(
                        "ies" if len(missing_gets) > 1 else "y",
                        ", ".join("'{}'".format(n) for n in missing_gets),
                        name,
                        "have" if len(missing_gets) > 1 else "has",
                    )
                )
            raise AttributeError("attribute '{}' not initialized".format(name))
        if value is SpecialValue.DELETED:
            raise AttributeError("attribute '{}' was deleted".format(name))
        return value

    def prepare_update(self, *name_value_pairs):
        # type: (Tuple[Tuple[str, Any], ...]) -> AttributeUpdates
        """Prepare attribute update based on input values."""
        cls = type(self)
        attributes = cls.attributes
        dependencies = cls.dependencies

        # Create a temporary update state based on the current state
        update_state = UpdateState(self.__state, attributes, dependencies)

        # Set values respecting order
        for name, value in name_value_pairs:
            try:
                attribute = attributes[name]
            except KeyError:
                exc = AttributeError("object has no attribute '{}'".format(name))
                raise_from(exc, None)
                raise exc

            # Delete
            if value is SpecialValue.DELETED:
                if not attribute.deletable:
                    raise AttributeError("attribute '{}' is not deletable".format(name))
                if attribute.fdel is not None:
                    attribute.fdel.func(
                        _make_access_object(
                            update_state,
                            name,
                            attributes,
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
                if value is SpecialValue.MISSING:
                    raise ValueError(
                        "can't set attribute to special value {}".format(value)
                    )
                if attribute.fset is not None:
                    attribute.fset.func(
                        _make_access_object(
                            update_state,
                            name,
                            attributes,
                            access_type=AttributeAccessType.SETTER,
                        ),
                        value,
                    )
                else:
                    update_state[name] = value

        return update_state.get_updates()

    def update(self, update_state):
        # type: (AttributeUpdates) -> None
        """Update attribute values in one operation."""
        if not update_state:
            return
        self.__state.update(update_state)


def make_object_state_class(*attributes):
    # type: (Tuple[Attribute, ...]) -> Union[ObjectStateMeta, Type[ObjectState]]
    """Make an object state class with given attributes."""
    return ObjectStateMeta(
        ObjectState.__name__,
        (ObjectState,),
        {"__slots__": (), "state_attributes": frozenset(attributes)},
    )


class Attribute(Slotted):
    """Attribute for object state."""

    __slots__ = (
        "__name",
        "__value_type",
        "__value_factory",
        "__exact_value_type",
        "__default_module",
        "__accepts_none",
        "__comparable",
        "__representable",
        "__delegated",
        "__fget",
        "__fset",
        "__fdel",
        "__public",
        "__magic",
        "__private",
        "__protected",
    )

    def __init__(
        self,
        name,  # type: str
        value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        value_factory=None,  # type: Optional[Callable]
        exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        default_module=None,  # type: Optional[str]
        accepts_none=None,  # type: Optional[bool]
        comparable=None,  # type: Optional[bool]
        representable=None,  # type: Optional[bool]
        delegated=False,  # type: bool
    ):
        # type: (...) -> None
        """Initialize with parameters."""

        # Name
        name = str(name)
        if name == "self":
            raise AttributeError("attribute can't named 'self'")
        elif not name:
            raise AttributeError("attribute needs a valid name")
        self.__name = name

        # Default module
        if default_module is None:
            self.__default_module = None
        else:
            self.__default_module = str(default_module)

        # Check, and store 'value_type', 'exact_value_type', and 'accepts_none'
        if value_type is not None and exact_value_type is not None:
            raise ValueError(
                "cannot specify bot 'value_type' and 'exact_value_type' arguments"
            )
        if value_type is not None:
            assert_is_unresolved_type(value_type)
            self.__value_type = value_type
            self.__exact_value_type = None
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else False
            )
        elif exact_value_type is not None:
            assert_is_unresolved_type(exact_value_type)
            self.__value_type = None
            self.__exact_value_type = exact_value_type
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else False
            )
        else:
            self.__value_type = None
            self.__exact_value_type = None
            self.__accepts_none = bool(
                accepts_none if accepts_none is not None else True
            )

        # Check and store 'value_factory'
        if value_factory is not None and not callable(value_factory):
            raise TypeError(
                "expected a callable for 'value_factory', got '{}'".format(
                    type(value_factory).__name__
                )
            )
        self.__value_factory = value_factory

        # Store 'comparable' and 'representable'
        self.__comparable = bool(
            comparable if comparable is not None else not name.startswith("_")
        )
        self.__representable = bool(
            representable if representable is not None else not name.startswith("_")
        )

        # Delegated
        self.__delegated = bool(delegated)

        # Delegates
        self.__fget = None
        self.__fset = None
        self.__fdel = None

        # Exposure type
        self.__public = not name.startswith("_")
        self.__private = False
        self.__protected = False
        self.__magic = False
        if not self.__public:
            self.__magic = name.startswith("__") and name.endswith("__")
            if not self.__magic:
                self.__private = name.startswith("__")
                if not self.__private:
                    self.__protected = True

    def __factory__(self, value):
        # type: (Any) -> Any
        """Fabricate value by running it through type checks and factory."""
        if self.__value_factory is not None:
            value = self.__value_factory(value)
        try:
            if self.__value_type is not None:
                assert_is_instance(
                    value,
                    self.__value_type,
                    optional=self.__accepts_none,
                    exact=False,
                    default_module_name=self.__default_module,
                )
            elif self.__exact_value_type is not None:
                assert_is_instance(
                    value,
                    self.__exact_value_type,
                    optional=self.__accepts_none,
                    exact=True,
                    default_module_name=self.__default_module,
                )
            elif not self.__accepts_none and value is None:
                raise TypeError(
                    "attribute '{}' does not accept None as a value".format(self.__name)
                )
        except TypeError as e:
            exc = TypeError("{} while setting attribute '{}'".format(e, self.__name))
            raise_from(exc, None)
            raise exc
        return value

    def getter(self, func):
        # type: (Union[Callable, AttributeDelegate]) -> Attribute
        """Assign a 'getter' function/delegate by decorating it."""
        if not self.__delegated:
            raise RuntimeError(
                "cannot define a getter for a non-delegated attribute '{}'".format(
                    self.__name
                )
            )
        if self.__fget is not None:
            raise RuntimeError(
                "already defined a getter for attribute '{}'".format(self.__name)
            )

        if not isinstance(func, AttributeDelegate):
            fget = AttributeDelegate(func)
        else:
            fget = func

        if fget.sets:
            raise ValueError(
                "error while defining a getter delegate for attribute '{}', can't "
                "have 'sets' dependencies".format(self.__name)
            )
        if fget.deletes:
            raise ValueError(
                "error while defining a getter delegate for attribute '{}', can't "
                "have 'deletes' dependencies".format(self.__name)
            )

        self.__fget = fget
        return self

    def setter(self, func):
        # type: (Callable) -> Attribute
        """Assign a 'setter' function/delegate by decorating it."""
        if not self.__delegated:
            raise RuntimeError(
                "cannot define a setter for a non-delegated attribute '{}'".format(
                    self.__name
                )
            )
        if self.__fset is not None:
            raise RuntimeError(
                "already defined a setter for attribute '{}'".format(self.__name)
            )

        if not isinstance(func, AttributeDelegate):
            fset = AttributeDelegate(func)
        else:
            fset = func

        self.__fset = fset
        return self

    def deleter(self, func):
        # type: (Callable) -> Attribute
        """Assign a 'deleter' function/delegate by decorating it."""
        if not self.__delegated:
            raise RuntimeError(
                "cannot define a deleter for a non-delegated attribute '{}'".format(
                    self.__name
                )
            )
        if self.__fdel is not None:
            raise RuntimeError(
                "already defined a deleter for attribute '{}'".format(self.__name)
            )

        if not isinstance(func, AttributeDelegate):
            fdel = AttributeDelegate(func)
        else:
            fdel = func

        self.__fdel = fdel
        return self

    @property
    def name(self):
        # type: () -> str
        """Name."""
        return self.__name

    @property
    def value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Value type."""
        return self.__value_type

    @property
    def value_factory(self):
        # type: () -> Optional[Callable]
        """Value factory."""
        return self.__value_factory

    @property
    def exact_value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Exact value type."""
        return self.__exact_value_type

    @property
    def default_module(self):
        # type: () -> Optional[str]
        """Default module name for type checking."""
        return self.__default_module

    @property
    def accepts_none(self):
        # type: () -> bool
        """Whether None can be accepted as a value."""
        return self.__accepts_none

    @property
    def comparable(self):
        # type: () -> bool
        """Whether this is leveraged in state's '__eq__' method."""
        return self.__comparable

    @property
    def representable(self):
        # type: () -> bool
        """Whether this is leveraged in state's '__repr__' and '__str__' methods."""
        return self.__representable

    @property
    def delegated(self):
        # type: () -> bool
        """Whether this attribute has access delegates (getter/setter/deleter)."""
        return self.__delegated

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
        # type: () -> bool
        """Whether attribute access is considered 'public'."""
        if self.__public is None:
            raise AttributeError("name was not set")
        return self.__public

    @property
    def magic(self):
        # type: () -> bool
        """Whether attribute access is considered 'magic'."""
        if self.__magic is None:
            raise AttributeError("name was not set")
        return self.__magic

    @property
    def private(self):
        # type: () -> bool
        """Whether attribute access is considered 'private'."""
        if self.__private is None:
            raise AttributeError("name was not set")
        return self.__private

    @property
    def protected(self):
        # type: () -> bool
        """Whether attribute access is considered 'protected'."""
        if self.__protected is None:
            raise AttributeError("name was not set")
        return self.__protected

    @property
    def readable(self):
        # type: () -> bool
        """Whether this attribute is readable."""
        return not self.__delegated or self.__fget is not None

    @property
    def settable(self):
        # type: () -> bool
        """Whether this attribute is settable."""
        return not self.__delegated or self.__fget is not None

    @property
    def deletable(self):
        # type: () -> bool
        """Whether this attribute is deletable."""
        return not self.__delegated or self.__fget is not None


class AttributeDelegate(Slotted):
    """Attribute fget/fset/fdel delegate."""

    __slots__ = ("__func", "__gets", "__sets", "__deletes")

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
            if not isinstance(value, collections_abc.Iterable) or any(
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


class AttributeUpdates(SlottedMapping):
    """Read-only dict-like object that holds attribute updates."""

    __slots__ = ("__updates", "__reverts", "__inverse")

    def __init__(self, updates, reverts):
        # type: (Mapping[str, Any], Mapping[str, Any]) -> None
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
        return str(self.__updates)

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
        "__attributes",
        "__dependencies",
    )

    def __init__(
        self,
        state,  # type: Mapping[str, Any]
        attributes,  # type: Mapping[str, Attribute]
        dependencies,  # type: Mapping[str, FrozenSet[str, ...]]
    ):
        # type: (...) -> None
        """Initialize with initial state, attributes, and dependencies."""
        self.__state = state
        self.__updates = {}
        self.__dirty = set()
        self.__attributes = attributes
        self.__dependencies = dependencies

    def __repr__(self):
        # type: () -> str
        """Representation."""
        return repr(dict(self))

    def __str__(self):
        # type: () -> str
        """String representation."""
        return str(dict(self))

    def __getitem__(self, name):
        # type: (str) -> Any
        """Get attribute value."""
        try:
            return self.__updates[name]
        except KeyError:
            return self.__state[name]

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
                        name,
                        self.__attributes,
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


class ObjectStateException(StateException):
    """Object state exception."""


class ObjectStateError(StateError, ObjectStateException):
    """Object state error."""
