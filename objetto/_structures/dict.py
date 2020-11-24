# -*- coding: utf-8 -*-
"""Dictionary structures."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, iterkeys, itervalues, with_metaclass

from .._bases import (
    Base,
    BaseInteractiveDict,
    BaseMutableDict,
    BaseProtectedDict,
    final,
)
from .._states import DictState
from ..utils.custom_repr import custom_mapping_repr
from ..utils.factoring import format_factory, import_factory, run_factory
from ..utils.type_checking import assert_is_instance, format_types, import_types
from .bases import (
    BaseAuxiliaryStructure,
    BaseAuxiliaryStructureMeta,
    BaseInteractiveAuxiliaryStructure,
    BaseMutableAuxiliaryStructure,
)

if TYPE_CHECKING:
    from typing import Any, Dict, Iterator, Optional, Tuple, Type, Union

    from ..utils.factoring import LazyFactory
    from ..utils.type_checking import LazyTypes

__all__ = [
    "KeyRelationship",
    "BaseDictStructureMeta",
    "BaseDictStructure",
    "BaseInteractiveDictStructure",
    "BaseMutableDictStructure",
]


KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.


@final
class KeyRelationship(Base):
    """
    Relationship between a dictionary auxiliary structure and their keys.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Key factory.
    """

    __slots__ = (
        "__hash",
        "__types",
        "__subtypes",
        "__checked",
        "__module",
        "__factory",
    )

    def __init__(
        self,
        types=(),  # type: LazyTypes
        subtypes=False,  # type: bool
        checked=True,  # type: bool
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
    ):
        self.__hash = None  # type: Optional[int]
        self.__types = format_types(types, module=module)
        self.__subtypes = bool(subtypes)
        self.__checked = bool(checked)
        self.__module = module
        self.__factory = format_factory(factory, module=module)

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        if self.__hash is None:
            self.__hash = hash(frozenset(iteritems(self.to_dict())))
        return self.__hash

    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare with another object for equality.

        :param other: Another object.
        :return: True if considered equal.
        """
        if type(self) is not type(other):
            return False
        assert isinstance(other, KeyRelationship)
        return self.to_dict() == other.to_dict()

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_mapping_repr(
            self.to_dict(),
            prefix="{}(".format(type(self).__name__),
            template="{key}={value}",
            suffix=")",
            sorting=True,
            key_repr=str,
        )

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        """
        return {
            "types": frozenset(import_types(self.types)),
            "subtypes": self.subtypes,
            "checked": self.checked,
            "module": self.module,
            "factory": import_factory(self.factory),
        }

    def fabricate_key(self, key, factory=True, **kwargs):
        # type: (Any, bool, Any) -> Any
        """
        Perform type check and run key through factory.

        :param key: Key.
        :param factory: Whether to run value through factory.
        :param kwargs: Keyword arguments to be passed to the factory.
        :return: Fabricated value.
        """
        if factory and self.factory is not None:
            key = run_factory(self.factory, args=(key,), kwargs=kwargs)
        if self.types and self.checked:
            assert_is_instance(key, self.types, subtypes=self.subtypes)
        return key

    @property
    def types(self):
        # type: () -> LazyTypes
        """Types."""
        return self.__types

    @property
    def subtypes(self):
        # type: () -> bool
        """Whether to accept subtypes."""
        return self.__subtypes

    @property
    def checked(self):
        # type: () -> bool
        """Whether to perform runtime type check."""
        return self.__checked

    @property
    def module(self):
        # type: () -> Optional[str]
        """Module path for lazy types/factories."""
        return self.__module

    @property
    def factory(self):
        # type: () -> LazyFactory
        """Key factory."""
        return self.__factory

    @property
    def passthrough(self):
        # type: () -> bool
        """Whether does not perform type checks and has no factory."""
        return (not self.types or not self.checked) and self.factory is None


# noinspection PyAbstractClass
class BaseDictStructureMeta(BaseAuxiliaryStructureMeta):
    """Metaclass for :class:`DictStructure`."""

    def __init__(cls, name, bases, dct):
        super(BaseDictStructureMeta, cls).__init__(name, bases, dct)

        # Check key relationship type.
        assert_is_instance(
            getattr(cls, "_key_relationship"),
            cls._key_relationship_type,
            subtypes=False,
        )

    @property
    @final
    def _key_relationship_type(cls):
        # type: () -> Type[KeyRelationship]
        """Relationship type."""
        return KeyRelationship


class BaseDictStructure(
    with_metaclass(
        BaseDictStructureMeta,
        BaseAuxiliaryStructure[KT],
        BaseProtectedDict[KT, VT],
    )
):
    """Base dictionary structure."""

    __slots__ = ()

    _key_relationship = KeyRelationship()
    """Relationship for the keys."""

    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        if type(self)._relationship.represented:
            return custom_mapping_repr(
                self._state,
                prefix="{}({{".format(type(self).__fullname__),
                suffix="})",
            )
        else:
            return "<{}>".format(type(self).__fullname__)

    @final
    def __reversed__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        """
        return reversed(self._state)

    @final
    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Invalid key.
        """
        return self._state[key]

    @final
    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key in self._state:
            yield key

    @final
    def __contains__(self, key):
        # type: (Any) -> bool
        """
        Get whether key is present.

        :param key: Key.
        :return: True if contains.
        """
        return key in self._state

    @final
    def get(self, key, fallback=None):
        # type: (KT, Any) -> Union[VT, Any]
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._state.get(key, fallback)

    @final
    def iteritems(self):
        # type: () -> Iterator[Tuple[KT, VT]]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key, value in iteritems(self._state):
            yield key, value

    @final
    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in iterkeys(self._state):
            yield key

    @final
    def itervalues(self):
        # type: () -> Iterator[VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in itervalues(self._state):
            yield value

    @property
    @abstractmethod
    def _state(self):
        # type: () -> DictState[KT, VT]
        """Internal state."""
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseInteractiveDictStructure(
    BaseDictStructure[KT, VT],
    BaseInteractiveAuxiliaryStructure[KT],
    BaseInteractiveDict[KT, VT],
):
    """Base interactive dictionary structure."""

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableDictStructure(
    BaseDictStructure[KT, VT],
    BaseMutableAuxiliaryStructure[KT],
    BaseMutableDict[KT, VT],
):
    """Base mutable dictionary structure."""

    __slots__ = ()
