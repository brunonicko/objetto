# -*- coding: utf-8 -*-

from typing import Any, Optional, Callable, Iterable, Union

from ._type_checking import UType
from ._constants import SpecialValue
from ._model import AttributeDelegate, AttributeDescriptor


def dependencies(
    gets=(),  # type: Iterable[str, ...]
    sets=(),  # type: Iterable[str, ...]
    deletes=(),  # type: Iterable[str, ...]
    reset=True,  # type: bool
):
    # type: (...) -> Callable
    """Get a decorator to decorate a function with attribute dependencies."""
    return AttributeDelegate.get_decorator(
        gets=gets, sets=sets, deletes=deletes, reset=reset
    )


def attribute(
    type=None,  # type: Optional[Union[UType, Iterable[UType, ...]]]
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
