# -*- coding: utf-8 -*-
"""Immutable dict state."""

from typing import TYPE_CHECKING, TypeVar, cast, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from pyrsistent import pmap
from six import iteritems, iterkeys, itervalues

from .._bases import BaseInteractiveDict, final
from ..utils.custom_repr import custom_mapping_repr
from ..utils.recursive_repr import recursive_repr
from .bases import BaseState

if TYPE_CHECKING:
    from typing import Any, Iterable, Iterator, Mapping, Tuple, Type, Union

    from pyrsistent.typing import PMap

__all__ = ["DictState"]


KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.


# noinspection PyTypeChecker
_DS = TypeVar("_DS", bound="DictState")


@final
class DictState(BaseState[KT], BaseInteractiveDict[KT, VT]):
    """
    Immutable dictionary state.

    Inherits from:
      - :class:`objetto.bases.BaseState`
      - :class:`objetto.bases.BaseInteractiveDict`

    :param initial: Initial values.
    :type initial: collections.abc.Mapping or collections.abc.Iterable[\
tuple[collections.abc.Hashable, Any]]
    """

    __slots__ = ()

    @classmethod
    def _make(cls, internal=pmap()):
        # type: (Type[_DS], PMap[KT, VT]) -> _DS
        """
        Make new state by directly setting the internal state.

        :param internal: Internal state.
        :return: State.
        """
        return super(DictState, cls)._make(internal)

    @staticmethod
    def _make_internal(initial):
        # type: (Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]]) -> PMap[KT, VT]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pmap(initial)

    def __init__(self, initial=()):
        # type: (Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]]) -> None
        super(DictState, self).__init__(initial=initial)

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        :rtype: int
        """
        return super(DictState, self).__hash__()

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.

        :return: True if equal.
        :rtype: bool
        """
        if self is other:
            return True
        if not isinstance(other, collections_abc.Hashable):
            return self._internal == other
        if isinstance(other, DictState):
            return self._internal == other._internal
        return False

    def __contains__(self, key):
        # type: (Any) -> bool
        """
        Get whether key is present.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: True if contains.
        :rtype: bool
        """
        return key in self._internal

    def __iter__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        :rtype: collections.abc.Iterator[collections.abc.Hashable]
        """
        for key in iterkeys(self._internal):
            yield key

    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        :rtype: int
        """
        return len(self._internal)

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        :rtype: str
        """
        return custom_mapping_repr(
            self._internal,
            prefix="{}({{".format(type(self).__fullname__),
            suffix="})",
            sorting=True,
            sort_key=lambda i: hash(i[0]),
        )

    def __reversed__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        :rtype: collections.abc.Iterator[collections.abc.Hashable]
        """
        return reversed(list(self.__iter__()))

    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Value.

        :raises KeyError: Key is not present.
        """
        return self._internal[key]

    def _clear(self):
        # type: (_DS) -> _DS
        """
        Clear.

        :return: Transformed.
        :rtype: objetto.states.DictState
        """
        return self._make()

    def _discard(self, key):
        # type: (_DS, KT) -> _DS
        """
        Discard key if it exists.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.states.DictState
        """
        return self._make(self._internal.discard(key))

    def _remove(self, key):
        # type: (_DS, KT) -> _DS
        """
        Delete existing key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.states.DictState

        :raises KeyError: Key is not present.
        """
        return self._make(self._internal.remove(key))

    def _set(self, key, value):
        # type: (_DS, KT, VT) -> _DS
        """
        Set value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.states.DictState
        """
        return self._make(self._internal.set(key, value))

    @overload
    def _update(self, __m, **kwargs):
        # type: (_DS, Mapping[KT, VT], VT) -> _DS
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (_DS, Iterable[Tuple[KT, VT]], VT) -> _DS
        pass

    @overload
    def _update(self, **kwargs):
        # type: (_DS, VT) -> _DS
        pass

    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        :rtype: objetto.states.DictState
        """
        return self._make(self._internal.update(dict(*args, **kwargs)))

    def get(self, key, fallback=None):
        # type: (KT, Any) -> Union[VT, Any]
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param fallback: Fallback value.

        :return: Value or fallback value.
        """
        return self._internal.get(key, fallback)

    def iteritems(self):
        # type: () -> Iterator[Tuple[KT, VT]]
        """
        Iterate over items.

        :return: Items iterator.
        :rtype: collections.abc.Iterator[tuple[collections.abc.Hashable, Any]]
        """
        for key, value in iteritems(self._internal):
            yield key, value

    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        :rtype: collections.abc.Iterator[collections.abc.Hashable]
        """
        for key in iterkeys(self._internal):
            yield key

    def itervalues(self):
        # type: () -> Iterator[VT]
        """
        Iterate over values.

        :return: Values iterator.
        :rtype: collections.abc.Iterator
        """
        for value in itervalues(self._internal):
            yield value

    def find_with_attributes(self, **attributes):
        # type: (Any) -> VT
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.

        :return: Value that has matching attributes.

        :raises ValueError: No attributes provided or no match found.
        """
        if not attributes:
            error = "no attributes provided"
            raise ValueError(error)
        for value in itervalues(self._internal):
            for a_name, a_value in iteritems(attributes):
                if not hasattr(value, a_name) or getattr(value, a_name) != a_value:
                    break
            else:
                return value
        error = "could not find a match for {}".format(
            custom_mapping_repr(
                attributes,
                prefix="(",
                template="{key}={value}",
                suffix=")",
                key_repr=str,
            ),
        )
        raise ValueError(error)

    @property
    def _internal(self):
        # type: () -> PMap[KT, VT]
        """Internal values."""
        return cast("PMap[KT, VT]", super(DictState, self)._internal)
