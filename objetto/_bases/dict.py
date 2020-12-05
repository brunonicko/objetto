# -*- coding: utf-8 -*-
"""Base dictionary classes."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from slotted import SlottedMapping, SlottedMutableMapping

from .bases import (
    MISSING,
    BaseCollection,
    BaseInteractiveCollection,
    BaseMutableCollection,
    BaseProtectedCollection,
    Generic,
    final,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        ItemsView,
        Iterable,
        Iterator,
        KeysView,
        Mapping,
        Optional,
        Tuple,
        Union,
        ValuesView,
    )

__all__ = [
    "BaseDict",
    "BaseProtectedDict",
    "BaseInteractiveDict",
    "BaseMutableDict",
]


KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.
VT_co = TypeVar("VT_co", covariant=True)  # Value type covariant containers.


class BaseDict(BaseCollection[KT], SlottedMapping, Generic[KT, VT_co]):
    """
    Base dictionary collection.

    Inherits from:
      - :class:`objetto.bases.BaseCollection`
      - :class:`slotted.SlottedMapping`
      - :class:`typing.Generic`

    Inherited By:
      - :class:`objetto.bases.BaseProtectedDict`
    """

    __slots__ = ()

    def __hash__(self):
        """
        Prevent hashing (not hashable by default).

        :raises TypeError: Not hashable.
        """
        error = "unhashable type: '{}'".format(type(self).__fullname__)
        raise TypeError(error)

    @abstractmethod
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.

        :return: True if equal.
        :rtype: bool

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def __reversed__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        :rtype: collections.abc.Iterator[collections.abc.Hashable]

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def __getitem__(self, key):
        # type: (KT) -> VT_co
        """
        Get value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Value.

        :raises KeyError: Key is not present.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def get(self, key, fallback=None):
        # type: (KT, Any) -> Union[VT_co, Any]
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param fallback: Fallback value.

        :return: Value or fallback value.

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def iteritems(self):
        # type: () -> Iterator[Tuple[KT, VT_co]]
        """
        Iterate over items.

        :return: Items iterator.
        :rtype: collections.abc.Iterator[tuple[collections.abc.Hashable, Any]]

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        :rtype: collections.abc.Iterator[collections.abc.Hashable]

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def itervalues(self):
        # type: () -> Iterator[VT_co]
        """
        Iterate over values.

        :return: Values iterator.
        :rtype: collections.abc.Iterator

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @final
    def items(self):
        # type: () -> ItemsView[KT, VT]
        """
        Get items.

        :return: Items.
        :rtype: collections.abc.ItemsView
        """
        return collections_abc.ItemsView(self)

    @final
    def keys(self):
        # type: () -> KeysView[KT]
        """
        Get keys.

        :return: Keys.
        :rtype: collections.abc.KeysView
        """
        return collections_abc.KeysView(self)

    @final
    def values(self):
        # type: () -> ValuesView[VT]
        """
        Get values.

        :return: Values.
        :rtype: collections.abc.ValuesView
        """
        return collections_abc.ValuesView(self)


# noinspection PyCallByClass
type.__setattr__(BaseDict, "__hash__", None)  # force non-hashable


# noinspection PyTypeChecker
_BPD = TypeVar("_BPD", bound="BaseProtectedDict")


class BaseProtectedDict(BaseDict[KT, VT], BaseProtectedCollection[KT]):
    """
    Base protected dictionary collection.

    Inherits from:
      - :class:`objetto.bases.BaseDict`
      - :class:`objetto.bases.BaseProtectedCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveDict`
      - :class:`objetto.bases.BaseMutableDict`
      - :class:`objetto.bases.BaseDictStructure`
    """

    __slots__ = ()

    @abstractmethod
    def _discard(self, key):
        # type: (_BPD, KT) -> _BPD
        """
        Discard key if it exists.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedDict

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _remove(self, key):
        # type: (_BPD, KT) -> _BPD
        """
        Delete existing key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedDict

        :raises KeyError: Key is not present.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def _set(self, key, value):
        # type: (_BPD, KT, VT) -> _BPD
        """
        Set value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedDict

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @overload
    @abstractmethod
    def _update(self, __m, **kwargs):
        # type: (_BPD, Mapping[KT, VT], VT) -> _BPD
        pass

    @overload
    @abstractmethod
    def _update(self, __m, **kwargs):
        # type: (_BPD, Iterable[Tuple[KT, VT]], VT) -> _BPD
        pass

    @overload
    @abstractmethod
    def _update(self, **kwargs):
        # type: (_BPD, VT) -> _BPD
        pass

    @abstractmethod
    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        :rtype: objetto.bases.BaseProtectedDict

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# noinspection PyTypeChecker
_BID = TypeVar("_BID", bound="BaseInteractiveDict")


# noinspection PyAbstractClass
class BaseInteractiveDict(BaseProtectedDict[KT, VT], BaseInteractiveCollection[KT]):
    """
    Base interactive dictionary collection.

    Inherits from:
      - :class:`objetto.bases.BaseProtectedDict`
      - :class:`objetto.bases.BaseInteractiveCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveDictStructure`
      - :class:`objetto.states.DictState`
    """

    __slots__ = ()

    @final
    def discard(self, key):
        # type: (_BID, KT) -> _BID
        """
        Discard key if it exists.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveDict
        """
        return self._discard(key)

    @final
    def remove(self, key):
        # type: (_BID, KT) -> _BID
        """
        Delete existing key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveDict

        :raises KeyError: Key is not present.
        """
        return self._remove(key)

    @final
    def set(self, key, value):
        # type: (_BID, KT, VT) -> _BID
        """
        Set value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveDict
        """
        return self._set(key, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (_BID, Mapping[KT, VT], VT) -> _BID
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (_BID, Iterable[Tuple[KT, VT]], VT) -> _BID
        pass

    @overload
    def update(self, **kwargs):
        # type: (_BID, VT) -> _BID
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        :rtype: objetto.bases.BaseInteractiveDict
        """
        return self._update(*args, **kwargs)


class BaseMutableDict(
    SlottedMutableMapping, BaseProtectedDict[KT, VT], BaseMutableCollection[KT]
):
    """
    Base mutable dictionary collection.

    Inherits from:
      - :class:`slotted.SlottedMutableMapping`
      - :class:`objetto.bases.BaseProtectedDict`
      - :class:`objetto.bases.BaseMutableCollection`

    Inherited By:
      - :class:`objetto.bases.BaseMutableDictStructure`
      - :class:`objetto.objects.ProxyDictObject`
    """

    __slots__ = ()

    @final
    def __setitem__(self, key, value):
        # type: (KT, VT) -> None
        """
        Set value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param value: Value.
        """
        self._set(key, value)

    @final
    def __delitem__(self, key):
        # type: (KT) -> None
        """
        Delete key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :raises KeyError: Key is not preset.
        """
        self._remove(key)

    @final
    def clear(self):
        # type: () -> None
        """Clear."""
        self._clear()

    @abstractmethod
    def pop(self, key, fallback=MISSING):
        # type: (KT, Any) -> Union[VT, Any]
        """
        Get value for key and remove it, return fallback value if key is not present.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param fallback: Fallback value.

        :return: Value or fallback value.

        :raises KeyError: Key is not present and fallback value not provided.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def popitem(self):
        # type: () -> Tuple[KT, VT]
        """
        Get item and discard key.

        :return: Item.
        :rtype: tuple[collections.abc.Hashable, Any]

        :raises KeyError: Dictionary is empty.
        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def setdefault(self, key, default=None):
        # type: (KT, Optional[VT]) -> Optional[VT]
        """
        Get the value for the specified key, insert key with default if not present.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param default: Default value.

        :return: Existing or default value.

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()

    @final
    def discard(self, key):
        # type: (KT) -> None
        """
        Discard key if it exists.

        :param key: Key.
        :type key: collections.abc.Hashable
        """
        self._discard(key)

    @final
    def remove(self, key):
        # type: (KT) -> None
        """
        Delete existing key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :raises KeyError: Key is not present.
        """
        self._remove(key)

    @final
    def set(self, key, value):
        # type: (KT, VT) -> None
        """
        Set value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param value: Value.
        """
        self._set(key, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (Mapping[KT, VT], VT) -> None
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (Iterable[Tuple[KT, VT]], VT) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (VT) -> None
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.
        """
        self._update(*args, **kwargs)
