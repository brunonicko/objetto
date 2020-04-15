# -*- coding: utf-8 -*-
"""Object model."""

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
    cast,
)
from slotted import Slotted
from collections import Counter

from .._components.hierarchy import Hierarchy
from .._components.state.base import State
from .._components.state.object import (
    SpecialValue, ObjectState, Attribute, AttributeDelegate, make_object_state_class
)
from ..utils.type_checking import UnresolvedType as UType
from ..utils.wrapped_dict import WrappedDict
from ..utils.naming import privatize_name
from ..utils.partial import Partial
from .base import ModelMeta, Model, ModelEvent

__all__ = [
    "AttributesUpdateEvent",
    "AttributeDescriptor",
    "ObjectModelMeta",
    "ObjectModel",
]


class AttributesUpdateEvent(ModelEvent):
    """Emitted when values for an object model's attributes change."""

    __slots__ = ("__new_values", "__old_values")

    def __init__(
        self,
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        new_values,  # type: Mapping[str, Any]
        old_values,  # type: Mapping[str, Any]
    ):
        # type: (...) -> None
        """Initialize with new values and old values."""
        super(AttributesUpdateEvent, self).__init__(adoptions, releases)
        self.__new_values = new_values
        self.__old_values = old_values

    @property
    def new_values(self):
        # type: () -> Mapping[str, Any]
        """New values."""
        return self.__new_values

    @property
    def old_values(self):
        # type: () -> Mapping[str, Any]
        """Old values."""
        return self.__old_values


class AttributeDescriptor(Slotted):
    """Attribute descriptor for _models."""

    __slots__ = (
        "__owner",
        "__name",
        "__attribute_kwargs",
        "__kwargs",
        "__parent",
        "__history",
        "__final",
        "__delegated",
        "__fget",
        "__fset",
        "__fdel",
        "__attribute"
    )

    def __init__(
        self,
        value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        value_factory=None,  # type: Optional[Callable]
        exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        default_module=None,  # type: Optional[str]
        accepts_none=None,  # type: Optional[bool]
        comparable=None,  # type: Optional[bool]
        representable=None,  # type: Optional[bool]
        delegated=False,  # type: bool
        parent=False,  # type: bool
        history=False,  # type: bool
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
        representable = bool(representable) if representable is not None else None
        delegated = bool(delegated)
        parent = bool(parent)
        history = bool(history)
        final = bool(final)

        # Store keyword arguments
        self.__attribute_kwargs = attribute_kwargs = {
            "value_type": value_type,
            "value_factory": value_factory,
            "exact_value_type": exact_value_type,
            "default_module": default_module,
            "accepts_none": accepts_none,
            "comparable": comparable,
            "representable": representable,
            "delegated": delegated
        }
        self.__kwargs = kwargs = dict(attribute_kwargs)
        kwargs.update({
            "parent": parent,
            "history": history,
            "final": final
        })

        # Delegate-only parameters
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

    def __get__(self, model, model_cls=None):
        # type: (Optional[ObjectModel], Optional[Type[ObjectModel]]) -> Any
        """Descriptor 'get' access."""
        name = self.__name
        if model is None:
            if name is not None and model_cls is not None:
                constants = model_cls.constants
                if name in constants:
                    return constants[name]
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

    def __set_owner__(self, owner, name):
        # type: (Type, str) -> None
        """Set ownership & name, and build attribute."""
        if self.__owner is not None and self.__name is not None:
            if owner is not self.__owner or name != self.__name:
                raise NameError(
                    "can't re-use attribute descriptor '{}.{}' as '{}.{}'".format(
                        self.__owner.__name__, self.__name, owner.__name__, name
                    )
                )
        if owner is self.__owner and name == self.__name:
            return
        self.__owner = owner
        self.__name = name

        # Build attribute
        self.__attribute = attribute = Attribute(name, **self.__attribute_kwargs)

        # Assign delegates to attribute
        if self.__delegated:
            if self.__fget is not None:
                fget = AttributeDelegate(
                    self.__fget.func,
                    gets=frozenset(
                        privatize_name(owner.__name__, n) for n in self.__fget.gets
                    )
                )
                attribute.getter(fget)
            if self.__fset is not None:
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
                    )
                )
                attribute.setter(fset)
            if self.__fdel is not None:
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
                    )
                )
                attribute.deleter(fdel)

    def getter(self, func):
        # type: (Union[Callable, AttributeDelegate]) -> AttributeDescriptor
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
        # type: (Callable) -> AttributeDescriptor
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
        # type: (Callable) -> AttributeDescriptor
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

    def copy(self):
        # type: () -> AttributeDescriptor
        """Get a new attribute descriptor with the same input original arguments."""
        copy = type(self)(**self.__kwargs)
        if self.__delegated:
            if self.__fget is not None:
                fget = AttributeDelegate(
                    self.__fget.func,
                    gets=self.__fget.gets
                )
                copy.getter(fget)
            if self.__fset is not None:
                fset = AttributeDelegate(
                    self.__fset.func,
                    gets=self.__fset.gets,
                    sets=self.__fset.sets,
                    deletes=self.__fset.deletes
                )
                copy.setter(fset)
            if self.__fdel is not None:
                fdel = AttributeDelegate(
                    self.__fdel.func,
                    gets=self.__fdel.gets,
                    sets=self.__fdel.sets,
                    deletes=self.__fdel.deletes
                )
                copy.deleter(fdel)
        return copy

    @property
    def __attribute__(self):
        # type: () -> Attribute
        """State attribute."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute

    @property
    def owner(self):
        # type: () -> Type[ObjectModel]
        """Owner class."""
        if self.__owner is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__owner

    @property
    def name(self):
        # type: () -> str
        """Owner class."""
        if self.__name is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__name

    @property
    def value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Value type."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.value_type

    @property
    def value_factory(self):
        # type: () -> Optional[Callable]
        """Value factory."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.value_factory

    @property
    def exact_value_type(self):
        # type: () -> Optional[Union[UType, Iterable[UType, ...]]]
        """Exact value type."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.exact_value_type

    @property
    def default_module(self):
        # type: () -> Optional[str]
        """Default module name for type checking."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.default_module

    @property
    def accepts_none(self):
        # type: () -> bool
        """Whether None can be accepted as a value."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.accepts_none

    @property
    def comparable(self):
        # type: () -> bool
        """Whether this is leveraged in state's '__eq__' method."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.comparable

    @property
    def representable(self):
        # type: () -> bool
        """Whether this is leveraged in state's '__repr__' and '__str__' methods."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.representable

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
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.public

    @property
    def magic(self):
        # type: () -> bool
        """Whether attribute access is considered 'magic'."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.magic

    @property
    def private(self):
        # type: () -> bool
        """Whether attribute access is considered 'private'."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.private

    @property
    def protected(self):
        # type: () -> bool
        """Whether attribute access is considered 'protected'."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.protected

    @property
    def readable(self):
        # type: () -> bool
        """Whether this attribute is readable."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.readable

    @property
    def settable(self):
        # type: () -> bool
        """Whether this attribute is settable."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.settable

    @property
    def deletable(self):
        # type: () -> bool
        """Whether this attribute is deletable."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__attribute.deletable

    @property
    def parent(self):
        # type: () -> bool
        """Whether model used as value should attach as a child."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__parent

    @property
    def history(self):
        # type: () -> bool
        """Whether model used as value should be assigned to the same history."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__history

    @property
    def final(self):
        # type: () -> bool
        """Whether this attribute can't be overridden by sub-classes."""
        if self.__attribute is None:
            raise RuntimeError("attribute descriptor has no owner")
        return self.__final


def _make_object_model_class(
    mcs,  # type: Type[ObjectModelMeta]
    name,  # type: str
    bases,  # type: Tuple[Type, ...]
    dct,  # type: Dict[str, Any]
):
    # type: (...) -> ObjectModelMeta
    """Make model class/subclass."""
    dct = dict(dct)

    # Prepare dictionaries
    attributes = {}
    dct["__attributes__"] = WrappedDict(attributes)

    # Make class
    cls = super(ObjectModelMeta, mcs).__new__(mcs, name, bases, dct)

    # Collect attribute descriptors
    for base in reversed(cls.__mro__):
        for member_name, member in iteritems(base.__dict__):
            if base is cls and attributes:
                if getattr(
                    attributes.get(member_name, None), "final", False
                ):
                    raise TypeError(
                        "can't override final attribute descriptor '{}'".format(
                            member_name
                        )
                    )
            if isinstance(member, AttributeDescriptor):
                if isinstance(cls, ObjectModelMeta):
                    attributes[member_name] = member
                    if base is cls:
                        member.__set_owner__(cls, member_name)
                else:
                    attributes[member_name] = member_copy = member.copy()
                    member_copy.__set_owner__(base, member_name)
            elif member_name in attributes:
                raise TypeError(
                    "can't override attribute descriptor '{}' with a non-attribute of "
                    "type '{}'".format(member_name, type(member).__name__)
                )

    # Make object state class and store it
    state_class = make_object_state_class(
        *(a.__attribute__ for a in itervalues(attributes))
    )
    type.__setattr__(cls, "__state_class__", state_class)

    # Check delegate-specific attribute rules
    for attribute_name, attribute in iteritems(attributes):

        # Constant attribute
        if attribute_name in state_class.constants:
            if attribute.parent:
                raise ValueError(
                    "the 'fget' delegate for attribute '{}' does not declare any"
                    "'get' dependencies (it is a constant), so its 'parent' parameter "
                    "can't be set to True".format(attribute_name)
                )
            if attribute.history:
                raise ValueError(
                    "the 'fget' delegate for attribute '{}' does not declare any"
                    "'get' dependencies (it is a constant), so its 'history' parameter "
                    "can't be set to True".format(attribute_name)
                )

    return cls


class ObjectModelMeta(ModelMeta):
    """Metaclass for 'ObjectModel'."""

    __new__ = staticmethod(_make_object_model_class)

    __attributes__ = {}  # type: Mapping[str, AttributeDescriptor]
    __state_class__ = ObjectState

    @property
    def attributes(cls):
        # type: () -> Mapping[str, AttributeDescriptor]
        """Get attribute descriptors mapped by name."""
        return cls.__attributes__

    @property
    def dependencies(cls):
        # type: () -> Mapping[str, FrozenSet[str, ...]]
        """Get dependencies."""
        return cls.__state_class__.dependencies

    @property
    def constants(cls):
        # type: () -> Mapping[str, Any]
        """Get constant values."""
        return cls.__state_class__.constants


class ObjectModel(with_metaclass(ObjectModelMeta, Model)):
    """Model described by attributes."""

    __slots__ = ()
    __state_class__ = ObjectState

    def __init__(self):
        # type: () -> None
        """Initialize."""
        super(ObjectModel, self).__init__()
        self._.add_component(type(self).__state_class__)

    # TODO: __repr__
    # TODO: __str__
    # TODO: __eq__
    # TODO: __ne__

    def __getitem__(self, name):
        # type: (str) -> Any
        """Get attribute value."""
        state = cast(ObjectState, self._[State])
        return state.get(name)

    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """Set attribute value."""
        self.update((name, value))

    def __delitem__(self, name):
        # type: (str) -> None
        """Delete attribute."""
        self.__getitem__(name)
        self.update((name, SpecialValue.DELETED))

    def keys(self):
        # type: () -> Iterable[str, ...]
        """Get/iterate over attribute names."""
        return type(self).attributes.keys()

    def update(self, *name_value_pairs):
        # type: (Tuple[Tuple[str, Any], ...]) -> None
        """Update attribute values in one operation."""
        if not name_value_pairs:
            return

        hierarchy = cast(Hierarchy, self._[Hierarchy])
        state = cast(ObjectState, self._[State])

        # Check for invalid names and values
        invalid_names = set()
        for name, value in name_value_pairs:
            if name not in type(self).attributes:
                invalid_names.add(name)
            if value is SpecialValue.MISSING:
                raise ValueError("cannot set attribute value to {}".format(value))
        if invalid_names:
            raise AttributeError(
                "'{}' object has no attribute{} '{}'".format(
                    type(self).__name__,
                    "s" if len(invalid_names) > 1 else "",
                    ", ".join("'{}'".format(n) for n in sorted(invalid_names)),
                )
            )

        # Prepare updates
        redo_update = state.prepare_update(*name_value_pairs)
        if not redo_update:
            return
        undo_update = ~redo_update

        # Prepare children
        child_count = Counter()
        for name, value in iteritems(redo_update):
            attribute = type(self).attributes[name]
            if attribute.parent:
                old_value = undo_update[name]
                if isinstance(old_value, Model):
                    child_count[old_value] -= 1
                if isinstance(value, Model):
                    child_count[value] += 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Create partials and events
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            state.update, redo_update
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            state.update, undo_update
        )
        redo_event = AttributesUpdateEvent(
            redo_children, undo_children, redo_update, undo_update
        )
        undo_event = AttributesUpdateEvent(
            undo_children, redo_children, undo_update, redo_update
        )

        # Dispatch
        self.__dispatch__("Update Attributes", redo, redo_event, undo, undo_event)
