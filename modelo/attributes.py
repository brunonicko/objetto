# -*- coding: utf-8 -*-
"""Attribute factories."""

from typing import Any, Optional, Callable, Iterable, Union

from .utils.type_checking import UnresolvedType
from .models.object import AttributeDelegate, AttributeDescriptor

__all__ = ["dependencies", "attribute", "constant_attribute"]


def dependencies(
    gets=(),  # type: Iterable[str, ...]
    sets=(),  # type: Iterable[str, ...]
    deletes=(),  # type: Iterable[str, ...]
    reset=True,  # type: bool
):
    # type: (...) -> Callable
    """Make a decorator that decorates a function into a delegate with dependencies."""
    return AttributeDelegate.get_decorator(
        gets=gets, sets=sets, deletes=deletes, reset=reset
    )


def attribute(
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
    # type: (...) -> AttributeDescriptor
    """Make an attribute descriptor."""
    return AttributeDescriptor(
        type=type,
        factory=factory,
        exact_type=exact_type,
        accepts_none=accepts_none,
        parent=parent,
        history=history,
        final=final,
        eq=eq,
        pprint=pprint,
        repr=repr,
        property=property,
    )


def constant_attribute(value, final=None):
    # type: (Any, Optional[bool]) -> AttributeDescriptor
    """Make a constant attribute descriptor."""
    descriptor = AttributeDescriptor(final=final, property=True)
    descriptor.getter(lambda _, _value=value: _value)
    return descriptor
