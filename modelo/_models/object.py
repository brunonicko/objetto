# -*- coding: utf-8 -*-
"""Object model."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from six import with_metaclass, iteritems, raise_from, string_types
from typing import (
    Type,
    Tuple,
    Dict,
    Any,
    Optional,
    Set,
    Callable,
    Mapping,
    Iterator,
    Iterable,
    FrozenSet,
    Union,
    AnyStr,
    MutableMapping,
    cast,
)
from slotted import (
    Slotted,
    SlottedABC,
    SlottedMapping,
    SlottedMutableMapping,
    SlottedHashable,
)
from collections import Counter, defaultdict

from .._components.broadcaster import EventListenerMixin, Event, EventPhase
from .._components.hierarchy import Hierarchy
from ..utils.type_checking import UnresolvedType, assert_is_instance
from ..utils.wrapped_dict import WrappedDict
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
        type=None,  # type: Optional[Union[UnresolvedType, Iterable[UnresolvedType, ...]]]
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
                    type(factory).__name__  # FIXME: type name collision
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
        # type: () -> Optional[Union[UnresolvedType, Iterable[UnresolvedType, ...]]]
        """Value type."""
        return self.__type

    @property
    def exact_type(self):
        # type: () -> Optional[Union[UnresolvedType, Iterable[UnresolvedType, ...]]]
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
    attribute_descriptors = {}
    attributes = {}
    dct["__attribute_descriptors__"] = WrappedDict(attribute_descriptors)
    dct["__attributes__"] = WrappedDict(attributes)

    # Make class
    cls = super(ObjectModelMeta, mcs).__new__(mcs, name, bases, dct)

    # Collect attribute descriptors
    for base in reversed(cls.__mro__):
        for member_name, member in iteritems(base.__dict__):
            if base is cls and attribute_descriptors:
                if getattr(
                    attribute_descriptors.get(member_name, None), "final", False
                ):
                    raise TypeError(
                        "can't override final attribute '{}'".format(member_name)
                    )
            if isinstance(member, AttributeDescriptor) and isinstance(
                cls, ObjectModelMeta
            ):
                attribute_descriptors[member_name] = member
                if base is cls:
                    if member_name == "self":
                        raise NameError("attribute can't be named 'self'")
                    member.__set_owner__(cls, member_name)
            elif member_name in attribute_descriptors:
                raise TypeError(
                    "can't override attribute '{}' with a non-attribute of type "
                    "'{}'".format(member_name, type(member).__name__)
                )

    # Build attributes
    for attribute_name, attribute_descriptor in iteritems(attribute_descriptors):
        attributes[attribute_name] = attribute = Attribute(attribute_name)

        # Check constant attribute rules
        if attribute.delegated and attribute.fget is not None:
            if not attribute.fget.gets:
                if attribute_descriptor.parent:
                    raise ValueError(
                        "the 'fget' delegate for attribute '{}' does not declare any"
                        "'get' dependencies (constant), so its 'parent' parameter "
                        "can't be set to True".format(attribute_name)
                    )
                if attribute_descriptor.history:
                    raise ValueError(
                        "the 'fget' delegate for attribute '{}' does not declare any"
                        "'get' dependencies (constant), so its 'history' parameter "
                        "can't be set to True".format(attribute_name)
                    )

    return cls


class ObjectModelMeta(ModelMeta):
    """Metaclass for 'ObjectModel'."""

    __new__ = staticmethod(_make_object_model_class)


class ObjectModel(
    with_metaclass(ObjectModelMeta, EventListenerMixin, SlottedHashable, Model)
):
    """Model described by attributes."""

    __slots__ = ("___state",)
    __attribute_descriptors__ = {}  # type: Dict[str, AttributeDescriptor]
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
        attribute = type(self).__attribute_descriptors__[name]
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
        attributes = cls.__attribute_descriptors__

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
        return type(self).__attribute_descriptors__.keys()

    def update(self, *name_value_pairs):
        # type: (Tuple[Tuple[str, Any], ...]) -> None
        """Update attribute values in one operation."""
        if not name_value_pairs:
            return

        # Get attribute descriptors
        cls = type(self)
        attributes = cls.__attribute_descriptors__

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
        hierarchy = cast(Hierarchy, self._[Hierarchy])

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
