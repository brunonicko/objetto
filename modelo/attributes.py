# -*- coding: utf-8 -*-
"""Attribute factories."""

from typing import Any, Optional, Callable, Iterable, Union, Tuple

from ._base.constants import SpecialValue
from ._components.attributes import AttributeDelegate
from ._models.object import AttributeDescriptor, AttributeDescriptorDependencyPromise
from ._models.sequence import MutableSequenceModel, SequenceProxyModel
from .utils.type_checking import UnresolvedType as UType

__all__ = [
    "dependencies",
    "attribute",
    "constant_attribute",
    "default_attribute",
    "protected_attribute_pair",
    "sequence_attribute",
    "protected_sequence_attribute_pair",
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


def constant_attribute(value, final=None):
    # type: (Any, Optional[bool]) -> AttributeDescriptor
    """Make a constant attribute."""
    descriptor = attribute(final=final, delegated=True, parent=False, history=False)
    descriptor.getter(lambda _, _value=value: _value)
    return descriptor


def default_attribute(
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
        )

    return default_attribute(
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
    final=False,  # type: bool
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
        )
        return SequenceProxyModel(
            source=source,
            comparable=comparable,
            represented=represented,
            printed=printed,
            parent=parent,
            history=False,
        )

    external = default_attribute(
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
