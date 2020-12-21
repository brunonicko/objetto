# -*- coding: utf-8 -*-
"""Dictionary structures."""

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, cast

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, iterkeys, itervalues, string_types, with_metaclass

from .._bases import (
    BaseHashable,
    BaseInteractiveDict,
    BaseMutableDict,
    BaseProtectedDict,
    final,
)
from .._states import DictState
from ..utils.custom_repr import custom_mapping_repr
from ..utils.factoring import format_factory, import_factory, run_factory
from ..utils.recursive_repr import recursive_repr
from ..utils.reraise_context import ReraiseContext
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
class KeyRelationship(BaseHashable):
    """
    Relationship between a dictionary auxiliary structure and their keys.

    Inherits from:
      - :class:`objetto.bases.BaseHashable`

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Key factory.
    :type factory: str or collections.abc.Callable or None

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
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
        checked=None,  # type: Optional[bool]
        module=None,  # type: Optional[str]
        factory=None,  # type: LazyFactory
    ):

        # 'module'
        with ReraiseContext(TypeError, "'module' parameter"):
            assert_is_instance(module, string_types + (None,))
        module = module or None

        # 'types' and 'checked'
        with ReraiseContext((ValueError, TypeError), "'types' parameter"):
            types = format_types(types, module=module)
        if not types:
            if checked:
                error = "did not provide any 'types' but 'checked' is True"
                raise ValueError(error)
            if checked is None:
                checked = False
        else:
            if checked is None:
                checked = True
        checked = bool(checked)

        # 'factory'
        with ReraiseContext((ValueError, TypeError), "'factory' parameter"):
            factory = format_factory(factory, module=module)

        self.__hash = None  # type: Optional[int]
        self.__types = types
        self.__subtypes = bool(subtypes)
        self.__checked = checked
        self.__module = module
        self.__factory = factory

    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        :rtype: int
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
        :rtype: bool
        """
        if self is other:
            return True
        if type(self) is not type(other):
            return False
        assert isinstance(other, KeyRelationship)
        return self.to_dict() == other.to_dict()

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        :rtype: str
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
        :rtype: dict[str, Any]
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
        :type key: collections.abc.Hashable

        :param factory: Whether to run value through factory.
        :type factory: bool

        :param kwargs: Keyword arguments to be passed to the factory.

        :return: Fabricated value.
        :type key: collections.abc.Hashable
        """
        if factory and self.factory is not None:
            key = run_factory(self.factory, args=(key,), kwargs=kwargs)
        if self.types and self.checked:
            assert_is_instance(key, self.types, subtypes=self.subtypes)
        return key

    @property
    def types(self):
        # type: () -> LazyTypes
        """
        Types.

        :rtype: tuple[str or type]
        """
        return self.__types

    @property
    def subtypes(self):
        # type: () -> bool
        """
        Whether to accept subtypes.

        :rtype: bool
        """
        return self.__subtypes

    @property
    def checked(self):
        # type: () -> bool
        """
        Whether to perform runtime type check.

        :rtype: bool
        """
        return self.__checked

    @property
    def module(self):
        # type: () -> Optional[str]
        """
        Module path for lazy types/factories.

        :rtype: str or None
        """
        return self.__module

    @property
    def factory(self):
        # type: () -> LazyFactory
        """
        Key factory.

        :rtype: str or collections.abc.Callable or None
        """
        return self.__factory

    @property
    def passthrough(self):
        # type: () -> bool
        """
        Whether does not perform type checks and has no factory.

        :rtype: bool
        """
        return (not self.types or not self.checked) and self.factory is None


# noinspection PyAbstractClass
class BaseDictStructureMeta(BaseAuxiliaryStructureMeta):
    """
    Metaclass for :class:`objetto.bases.BaseDictStructure`.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructureMeta`

    Inherited by:
      - :class:`objetto.data.DictDataMeta`
      - :class:`objetto.objects.DictObjectMeta`

    Features:
      - Defines a key relationship type.
      - Enforces correct type for :attr:`objetto.bases.BaseDictStructure.\
_key_relationship`.
    """

    def __init__(cls, name, bases, dct):
        super(BaseDictStructureMeta, cls).__init__(name, bases, dct)

        # Check key relationship type.
        cls_ = cast("Type[BaseDictStructure]", cls)
        assert_is_instance(
            cls_._key_relationship,
            cls._key_relationship_type,
            subtypes=False,
        )

    @property
    @final
    def _key_relationship_type(cls):
        # type: () -> Type[KeyRelationship]
        """
        Relationship type.

        :rtype: type[objetto.objects.KeyRelationship or objetto.data.KeyRelationship]
        """
        return KeyRelationship


class BaseDictStructure(
    with_metaclass(
        BaseDictStructureMeta,
        BaseAuxiliaryStructure[KT],
        BaseProtectedDict[KT, VT],
    )
):
    """
    Base dictionary structure.

    Metaclass:
      - :class:`objetto.bases.BaseDictStructureMeta`

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructure`
      - :class:`objetto.bases.BaseProtectedDict`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveDictStructure`
      - :class:`objetto.bases.BaseMutableDictStructure`
      - :class:`objetto.data.DictData`
      - :class:`objetto.objects.DictObject`
    """

    __slots__ = ()

    _key_relationship = KeyRelationship()
    """
    **Class Attribute**

    Relationship for the keys.

    :type: objetto.objects.KeyRelationship or objetto.data.KeyRelationship
    """

    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        :rtype: str
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
        :rtype: collections.abc.Iterator[collections.abc.Hashable]
        """
        return reversed(self._state)

    @final
    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :type key: collections.abc.Hashable

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
        :rtype: int
        """
        return len(self._state)

    @final
    def __iter__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Key iterator.
        :rtype: collections.abc.Iterator[collections.abc.Hashable]
        """
        for key in self._state:
            yield key

    @final
    def __contains__(self, key):
        # type: (Any) -> bool
        """
        Get whether key is present.

        :param key: Key.
        :type key: collections.abc.Hashable

        :return: True if contains.
        :rtype: bool
        """
        return key in self._state

    @final
    def get(self, key, fallback=None):
        # type: (KT, Any) -> Union[VT, Any]
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :type key: collections.abc.Hashable

        :param fallback: Fallback value.

        :return: Value or fallback value.
        """
        return self._state.get(key, fallback)

    @final
    def iteritems(self):
        # type: () -> Iterator[Tuple[KT, VT]]
        """
        Iterate over items.

        :return: Items iterator.
        :rtype: collections.abc.Iterator[tuple[collections.abc.Hashable, Any]]
        """
        for key, value in iteritems(self._state):
            yield key, value

    @final
    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        :rtype: collections.abc.Iterator[collections.abc.Hashable]
        """
        for key in iterkeys(self._state):
            yield key

    @final
    def itervalues(self):
        # type: () -> Iterator[VT]
        """
        Iterate over values.

        :return: Values iterator.
        :rtype: collections.abc.Iterator
        """
        for value in itervalues(self._state):
            yield value

    @property
    @abstractmethod
    def _state(self):
        # type: () -> DictState[KT, VT]
        """
        Internal state.

        :rtype: objetto.states.DictState

        :raises NotImplementedError: Abstract method not implemented.
        """
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseInteractiveDictStructure(
    BaseDictStructure[KT, VT],
    BaseInteractiveAuxiliaryStructure[KT],
    BaseInteractiveDict[KT, VT],
):
    """
    Base interactive dictionary structure.

    Inherits from:
      - :class:`objetto.bases.BaseDictStructure`
      - :class:`objetto.bases.BaseInteractiveAuxiliaryStructure`
      - :class:`objetto.bases.BaseInteractiveDict`

    Inherited By:
      - :class:`objetto.data.InteractiveDictData`
    """

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableDictStructure(
    BaseMutableDict[KT, VT],
    BaseDictStructure[KT, VT],
    BaseMutableAuxiliaryStructure[KT],
):
    """
    Base mutable dictionary structure.

    Inherits from:
      - :class:`objetto.bases.BaseMutableDict`
      - :class:`objetto.bases.BaseDictStructure`
      - :class:`objetto.bases.BaseMutableAuxiliaryStructure`

    Inherited By:
      - :class:`objetto.objects.MutableDictObject`
    """

    __slots__ = ()
