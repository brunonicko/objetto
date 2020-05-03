# -*- coding: utf-8 -*-
"""Object."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from six import with_metaclass, iteritems, itervalues, raise_from
from typing import (
    Type,
    Tuple,
    Dict,
    Any,
    Optional,
    Callable,
    Mapping,
    Iterable,
    FrozenSet,
    Union,
)
from slotted import Slotted
from collections import Counter

from .._base.constants import MISSING, DELETED
from .._components.events import field
from .._components.attributes import (
    ObjectState,
    Attribute,
    AttributeDelegate,
    DependencyPromise,
    make_object_state_class,
)

from ..utils.type_checking import UnresolvedType as UType
from ..utils.wrapped_dict import WrappedDict
from ..utils.recursive_repr import recursive_repr
from ..utils.naming import privatize_name
from ..utils.partial import Partial
from ..utils.object_repr import object_repr
from ..utils.type_checking import assert_is_instance

from .base import BaseObjectEvent, BaseObjectMeta, BaseObject

__all__ = [
    "ObjectEvent",
    "AttributesUpdateEvent",
    "AttributeDescriptor",
    "AttributeDescriptorDependencyPromise",
    "ObjectMeta",
    "Object",
]


class ObjectEvent(BaseObjectEvent):
    """Object event."""


class AttributesUpdateEvent(ObjectEvent):
    """Emitted when values for an object's attributes change."""

    new_values = field()
    old_values = field()
    input_values = field()


class AttributeDescriptorDependencyPromise(DependencyPromise):
    """Placeholder for an attribute dependency."""

    def collapse(self):
        # type: () -> str
        """Collapse into an attribute name."""
        assert_is_instance(self.obj, AttributeDescriptor)
        return self.obj.name


class AttributeDescriptor(Slotted):
    """Attribute descriptor for _objects."""

    __slots__ = (
        "__owner",
        "__name",
        "__attribute_kwargs",
        "__kwargs",
        "__default",
        "__default_factory",
        "__parent",
        "__history",
        "__final",
        "__delegated",
        "__fget",
        "__fset",
        "__fdel",
        "__attribute",
    )

    def __init__(
        self,
        value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        value_factory=None,  # type: Optional[Callable]
        exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        default_module=None,  # type: Optional[str]
        accepts_none=None,  # type: Optional[bool]
        comparable=None,  # type: Optional[bool]
        represented=False,  # type: Optional[bool]
        printed=None,  # type: Optional[bool]
        delegated=False,  # type: bool
        settable=None,  # type: Optional[bool]
        deletable=None,  # type: Optional[bool]
        default=MISSING,  # type: Any
        default_factory=None,  # type: Optional[Callable]
        parent=True,  # type: bool
        history=True,  # type: bool
        final=False,  # type: bool
    ):
        # type: (...) -> None
        """Initialize with parameters."""

        # Ownership
        self.__owner = None
        self.__name = None

        # Format parameters
        default_module = str(default_module) if default_module is not None else None
        accepts_none = bool(accepts_none) if accepts_none is not None else None
        comparable = bool(comparable) if comparable is not None else None
        represented = bool(represented) if represented is not None else None
        printed = bool(printed) if printed is not None else None
        delegated = bool(delegated)
        settable = bool(settable) if settable is not None else None
        deletable = bool(deletable) if deletable is not None else None
        parent = bool(parent)
        history = bool(history)
        final = bool(final)

        # Check parameters
        if default is not MISSING and default_factory is not None:
            error = "can't specify both 'default' and 'default_factory' parameters"
            raise ValueError(error)
        if default is not MISSING or default_factory is not None:
            if default_factory is not None and not callable(default_factory):
                error = (
                    "specified 'default_factory' of type '{}' is not callable"
                ).format(type(default_factory).__name__)
                raise TypeError(error)
            if delegated:
                error = (
                    "can't specify 'default' or 'default_factory' parameters for "
                    "delegated attributes"
                )
                raise ValueError(error)
        elif default is MISSING and default_factory is None:
            if settable is False:
                error = (
                    "need to specify 'default' or 'default_factory' if 'settable' is "
                    "set to False"
                )
                raise ValueError(error)

        # Store keyword arguments
        self.__attribute_kwargs = attribute_kwargs = {
            "value_type": value_type,
            "value_factory": value_factory,
            "exact_value_type": exact_value_type,
            "default_module": default_module,
            "accepts_none": accepts_none,
            "comparable": comparable,
            "represented": represented,
            "printed": printed,
            "delegated": delegated,
            "settable": settable,
            "deletable": deletable,
        }
        self.__kwargs = kwargs = dict(attribute_kwargs)
        kwargs.update(
            {
                "default": default,
                "default_factory": default_factory,
                "parent": parent,
                "history": history,
                "final": final,
            }
        )

        # Descriptor-only parameters
        self.__default = default
        self.__default_factory = default_factory
        self.__parent = parent
        self.__history = history
        self.__final = final

        # Shared parameters
        self.__delegated = delegated

        # Delegates
        self.__fget = None
        self.__fset = None
        self.__fdel = None

        # Attribute
        self.__attribute = None

    def __get__(self, obj, obj_cls=None):
        # type: (Optional[Object], Optional[Type[Object]]) -> Any
        """Descriptor 'get' access."""
        name = self.__name
        if obj is None:
            if name is not None and obj_cls is not None:
                constants = obj_cls.constants
                if name in constants:
                    return constants[name]
            return self
        if name is None:
            error = "attribute has no owner"
            raise RuntimeError(error)
        try:
            return obj[name]
        except KeyError as e:
            exc = AttributeError(e)
            raise_from(exc, None)
            raise exc

    def __set__(self, obj, value):
        # type: (Object, Any) -> None
        """Descriptor 'set' access."""
        name = self.__name
        if name is None:
            error = "attribute has no owner"
            raise RuntimeError(error)
        obj[name] = value

    def __delete__(self, obj):
        # type: (Object) -> None
        """Descriptor 'delete' access."""
        name = self.__name
        if name is None:
            error = "attribute has no owner"
            raise RuntimeError(error)
        try:
            del obj[name]
        except KeyError as e:
            exc = AttributeError(e)
            raise_from(exc, None)
            raise exc

    def __set_owner__(self, owner, name):
        # type: (Type, str) -> None
        """Set ownership & name, and build attribute."""
        if self.__owner is not None and self.__name is not None:
            if owner is not self.__owner or name != self.__name:
                error = "can't re-use attribute descriptor '{}.{}' as '{}.{}'".format(
                    self.__owner.__name__, self.__name, owner.__name__, name
                )
                raise NameError(error)
        if owner is self.__owner and name == self.__name:
            return
        self.__owner = owner
        self.__name = name

        # Build attribute
        self.__attribute = Attribute(name, **self.__attribute_kwargs)

    def __assign_delegates__(self):
        # type: () -> None
        """Assign delegates."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)

        # Get owner and attribute
        owner = self.__owner
        attribute = self.__attribute

        # Assign delegates to attribute
        if self.__delegated:
            if self.__fget is not None:
                self.__fget.__collapse_promises__()
                fget = AttributeDelegate(
                    self.__fget.func,
                    gets=frozenset(
                        privatize_name(owner.__name__, n) for n in self.__fget.gets
                    ),
                )
                attribute.getter(fget)
            if self.__fset is not None:
                self.__fset.__collapse_promises__()
                fset = AttributeDelegate(
                    self.__fset.func,
                    gets=frozenset(
                        privatize_name(owner.__name__, n) for n in self.__fset.gets
                    ),
                    sets=frozenset(
                        privatize_name(owner.__name__, n) for n in self.__fset.sets
                    ),
                    deletes=frozenset(
                        privatize_name(owner.__name__, n) for n in self.__fset.deletes
                    ),
                )
                attribute.setter(fset)
            if self.__fdel is not None:
                self.__fdel.__collapse_promises__()
                fdel = AttributeDelegate(
                    self.__fdel.func,
                    gets=frozenset(
                        privatize_name(owner.__name__, n) for n in self.__fdel.gets
                    ),
                    sets=frozenset(
                        privatize_name(owner.__name__, n) for n in self.__fdel.sets
                    ),
                    deletes=frozenset(
                        privatize_name(owner.__name__, n) for n in self.__fdel.deletes
                    ),
                )
                attribute.deleter(fdel)

    def getter(self, func):
        # type: (Union[Callable, AttributeDelegate]) -> AttributeDescriptor
        """Assign a 'getter' function/delegate by decorating it."""
        if not self.__delegated:
            error = "cannot define a getter for a non-delegated attribute '{}'".format(
                self.__name
            )
            raise RuntimeError(error)
        if self.__fget is not None:
            error = "already defined a getter for attribute '{}'".format(self.__name)
            raise RuntimeError(error)

        if not isinstance(func, AttributeDelegate):
            fget = AttributeDelegate(func)
        else:
            fget = func

        if fget.sets:
            error = (
                "error while defining a getter delegate for attribute '{}', can't have "
                "'sets' dependencies"
            ).format(self.__name)
            raise ValueError(error)
        if fget.deletes:
            error = (
                "error while defining a getter delegate for attribute '{}', can't have "
                "'deletes' dependencies"
            ).format(self.__name)
            raise ValueError(error)

        self.__fget = fget
        return self

    def setter(self, func):
        # type: (Callable) -> AttributeDescriptor
        """Assign a 'setter' function/delegate by decorating it."""
        if not self.__delegated:
            error = "cannot define a setter for a non-delegated attribute '{}'".format(
                self.__name
            )
            raise RuntimeError(error)
        if self.__fset is not None:
            error = "already defined a setter for attribute '{}'".format(self.__name)
            raise RuntimeError(error)

        if not isinstance(func, AttributeDelegate):
            fset = AttributeDelegate(func)
        else:
            fset = func

        self.__fset = fset
        return self

    def deleter(self, func):
        # type: (Callable) -> AttributeDescriptor
        """Assign a 'deleter' function/delegate by decorating it."""
        if not self.__delegated:
            error = "cannot define a deleter for a non-delegated attribute '{}'".format(
                self.__name
            )
            raise RuntimeError(error)
        if self.__fdel is not None:
            error = "already defined a deleter for attribute '{}'".format(self.__name)
            raise RuntimeError(error)

        if not isinstance(func, AttributeDelegate):
            fdel = AttributeDelegate(func)
        else:
            fdel = func

        self.__fdel = fdel
        return self

    def copy(self):
        # type: () -> AttributeDescriptor
        """Get a new attribute descriptor with the same input original arguments."""
        copy = type(self)(**self.__kwargs)
        if self.__delegated:
            if self.__fget is not None:
                fget = AttributeDelegate(self.__fget.func, gets=self.__fget.gets)
                copy.getter(fget)
            if self.__fset is not None:
                fset = AttributeDelegate(
                    self.__fset.func,
                    gets=self.__fset.gets,
                    sets=self.__fset.sets,
                    deletes=self.__fset.deletes,
                )
                copy.setter(fset)
            if self.__fdel is not None:
                fdel = AttributeDelegate(
                    self.__fdel.func,
                    gets=self.__fdel.gets,
                    sets=self.__fdel.sets,
                    deletes=self.__fdel.deletes,
                )
                copy.deleter(fdel)
        return copy

    @property
    def __attribute__(self):
        # type: () -> Attribute
        """State attribute."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute

    @property
    def owned(self):
        # type: () -> bool
        """Whether owned by a class."""
        return self.__owner is not None

    @property
    def owner(self):
        # type: () -> Type[Object]
        """Owner class."""
        if self.__owner is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__owner

    @property
    def name(self):
        # type: () -> str
        """Owner class."""
        if self.__name is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__name

    @property
    def value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Value type."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.value_type

    @property
    def value_factory(self):
        # type: () -> Optional[Callable]
        """Value factory."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.value_factory

    @property
    def exact_value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Exact value type."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.exact_value_type

    @property
    def default_module(self):
        # type: () -> Optional[str]
        """Default module name for type checking."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.default_module

    @property
    def accepts_none(self):
        # type: () -> bool
        """Whether None can be accepted as a value."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.accepts_none

    @property
    def comparable(self):
        # type: () -> bool
        """Whether this is leveraged in state's '__eq__' method."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.comparable

    @property
    def represented(self):
        # type: () -> bool
        """Whether this is leveraged in state's '__repr__' method."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.represented

    @property
    def printed(self):
        # type: () -> bool
        """Whether this is leveraged in state's '__str__' method."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.printed

    @property
    def delegated(self):
        # type: () -> bool
        """Whether this attribute has access delegates (getter/setter/deleter)."""
        if self.__attribute is None:
            return self.__delegated
        return self.__attribute.delegated

    @property
    def fget(self):
        # type: () -> Optional[AttributeDelegate]
        """Access delegate (fget)."""
        if self.__attribute is None:
            return self.__fget
        else:
            return self.__attribute.fget

    @property
    def fset(self):
        # type: () -> Optional[AttributeDelegate]
        """Access delegate (fset)."""
        if self.__attribute is None:
            return self.__fset
        else:
            return self.__attribute.fset

    @property
    def fdel(self):
        # type: () -> Optional[AttributeDelegate]
        """Access delegate (fdel)."""
        if self.__attribute is None:
            return self.__fdel
        else:
            return self.__attribute.fdel

    @property
    def public(self):
        # type: () -> bool
        """Whether attribute access is considered 'public'."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.public

    @property
    def magic(self):
        # type: () -> bool
        """Whether attribute access is considered 'magic'."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.magic

    @property
    def private(self):
        # type: () -> bool
        """Whether attribute access is considered 'private'."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.private

    @property
    def protected(self):
        # type: () -> bool
        """Whether attribute access is considered 'protected'."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.protected

    @property
    def readable(self):
        # type: () -> bool
        """Whether this attribute is readable."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.readable

    @property
    def settable(self):
        # type: () -> bool
        """Whether this attribute is settable."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.settable

    @property
    def deletable(self):
        # type: () -> bool
        """Whether this attribute is deletable."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__attribute.deletable

    @property
    def default(self):
        # type: () -> Any
        """Default value."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__default

    @property
    def default_factory(self):
        # type: () -> Optional[Callable]
        """Default factory."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__default_factory

    @property
    def parent(self):
        # type: () -> bool
        """Whether obj used as value should attach as a child."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__parent

    @property
    def history(self):
        # type: () -> bool
        """Whether obj used as value should be assigned to the same history."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__history

    @property
    def final(self):
        # type: () -> bool
        """Whether this attribute can't be overridden by sub-classes."""
        if self.__attribute is None:
            error = "attribute descriptor has no owner"
            raise RuntimeError(error)
        return self.__final


def _make_object_class(
    mcs,  # type: Type[ObjectMeta]
    name,  # type: str
    bases,  # type: Tuple[Type, ...]
    dct,  # type: Dict[str, Any]
):
    # type: (...) -> ObjectMeta
    """Make obj class/subclass."""
    dct = dict(dct)

    # Prepare dictionaries
    attributes = {}
    factories = {}
    dct["__attributes__"] = WrappedDict(attributes)
    dct["__factories__"] = WrappedDict(factories)

    # Make class
    cls = super(ObjectMeta, mcs).__new__(mcs, name, bases, dct)

    # Collect attribute descriptors
    new_attributes = set()
    for base in reversed(cls.__mro__):
        for member_name, member in iteritems(base.__dict__):
            if base is cls and attributes:
                if getattr(attributes.get(member_name, None), "final", False):
                    error = "can't override final attribute descriptor '{}'".format(
                        member_name
                    )
                    raise TypeError(error)
            if isinstance(member, AttributeDescriptor):
                if isinstance(base, ObjectMeta):
                    attributes[member_name] = member
                    if base is cls:
                        member.__set_owner__(cls, member_name)
                        new_attributes.add(member)
                else:
                    attributes[member_name] = member_copy = member.copy()
                    member_copy.__set_owner__(base, member_name)
                    new_attributes.add(member_copy)
            elif member_name in attributes:
                error = (
                    "can't override attribute descriptor '{}' with a non-attribute of "
                    "type '{}'"
                ).format(member_name, type(member).__name__)
                raise TypeError(error)

    # Assign delegates to new attributes
    for attribute in new_attributes:
        attribute.__assign_delegates__()

    # Make object state class and store it
    state_class = make_object_state_class(
        *(a.__attribute__ for a in itervalues(attributes))
    )
    type.__setattr__(cls, "__state_type__", state_class)

    # Check delegate-specific attribute rules and collect factories
    for attribute_name, attribute in iteritems(attributes):

        # Constant attribute
        if attribute_name in state_class.constants:
            if attribute.parent:
                error = (
                    "the 'fget' delegate for attribute '{}' does not declare any 'get' "
                    "dependencies (it is a constant), so its 'parent' parameter can't "
                    "be set to True"
                ).format(attribute_name)
                raise ValueError(error)
            if attribute.history:
                error = (
                    "the 'fget' delegate for attribute '{}' does not declare any 'get' "
                    "dependencies (it is a constant), so its 'history' parameter can't "
                    "be set to True"
                ).format(attribute_name)
                raise ValueError(error)

        # Has default/default factory, collect it
        factory = None
        if attribute.default is not MISSING:
            factory = lambda _v=attribute.default: _v
        elif attribute.default_factory is not None:
            factory = attribute.default_factory
        if factory is not None:
            factories[attribute_name] = factory

    return cls


class ObjectMeta(BaseObjectMeta):
    """Metaclass for 'Object'."""

    __new__ = staticmethod(_make_object_class)

    __attributes__ = {}  # type: Mapping[str, AttributeDescriptor]
    __factories__ = {}  # type: Mapping[str, Callable]
    __state_type__ = ObjectState

    @property
    def attributes(cls):
        # type: () -> Mapping[str, AttributeDescriptor]
        """Get attribute descriptors mapped by name."""
        return cls.__attributes__

    @property
    def factories(cls):
        # type: () -> Mapping[str, Callable]
        """Get default factories by name."""
        return cls.__factories__

    @property
    def dependencies(cls):
        # type: () -> Mapping[str, FrozenSet[str, ...]]
        """Get dependencies."""
        return cls.__state_type__.dependencies

    @property
    def constants(cls):
        # type: () -> Mapping[str, Any]
        """Get constant values."""
        return cls.__state_type__.constants


class Object(with_metaclass(ObjectMeta, BaseObject)):
    """BaseObject described by attributes."""

    __slots__ = ("__state",)
    __state_type__ = ObjectState

    def __pre_init__(self):
        # type: () -> None
        """Pre-initialize."""
        super(Object, self).__pre_init__()
        cls = type(self)
        self.__state = cls.__state_type__(self)
        if cls.factories:
            self.update(*iteritems(dict((n, f()) for n, f in iteritems(cls.factories))))

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """Get representation."""
        repr_dict = self.__state.get_dict(attribute_sieve=lambda a: a.represented)
        return "<{} {}{}>".format(
            type(self).__name__,
            hex(id(self)),
            " | {}".format(object_repr(**repr_dict)) if repr_dict else "",
        )

    @recursive_repr
    def __str__(self):
        # type: () -> str
        """Get string representation."""
        str_dict = self.__state.get_dict(attribute_sieve=lambda a: a.printed)
        return "<{}{}>".format(
            type(self).__name__,
            " {}".format(object_repr(**str_dict)) if str_dict else "",
        )

    def __eq__(self, other):
        # type: (Object) -> bool
        """Compare for equality."""
        if type(self) is not type(other):
            return False
        self_state = self.__state
        other_state = other.__state
        return self_state == other_state

    def __getitem__(self, name):
        # type: (str) -> Any
        """Get attribute value."""
        return self.__state[name]

    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """Set attribute value."""
        with self._batch_context("Set Attribute"):
            self.update((name, value))

    def __delitem__(self, name):
        # type: (str) -> None
        """Delete attribute."""
        self.__getitem__(name)
        with self._batch_context("Delete Attribute"):
            self.update((name, DELETED))

    def update(self, *name_value_pairs):
        # type: (Tuple[Tuple[str, Any], ...]) -> None
        """Update attribute values in one operation."""
        if not name_value_pairs:
            return

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Prepare updates
        redo_update = self.__state.prepare_update(*name_value_pairs)
        if not redo_update:
            return
        undo_update = ~redo_update

        # Prepare children
        child_count = Counter()
        for name, value in iteritems(redo_update):
            attribute = type(self).attributes[name]
            if attribute.parent:
                old_value = undo_update[name]
                if isinstance(old_value, BaseObject):
                    child_count[old_value] -= 1
                if isinstance(value, BaseObject):
                    child_count[value] += 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Prepare history adopters
        history_adopters = set()
        for name, value in iteritems(redo_update):
            attribute = type(self).attributes[name]
            if attribute.history and isinstance(value, BaseObject):
                history_adopters.add(value)
        history_adopters = frozenset(history_adopters)

        # Create partials and events
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            self.__state.update, redo_update
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            self.__state.update, undo_update
        )
        redo_event = AttributesUpdateEvent(
            obj=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            new_values=redo_update,
            old_values=undo_update,
            input_values=name_value_pairs,
        )
        undo_event = AttributesUpdateEvent(
            obj=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            new_values=undo_update,
            old_values=redo_update,
            input_values=None,
        )

        # Dispatch
        self.__dispatch__(
            "Update Attributes", redo, redo_event, undo, undo_event, history_adopters
        )
