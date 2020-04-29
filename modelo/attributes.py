# -*- coding: utf-8 -*-
"""Attribute factories."""

from typing import Any, Optional, Callable, Iterable, Union, Tuple

from ._base.constants import SpecialValue
from ._components.attributes import AttributeDelegate
from ._components.broadcaster import EventPhase
from ._models.base import HistoryDescriptor
from ._models.object import AttributeDescriptor, AttributeDescriptorDependencyPromise
from ._models.sequence import MutableSequenceModel, SequenceProxyModel
from ._models.mapping import MutableMappingModel, MappingProxyModel
from ._models.set import MutableSetModel, SetProxyModel
from .utils.type_checking import UnresolvedType as UType

__all__ = [
    "dependencies",
    "attribute",
    "history_attribute",
    "constant_attribute",
    "permanent_attribute",
    "protected_attribute_pair",
    "sequence_attribute",
    "protected_sequence_attribute_pair",
    "mapping_attribute",
    "protected_mapping_attribute_pair",
    "set_attribute",
    "protected_set_attribute_pair",
]


def dependencies(
    gets=(),  # type: Iterable[Union[str, AttributeDescriptor], ...]
    sets=(),  # type: Iterable[Union[str, AttributeDescriptor], ...]
    deletes=(),  # type: Iterable[Union[str, AttributeDescriptor], ...]
    reset=True,  # type: bool
):
    # type: (...) -> Callable
    """Make a decorator that decorates a function into a delegate with dependencies."""
    gets = frozenset(
        AttributeDescriptorDependencyPromise(d)
        if isinstance(d, AttributeDescriptor)
        else d
        for d in gets
    )
    sets = frozenset(
        AttributeDescriptorDependencyPromise(d)
        if isinstance(d, AttributeDescriptor)
        else d
        for d in sets
    )
    deletes = frozenset(
        AttributeDescriptorDependencyPromise(d)
        if isinstance(d, AttributeDescriptor)
        else d
        for d in deletes
    )
    return AttributeDelegate.get_decorator(
        gets=gets, sets=sets, deletes=deletes, reset=reset
    )


def attribute(
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
    default=SpecialValue.MISSING,  # type: Any
    default_factory=None,  # type: Optional[Callable]
    parent=True,  # type: bool
    history=True,  # type: bool
    final=False,  # type: bool
):
    # type: (...) -> AttributeDescriptor
    """Make an attribute."""
    return AttributeDescriptor(
        value_type=value_type,
        value_factory=value_factory,
        exact_value_type=exact_value_type,
        default_module=default_module,
        accepts_none=accepts_none,
        comparable=comparable,
        represented=represented,
        printed=printed,
        delegated=delegated,
        settable=settable,
        deletable=deletable,
        default=default,
        default_factory=default_factory,
        parent=parent,
        history=history,
        final=final,
    )


def history_attribute(size=500):
    # type: (int) -> HistoryDescriptor
    """Make a history attribute."""
    return HistoryDescriptor(size=size)


def constant_attribute(value, final=None):
    # type: (Any, Optional[bool]) -> AttributeDescriptor
    """Make a constant attribute."""
    descriptor = attribute(final=final, delegated=True, parent=False, history=False)
    descriptor.getter(lambda _, _value=value: _value)
    return descriptor


def permanent_attribute(
    value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    value_factory=None,  # type: Optional[Callable]
    exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    default_module=None,  # type: Optional[str]
    accepts_none=None,  # type: Optional[bool]
    comparable=None,  # type: Optional[bool]
    represented=False,  # type: Optional[bool]
    printed=None,  # type: Optional[bool]
    default=SpecialValue.MISSING,  # type: Any
    default_factory=None,  # type: Optional[Callable]
    parent=True,  # type: bool
    history=True,  # type: bool
    final=False,  # type: bool
):
    # type: (...) -> AttributeDescriptor
    """Make an read-only attribute that initializes with a default/default factory."""
    if default is SpecialValue.MISSING and default_factory is None:
        error = "need to specify 'default' or 'default_factory' for permanent attribute"
        raise ValueError(error)

    return attribute(
        value_type=value_type,
        value_factory=value_factory,
        exact_value_type=exact_value_type,
        default_module=default_module,
        accepts_none=accepts_none,
        comparable=comparable,
        represented=represented,
        printed=printed,
        delegated=False,
        settable=False,
        deletable=False,
        default=default,
        default_factory=default_factory,
        parent=parent,
        history=history,
        final=final,
    )


def protected_attribute_pair(
    value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    value_factory=None,  # type: Optional[Callable]
    exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    default_module=None,  # type: Optional[str]
    accepts_none=None,  # type: Optional[bool]
    comparable=None,  # type: Optional[bool]
    represented=False,  # type: Optional[bool]
    printed=None,  # type: Optional[bool]
    default=SpecialValue.MISSING,  # type: Any
    default_factory=None,  # type: Optional[Callable]
    parent=True,  # type: bool
    history=True,  # type: bool
    final=False,  # type: bool
):
    # type: (...) -> Tuple[AttributeDescriptor, AttributeDescriptor]
    """Make two attributes, one internal and one external (read-only)."""
    internal = attribute(
        value_type=value_type,
        value_factory=value_factory,
        exact_value_type=exact_value_type,
        default_module=default_module,
        accepts_none=accepts_none,
        comparable=False,
        represented=False,
        printed=False,
        delegated=False,
        default=default,
        default_factory=default_factory,
        parent=False,
        history=history,
        final=final,
    )
    external = attribute(
        value_type=None,
        value_factory=None,
        exact_value_type=None,
        default_module=None,
        accepts_none=None,
        comparable=comparable,
        represented=represented,
        printed=printed,
        delegated=True,
        default=SpecialValue.MISSING,
        default_factory=None,
        parent=parent,
        history=False,
        final=final,
    )
    external.getter(
        AttributeDelegate(
            lambda d, _i=internal: getattr(d, _i.name),
            gets=(AttributeDescriptorDependencyPromise(internal),),
        )
    )
    return internal, external


def sequence_attribute(
    value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    value_factory=None,  # type: Optional[Callable]
    exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    default_module=None,  # type: Optional[str]
    accepts_none=None,  # type: Optional[bool]
    comparable=None,  # type: Optional[bool]
    represented=False,  # type: Optional[bool]
    printed=True,  # type: Optional[bool]
    parent=True,  # type: bool
    history=True,  # type: bool
    type_name=None,  # type: Optional[str]
    reaction=None,  # type: Optional[Callable]
    final=False,  # type: bool
):
    # type: (...) -> AttributeDescriptor
    """Make a sequence attribute."""

    def default_factory():
        return MutableSequenceModel(
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

    return permanent_attribute(
        comparable=comparable,
        represented=represented,
        printed=printed,
        default_factory=default_factory,
        parent=parent,
        history=history,
        final=final,
    )


def protected_sequence_attribute_pair(
    value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    value_factory=None,  # type: Optional[Callable]
    exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    default_module=None,  # type: Optional[str]
    accepts_none=None,  # type: Optional[bool]
    comparable=None,  # type: Optional[bool]
    represented=False,  # type: Optional[bool]
    printed=True,  # type: Optional[bool]
    parent=True,  # type: bool
    history=True,  # type: bool
    type_name=None,  # type: Optional[str]
    reaction=None,  # type: Optional[Callable]
    final=False,  # type: bool
    reaction_phase=EventPhase.POST,  # type: EventPhase
):
    # type: (...) -> Tuple[AttributeDescriptor, AttributeDescriptor]
    """Make two sequence attributes, one internal and one external (read-only)."""

    def default_factory():
        source = MutableSequenceModel(
            value_type=value_type,
            value_factory=value_factory,
            exact_value_type=exact_value_type,
            default_module=default_module,
            accepts_none=accepts_none,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=False,
            history=history,
            type_name=type_name,
            reaction=reaction,
        )
        proxy_type_name = "ReadOnly{}".format(
            source.default_type_name if type_name is None else type_name
        )
        return SequenceProxyModel(
            source=source,
            reaction_phase=reaction_phase,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=parent,
            history=False,
            type_name=proxy_type_name,
        )

    external = permanent_attribute(
        comparable=comparable,
        represented=represented,
        printed=printed,
        default_factory=default_factory,
        parent=parent,
        history=False,
        final=final,
    )

    internal = attribute(
        comparable=False,
        represented=False,
        printed=False,
        delegated=True,
        parent=False,
        history=history,
        final=final,
    )
    internal.getter(
        AttributeDelegate(
            lambda d, _e=external: getattr(getattr(d, _e.name), "_source"),
            gets=(AttributeDescriptorDependencyPromise(external),),
        )
    )

    return internal, external


def mapping_attribute(
    value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    value_factory=None,  # type: Optional[Callable]
    exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    default_module=None,  # type: Optional[str]
    accepts_none=None,  # type: Optional[bool]
    comparable=None,  # type: Optional[bool]
    represented=False,  # type: Optional[bool]
    printed=True,  # type: Optional[bool]
    parent=True,  # type: bool
    history=True,  # type: bool
    type_name=None,  # type: Optional[str]
    reaction=None,  # type: Optional[Callable]
    key_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    exact_key_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    key_accepts_none=None,  # type: Optional[bool]
    key_parent=True,  # type: bool
    key_history=True,  # type: bool
    final=False,  # type: bool
):
    # type: (...) -> AttributeDescriptor
    """Make a mapping attribute."""

    def default_factory():
        return MutableMappingModel(
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
            key_type=key_type,
            exact_key_type=exact_key_type,
            key_accepts_none=key_accepts_none,
            key_parent=key_parent,
            key_history=key_history,
        )

    return permanent_attribute(
        comparable=comparable,
        represented=represented,
        printed=printed,
        default_factory=default_factory,
        parent=parent,
        history=history,
        final=final,
    )


def protected_mapping_attribute_pair(
    value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    value_factory=None,  # type: Optional[Callable]
    exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    default_module=None,  # type: Optional[str]
    accepts_none=None,  # type: Optional[bool]
    comparable=None,  # type: Optional[bool]
    represented=False,  # type: Optional[bool]
    printed=True,  # type: Optional[bool]
    parent=True,  # type: bool
    history=True,  # type: bool
    type_name=None,  # type: Optional[str]
    reaction=None,  # type: Optional[Callable]
    key_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    exact_key_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    key_accepts_none=None,  # type: Optional[bool]
    key_parent=True,  # type: bool
    key_history=True,  # type: bool
    final=False,  # type: bool
    reaction_phase=EventPhase.POST,  # type: EventPhase
):
    # type: (...) -> Tuple[AttributeDescriptor, AttributeDescriptor]
    """Make two mapping attributes, one internal and one external (read-only)."""

    def default_factory():
        source = MutableMappingModel(
            value_type=value_type,
            value_factory=value_factory,
            exact_value_type=exact_value_type,
            default_module=default_module,
            accepts_none=accepts_none,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=False,
            history=history,
            type_name=type_name,
            reaction=reaction,
            key_type=key_type,
            exact_key_type=exact_key_type,
            key_accepts_none=key_accepts_none,
            key_parent=False,
            key_history=key_history,
        )
        proxy_type_name = "ReadOnly{}".format(
            source.default_type_name if type_name is None else type_name
        )
        return MappingProxyModel(
            source=source,
            reaction_phase=reaction_phase,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=parent,
            type_name=proxy_type_name,
            history=False,
            key_parent=key_parent,
            key_history=False,
        )

    external = permanent_attribute(
        comparable=comparable,
        represented=represented,
        printed=printed,
        default_factory=default_factory,
        parent=parent,
        history=False,
        final=final,
    )

    internal = attribute(
        comparable=False,
        represented=False,
        printed=False,
        delegated=True,
        parent=False,
        history=history,
        final=final,
    )
    internal.getter(
        AttributeDelegate(
            lambda d, _e=external: getattr(getattr(d, _e.name), "_source"),
            gets=(AttributeDescriptorDependencyPromise(external),),
        )
    )

    return internal, external


def set_attribute(
    value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    value_factory=None,  # type: Optional[Callable]
    exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    default_module=None,  # type: Optional[str]
    accepts_none=None,  # type: Optional[bool]
    comparable=None,  # type: Optional[bool]
    represented=False,  # type: Optional[bool]
    printed=True,  # type: Optional[bool]
    parent=True,  # type: bool
    history=True,  # type: bool
    type_name=None,  # type: Optional[str]
    reaction=None,  # type: Optional[Callable]
    final=False,  # type: bool
):
    # type: (...) -> AttributeDescriptor
    """Make a set attribute."""

    def default_factory():
        return MutableSetModel(
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

    return permanent_attribute(
        comparable=comparable,
        represented=represented,
        printed=printed,
        default_factory=default_factory,
        parent=parent,
        history=history,
        final=final,
    )


def protected_set_attribute_pair(
    value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    value_factory=None,  # type: Optional[Callable]
    exact_value_type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
    default_module=None,  # type: Optional[str]
    accepts_none=None,  # type: Optional[bool]
    comparable=None,  # type: Optional[bool]
    represented=False,  # type: Optional[bool]
    printed=True,  # type: Optional[bool]
    parent=True,  # type: bool
    history=True,  # type: bool
    type_name=None,  # type: Optional[str]
    reaction=None,  # type: Optional[Callable]
    final=False,  # type: bool
    reaction_phase=EventPhase.POST,  # type: EventPhase
):
    # type: (...) -> Tuple[AttributeDescriptor, AttributeDescriptor]
    """Make two set attributes, one internal and one external (read-only)."""

    def default_factory():
        source = MutableSetModel(
            value_type=value_type,
            value_factory=value_factory,
            exact_value_type=exact_value_type,
            default_module=default_module,
            accepts_none=accepts_none,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=False,
            history=history,
            type_name=type_name,
            reaction=reaction,
        )
        proxy_type_name = "ReadOnly{}".format(
            source.default_type_name if type_name is None else type_name
        )
        return SetProxyModel(
            source=source,
            reaction_phase=reaction_phase,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=parent,
            history=False,
            type_name=proxy_type_name,
        )

    external = permanent_attribute(
        comparable=comparable,
        represented=represented,
        printed=printed,
        default_factory=default_factory,
        parent=parent,
        history=False,
        final=final,
    )

    internal = attribute(
        comparable=False,
        represented=False,
        printed=False,
        delegated=True,
        parent=False,
        history=history,
        final=final,
    )
    internal.getter(
        AttributeDelegate(
            lambda d, _e=external: getattr(getattr(d, _e.name), "_source"),
            gets=(AttributeDescriptorDependencyPromise(external),),
        )
    )

    return internal, external
