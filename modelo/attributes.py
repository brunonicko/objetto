# -*- coding: utf-8 -*-
"""Attribute factories."""

from typing import Any, Optional, Callable, Iterable, Union

from ._components.attributes import AttributeDelegate
from ._models.object import AttributeDescriptor, AttributeDescriptorDependencyPromise
from .utils.type_checking import UnresolvedType as UType

__all__ = ["dependencies", "attribute", "constant_attribute"]


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
    parent=True,  # type: bool
    history=True,  # type: bool
    final=False,  # type: bool
):
    # type: (...) -> AttributeDescriptor
    """Make an attribute descriptor."""
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
        parent=parent,
        history=history,
        final=final,
    )


def constant_attribute(value, final=None):
    # type: (Any, Optional[bool]) -> AttributeDescriptor
    """Make a constant attribute descriptor."""
    descriptor = AttributeDescriptor(
        final=final, delegated=True, parent=False, history=False
    )
    descriptor.getter(lambda _, _value=value: _value)
    return descriptor
