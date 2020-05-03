# -*- coding: utf-8 -*-
"""Dict object."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from collections import Counter
from six import with_metaclass, iteritems, iterkeys, itervalues, string_types
from typing import (
    Dict,
    Callable,
    Any,
    Optional,
    Mapping,
    Hashable,
    Iterable,
    Iterator,
    Union,
    Tuple,
    List,
    cast,
)

from .._base.constants import MISSING, DELETED
from .._components.events import EventPhase, field

from ..utils.partial import Partial
from ..utils.wrapped_dict import WrappedDict
from ..utils.type_checking import UnresolvedType as UType
from ..utils.type_checking import assert_is_instance

from .base import BaseObjectEvent, BaseObject
from .container import (
    ContainerObjectEvent,
    ContainerObjectMeta,
    ContainerObject,
    ContainerObjectParameters,
)


__all__ = [
    "DictObjectEvent",
    "DictUpdateEvent",
    "DictObjectMeta",
    "DictObject",
    "MutableDictObject",
    "DictProxyObject",
]


class DictObjectEvent(ContainerObjectEvent):
    """Dict object event."""


class DictUpdateEvent(DictObjectEvent):
    """Emitted when key-value pairs in a dict object change."""

    new_values = field()
    old_values = field()


class DictObjectMeta(ContainerObjectMeta):
    """Metaclass for 'DictObject'."""


class DictObject(with_metaclass(DictObjectMeta, ContainerObject)):
    """Object that stores values in a dictionary."""

    __slots__ = ("__key_parameters",)
    __state_type__ = dict

    def __init__(
        self,
        value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        value_factory=None,  # type: Optional[Callable]
        exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        default_module=None,  # type: Optional[str]
        accepts_none=None,  # type: Optional[bool]
        comparable=True,  # type: bool
        represented=False,  # type: bool
        printed=True,  # type: bool
        parent=True,  # type: bool
        history=True,  # type: bool
        type_name=None,  # type: Optional[str]
        reaction=None,  # type: Optional[Callable]
        key_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        exact_key_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        key_accepts_none=None,  # type: Optional[bool]
        key_parent=True,  # type: bool
        key_history=True,  # type: bool
    ):
        # type: (...) -> None
        """Initialize with value parameters and key parameters."""
        super(DictObject, self).__init__(
            value_type=value_type,
            value_factory=value_factory,
            exact_value_type=exact_value_type,
            default_module=default_module,
            accepts_none=accepts_none,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=parent,
            history=history,
            type_name=type_name,
            reaction=reaction,
        )
        self.__key_parameters = ContainerObjectParameters(
            value_type=key_type,
            value_factory=None,
            exact_value_type=exact_key_type,
            default_module=default_module,
            accepts_none=key_accepts_none,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=key_parent,
            history=key_history,
        )

    def __getitem__(self, key):
        # type: (Hashable) -> Any
        """Get value associated with key."""
        return self.__state[key]

    def __len__(self):
        # type: () -> int
        """Get key count."""
        return len(self.__state)

    def __iter__(self):
        # type: () -> Iterator[Hashable]
        """Iterate over keys."""
        for key in self.__state:
            yield key

    def __contains__(self, key):
        # type: (Hashable) -> bool
        """Whether contains a value."""
        return key in self.__state

    def __prepare_update(self, update):
        # type: (Mapping) -> Tuple[Mapping[Hashable, Any], Mapping[Hashable, Any]]
        """Prepare update."""
        if not update:
            error = "no updates provided"
            raise ValueError(error)

        processed_update = {}
        processed_revert = {}
        dict_update = WrappedDict(processed_update)
        dict_revert = WrappedDict(processed_revert)
        for key, value in iteritems(update):
            key = self._key_parameters.fabricate(
                key, accepts_missing=False, accepts_deleted=False
            )
            value = self._parameters.fabricate(
                value, accepts_deleted=True, accepts_missing=False
            )
            if value is DELETED:
                if key not in self.__state:
                    raise KeyError(key)
                processed_revert[key] = self.__state[key]
            elif key not in self.__state:
                processed_revert[key] = DELETED
            else:
                processed_revert[key] = self.__state[key]
            processed_update[key] = value

        return dict_update, dict_revert

    def __update(self, dict_update):
        # type: (Mapping[Hashable, Any]) -> None
        """Update."""
        for key, value in iteritems(dict_update):
            if value in (MISSING, DELETED):
                del self.__state[key]
            else:
                self.__state[key] = value

    def _update(self, *args, **kwargs):
        # type: (Tuple[Mapping], Dict[str, Any]) -> None
        """Update."""

        # Prepare update
        redo_update, undo_update = self.__prepare_update(dict(*args, **kwargs))

        # Get hierarchy
        hierarchy = self.__get_hierarchy__()

        # Count children
        child_count = Counter()
        special_drop_values = MISSING, DELETED
        if self._key_parameters.parent or self._parameters.parent:
            for key, value in iteritems(redo_update):
                if value in special_drop_values:
                    if self._key_parameters.parent:
                        if isinstance(key, BaseObject):
                            child_count[key] -= 1
                    if self._parameters.parent:
                        old_value = undo_update[key]
                        if isinstance(old_value, BaseObject):
                            child_count[old_value] -= 1
                else:
                    if self._key_parameters.parent:
                        if (
                            isinstance(key, BaseObject)
                            and undo_update[key] in special_drop_values
                        ):
                            child_count[key] += 1
                    if self._parameters.parent:
                        old_value = undo_update[key]
                        if isinstance(value, BaseObject):
                            child_count[value] += 1
                        if isinstance(old_value, BaseObject):
                            child_count[old_value] -= 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Prepare history adopters
        history_adopters = set()
        if self._key_parameters.history or self._parameters.history:
            for key, value in iteritems(redo_update):
                if self._key_parameters.history and isinstance(key, BaseObject):
                    history_adopters.add(key)
                if self._parameters.history and isinstance(value, BaseObject):
                    history_adopters.add(value)
        history_adopters = frozenset(history_adopters)

        # Create partials
        redo = Partial(hierarchy.update_children, redo_children) + Partial(
            self.__update, redo_update
        )
        undo = Partial(hierarchy.update_children, undo_children) + Partial(
            self.__update, undo_update
        )

        # Create events
        redo_event = DictUpdateEvent(
            obj=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            new_values=redo_update,
            old_values=undo_update,
        )
        undo_event = DictUpdateEvent(
            obj=self,
            adoptions=undo_children.adoptions,
            releases=undo_children.releases,
            new_values=undo_update,
            old_values=redo_update,
        )

        # Dispatch
        self.__dispatch__(
            "Update Items", redo, redo_event, undo, undo_event, history_adopters
        )

    def _clear(self):
        # type: () -> None
        """Clear dict."""
        with self._batch_context("Clear Items"):
            self._update(dict((k, DELETED) for k in self.__state))

    def _pop(self, key, fallback=MISSING):
        # type: (Hashable, Any) -> Any
        """Pop key"""
        if key not in self.__state:
            if fallback is MISSING:
                raise KeyError(key)
            return fallback
        value = self.__state[key]
        with self._batch_context("Remove Item"):
            self._update({key: DELETED})
        return value

    def _popitem(self):
        # type: () -> Tuple[Hashable, Any]
        """Pop item."""
        if not self.__state:
            error = "dict is empty"
            raise KeyError(error)
        key = next(iter(self.__state))
        with self._batch_context("Remove Item"):
            value = self._pop(key)
        return key, value

    def _setdefault(self, key, value):
        # type: (Hashable, Any) -> Any
        """Set default value for key."""
        if key in self.__state:
            return self.__state[key]
        self._update({key: value})
        return value

    def get(self, key, fallback=None):
        # type: (Hashable, Any) -> Any
        """Get value associated with key."""
        return self.__state.get(key, fallback)

    def has_key(self, key):
        # type: (Hashable) -> bool
        """Whether key is in the dict."""
        return key in self.__state

    def iteritems(self):
        # type: () -> Iterator[Tuple[str, Any]]
        """Iterate over items."""
        for item in iteritems(self.__state):
            yield item

    def iterkeys(self):
        # type: () -> Iterator[Hashable]
        """Iterate over keys."""
        for key in iterkeys(self.__state):
            yield key

    def itervalues(self):
        # type: () -> Iterator[Any]
        """Iterate over values."""
        for value in itervalues(self.__state):
            yield value

    def items(self):
        # type: () -> List[Tuple[str, Any]]
        """Get items."""
        return list(self.__state.items())

    def keys(self):
        # type: () -> List[Hashable]
        """Get keys."""
        return list(self.__state.keys())

    def values(self):
        # type: () -> List[Any]
        """Get values."""
        return list(self.__state.values())

    @property
    def default_type_name(self):
        # type: () -> str
        """Default type name."""
        value_type = self._parameters.value_type
        key_type = self._key_parameters.value_type

        if isinstance(value_type, type):
            value_type_name = value_type.__name__.capitalize()
        elif isinstance(value_type, string_types):
            value_type_name = value_type.split(".")[-1].capitalize()
        else:
            value_type_name = ""

        if isinstance(key_type, type):
            key_type_name = key_type.__name__.capitalize()
        elif isinstance(key_type, string_types):
            key_type_name = key_type.split(".")[-1].capitalize()
        else:
            key_type_name = ""

        if value_type_name and key_type_name:
            type_name = "{}To{}Dict".format(key_type_name, value_type_name)
        elif value_type_name or key_type_name:
            type_name = "{}Dict".format(value_type_name or key_type_name)
        else:
            type_name = "Dict"

        return type_name

    @property
    def __state(self):
        # type: () -> Dict
        """Internal state."""
        return cast(Dict, super(DictObject, self).__get_state__())

    @property
    def _key_parameters(self):
        # type: () -> ContainerObjectParameters
        """Container key parameters."""
        return self.__key_parameters


class MutableDictObject(DictObject):
    """Dict object with public mutable methods."""

    __slots__ = ()

    def __setitem__(self, key, value):
        # type: (Hashable, Any) -> None
        """Set value for key."""
        self.update({key: value})

    def __delitem__(self, key):
        # type: (Hashable) -> None
        """Delete value associated with key."""
        self.update({key: DELETED})

    def update(self, *args, **kwargs):
        # type: (Tuple[Mapping], Dict[str, Any]) -> None
        """Update."""
        self._update(*args, **kwargs)

    def clear(self):
        # type: () -> None
        """Clear dict."""
        return self._clear()

    def pop(self, key, fallback=MISSING):
        # type: (Hashable, Any) -> Any
        """Pop key"""
        return self._pop(key, fallback=fallback)

    def popitem(self):
        # type: () -> Tuple[Hashable, Any]
        """Pop item."""
        return self._popitem()

    def setdefault(self, key, value):
        # type: (Hashable, Any) -> Any
        """Set default value for key."""
        return self._setdefault(key, value)


class DictProxyObject(DictObject):
    """Read-only dict object that reflects the values of another dict object."""

    __slots__ = ("__source", "__reaction_phase")

    def __init__(
        self,
        source=None,  # type: Optional[DictObject]
        source_factory=None,  # type: Optional[Callable]
        reaction_phase=EventPhase.POST,  # type: EventPhase
        value_factory=None,  # type: Optional[Callable]
        comparable=True,  # type: bool
        represented=False,  # type: bool
        printed=True,  # type: bool
        parent=True,  # type: bool
        history=True,  # type: bool
        type_name=None,  # type: Optional[str]
        key_parent=True,  # type: bool
        key_history=True,  # type: bool
        reaction=None,  # type: Optional[Callable]
    ):
        if source is None:
            if source_factory is None:
                error = "need to provide exactly one of 'source' or 'source_factory'"
                raise ValueError(error)
            source = source_factory()
        elif source_factory is not None:
            error = "can't provide both 'source' and 'source_factory'"
            raise ValueError(error)

        assert_is_instance(source, DictObject)
        assert_is_instance(reaction_phase, EventPhase)

        parent = bool(parent) if parent is not None else not source.parent
        history = bool(history) if history is not None else not source.history
        key_parent = bool(
            key_parent if key_parent is not None else not source.key_parent
        )
        key_history = bool(
            key_history if key_history is not None else not source.key_history
        )

        if getattr(source, "_parameters").parent and parent:
            error = "both source and proxy container objects have 'parent' set to True"
            raise ValueError(error)
        if getattr(source, "_parameters").history and history:
            error = "both source and proxy container objects have 'history' set to True"
            raise ValueError(error)
        if getattr(source, "_key_parameters").key_parent and key_parent:
            error = (
                "both source and proxy container objects have 'key_parent' set to True"
            )
            raise ValueError(error)
        if getattr(source, "_key_parameters").key_history and key_history:
            error = (
                "both source and proxy container objects have 'key_history' set to True"
            )
            raise ValueError(error)

        super(DictProxyObject, self).__init__(
            value_type=None,
            value_factory=value_factory,
            exact_value_type=None,
            default_module=None,
            accepts_none=None,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=parent,
            history=history,
            type_name=type_name,
            reaction=reaction,
            key_parent=key_parent,
            key_history=key_history,
        )

        self.__source = source
        self.__reaction_phase = reaction_phase

        self._extend(source)
        source.events.add_listener(self)

    def __react__(self, event, phase):
        # type: (BaseObjectEvent, EventPhase) -> None
        """React to an event."""
        if isinstance(event, BaseObjectEvent) and event.obj is self._source:
            if phase is self.__reaction_phase:
                if type(event) is DictUpdateEvent:
                    event = cast(DictUpdateEvent, event)
                    self._update(event.new_values)

    @property
    def _source(self):
        # type: () -> DictObject
        """Source dict object."""
        return self.__source

    @property
    def reaction_phase(self):
        # type: () -> EventPhase
        """Phase in which the reaction takes place."""
        return self.__reaction_phase
