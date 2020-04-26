# -*- coding: utf-8 -*-
"""Mapping model."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc
from six import with_metaclass, iteritems, iterkeys, itervalues
from typing import (
    Dict,
    Callable,
    Any,
    Optional,
    FrozenSet,
    Mapping,
    Hashable,
    Iterable,
    Iterator,
    Union,
    Tuple,
    List,
    cast,
)
from collections import Counter

from .._base.constants import SpecialValue
from .._components.broadcaster import EventPhase
from ..utils.type_checking import UnresolvedType as UType
from ..utils.type_checking import assert_is_instance
from ..utils.partial import Partial
from ..utils.wrapped_dict import WrappedDict
from .base import Model, ModelEvent
from .container import ContainerModelMeta, ContainerModel, ContainerModelParameters

__all__ = [
    "MappingUpdateEvent",
    "MappingModelMeta",
    "MappingModel",
    "MutableMappingModel",
    "MappingProxyModel",
]


class MappingUpdateEvent(ModelEvent):
    """Emitted when key-value pairs in a mapping model change."""

    __slots__ = ("__new_values", "__old_values")

    def __init__(
        self,
        model,  # type: MappingModel
        adoptions,  # type: FrozenSet[Model, ...]
        releases,  # type: FrozenSet[Model, ...]
        new_values,  # type: Mapping[Hashable, Any]
        old_values,  # type: Mapping[Hashable, Any]
    ):
        # type: (...) -> None
        """Initialize with new values and old values."""
        super(MappingUpdateEvent, self).__init__(model, adoptions, releases)
        self.__new_values = new_values
        self.__old_values = old_values

    def __eq_equal_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should compared using equality."""
        return super(MappingUpdateEvent, self).__eq_equal_properties__() + (
            "new_values",
            "old_values",
        )

    def __repr_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__repr__'."""
        return super(MappingUpdateEvent, self).__repr_properties__() + (
            "new_values",
            "old_values",
        )

    def __str_properties__(self):
        # type: () -> Tuple[str, ...]
        """Get names of properties that should show up in the result of '__str__'."""
        return super(MappingUpdateEvent, self).__str_properties__() + (
            "new_values",
            "old_values",
        )

    @property
    def new_values(self):
        # type: () -> Mapping[Hashable, Any]
        """New values."""
        return self.__new_values

    @property
    def old_values(self):
        # type: () -> Mapping[Hashable, Any]
        """Old values."""
        return self.__old_values


class MappingModelMeta(ContainerModelMeta):
    """Metaclass for 'MappingModel'."""


class MappingModel(with_metaclass(MappingModelMeta, ContainerModel)):
    """Model that stores values in a mapping."""

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
        key_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        exact_key_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
        key_accepts_none=None,  # type: Optional[bool]
        key_parent=True,  # type: bool
        key_history=True,  # type: bool
    ):
        # type: (...) -> None
        """Initialize with value parameters and key parameters."""
        super(MappingModel, self).__init__(
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
        )
        self.__key_parameters = ContainerModelParameters(
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
        mapping_update = WrappedDict(processed_update)
        mapping_revert = WrappedDict(processed_revert)
        for key, value in iteritems(update):
            key = self._key_parameters.fabricate(
                key, accepts_missing=False, accepts_deleted=False
            )
            value = self._parameters.fabricate(
                value, accepts_deleted=True, accepts_missing=False
            )
            if value is SpecialValue.DELETED:
                if key not in self.__state:
                    raise KeyError(key)
                processed_revert[key] = self.__state[key]
            elif key not in self.__state:
                processed_revert[key] = SpecialValue.DELETED
            else:
                processed_revert[key] = self.__state[key]
            processed_update[key] = value

        return mapping_update, mapping_revert

    def __update(self, mapping_update):
        # type: (Mapping[Hashable, Any]) -> None
        """Update."""
        for key, value in iteritems(mapping_update):
            if value in (SpecialValue.MISSING, SpecialValue.DELETED):
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
        special_drop_values = SpecialValue.MISSING, SpecialValue.DELETED
        if self._key_parameters.parent or self._parameters.parent:
            for key, value in iteritems(redo_update):
                if value in special_drop_values:
                    if self._key_parameters.parent:
                        if isinstance(key, Model):
                            child_count[key] -= 1
                    if self._parameters.parent:
                        old_value = undo_update[key]
                        if isinstance(old_value, Model):
                            child_count[old_value] -= 1
                else:
                    if self._key_parameters.parent:
                        if (
                            isinstance(key, Model)
                            and undo_update[key] in special_drop_values
                        ):
                            child_count[key] += 1
                    if self._parameters.parent:
                        old_value = undo_update[key]
                        if isinstance(value, Model):
                            child_count[value] += 1
                        if isinstance(old_value, Model):
                            child_count[old_value] -= 1
        redo_children = hierarchy.prepare_children_updates(child_count)
        undo_children = ~redo_children

        # Prepare history adopters
        history_adopters = set()
        if self._key_parameters.history or self._parameters.history:
            for key, value in iteritems(redo_update):
                if self._key_parameters.history and isinstance(key, Model):
                    history_adopters.add(key)
                if self._parameters.history and isinstance(value, Model):
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
        redo_event = MappingUpdateEvent(
            model=self,
            adoptions=redo_children.adoptions,
            releases=redo_children.releases,
            new_values=redo_update,
            old_values=undo_update,
        )
        undo_event = MappingUpdateEvent(
            model=self,
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
        """Clear mapping."""
        with self._batch_context("Clear Items"):
            self._update(dict((k, SpecialValue.DELETED) for k in self.__state))

    def _pop(self, key, fallback=SpecialValue.MISSING):
        # type: (Hashable, Any) -> Any
        """Pop key"""
        if key not in self.__state:
            if fallback is SpecialValue.MISSING:
                raise KeyError(key)
            return fallback
        value = self.__state[key]
        with self._batch_context("Remove Item"):
            self._update({key: SpecialValue.DELETED})
        return value

    def _popitem(self):
        # type: () -> Tuple[Hashable, Any]
        """Pop item."""
        if not self.__state:
            error = "mapping is empty"
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
        """Whether key is in the mapping."""
        return self.__state.has_key(key)

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
    def __state(self):
        # type: () -> Dict
        """Internal state."""
        return cast(Dict, super(MappingModel, self).__get_state__())

    @property
    def _key_parameters(self):
        # type: () -> ContainerModelParameters
        """Container key parameters."""
        return self.__key_parameters


class MutableMappingModel(MappingModel):
    """Mapping model with public mutable methods."""

    __slots__ = ()

    def __setitem__(self, key, value):
        # type: (Hashable, Any) -> None
        """Set value for key."""
        self.update({key: value})

    def __delitem__(self, key):
        # type: (Hashable) -> None
        """Delete value associated with key."""
        self.update({key: SpecialValue.DELETED})

    def update(self, *args, **kwargs):
        # type: (Tuple[Mapping], Dict[str, Any]) -> None
        """Update."""
        self._update(*args, **kwargs)

    def clear(self):
        # type: () -> None
        """Clear mapping."""
        return self._clear()

    def pop(self, key, fallback=SpecialValue.MISSING):
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


class MappingProxyModel(MappingModel):
    """Read-only mapping model that reflects the values of another mapping model."""

    __slots__ = ("__source", "__reaction_phase")

    def __init__(
        self,
        source=None,  # type: Optional[MappingModel]
        source_factory=None,  # type: Optional[Callable]
        reaction_phase=EventPhase.POST,  # type: EventPhase
        value_factory=None,  # type: Optional[Callable]
        comparable=True,  # type: bool
        represented=False,  # type: bool
        printed=True,  # type: bool
        parent=True,  # type: bool
        history=True,  # type: bool
        key_parent=True,  # type: bool
        key_history=True,  # type: bool
    ):
        if source is None:
            if source_factory is None:
                error = "need to provide exactly one of 'source' or 'source_factory'"
                raise ValueError(error)
            source = source_factory()
        elif source_factory is not None:
            error = "can't provide both 'source' and 'source_factory'"
            raise ValueError(error)

        assert_is_instance(source, MappingModel)
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
            error = "both source and proxy container models have 'parent' set to True"
            raise ValueError(error)
        if getattr(source, "_parameters").history and history:
            error = "both source and proxy container models have 'history' set to True"
            raise ValueError(error)
        if getattr(source, "_key_parameters").key_parent and key_parent:
            error = (
                "both source and proxy container models have 'key_parent' set to True"
            )
            raise ValueError(error)
        if getattr(source, "_key_parameters").key_history and key_history:
            error = (
                "both source and proxy container models have 'key_history' set to True"
            )
            raise ValueError(error)

        super(MappingProxyModel, self).__init__(
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
            key_parent=key_parent,
            key_history=key_history,
        )

        self.__source = source
        self.__reaction_phase = reaction_phase

        self._extend(source)
        source.events.add_listener(self)

    def __react__(self, event, phase):
        # type: (ModelEvent, EventPhase) -> None
        """React to an event."""
        if isinstance(event, ModelEvent) and event.model is self._source:
            if phase is self.__reaction_phase:
                if type(event) is MappingUpdateEvent:
                    event = cast(MappingUpdateEvent, event)
                    self._update(event.new_values)

    @property
    def _source(self):
        # type: () -> MappingModel
        """Source mapping model."""
        return self.__source

    @property
    def reaction_phase(self):
        # type: () -> EventPhase
        """Phase in which the reaction takes place."""
        return self.__reaction_phase
