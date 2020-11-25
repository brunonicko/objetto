# -*- coding: utf-8 -*-
"""Objects."""

from typing import TYPE_CHECKING, TypeVar, Callable

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from decorator import decorator
from six import string_types

from ._bases import MISSING
from ._objects import (
    DATA_METHOD_TAG,
    Attribute,
    Relationship,
    BaseReaction,
    Object,
    MutableDictObject,
    MutableListObject,
    MutableSetObject,
)
from ._structures import KeyRelationship, make_auxiliary_cls
from ._data import DataRelationship
from .reactions import reaction
from .utils.caller_module import get_caller_module
from .utils.reraise_context import ReraiseContext
from .utils.type_checking import assert_is_instance
from .utils.factoring import import_factory

if TYPE_CHECKING:
    from typing import (
        Any, Dict, Iterable, Mapping, Optional, Tuple, Type, Union
    )

    from .utils.factoring import LazyFactory
    from .utils.type_checking import LazyTypes

    ReactionType = Union[LazyFactory, BaseReaction]
    ReactionsType = Union[ReactionType, Iterable[ReactionType]]


__all__ = [
    "Object",
    "data_method",
    "data_relationship",
    "attribute",
    "dict_attribute",
    "dict_cls",
]


F = TypeVar("F", bound=Callable)  # Callable type.
T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Any key type.
VT = TypeVar("VT")  # Any value type.


def data_method(func):
    # type: (F) -> F
    """
    Decorate object methods by tagging them as data methods.
    The generated data class will have the decorated methods in them.

    .. code:: python

        >>> from objetto.applications import Application
        >>> from objetto.objects import Object, attribute, data_method

        >>> class MyObject(Object):
        ...     value = attribute(int, default=0)
        ...
        ...     @data_method
        ...     def get_double(self):
        ...         return self.value * 2
        ...
        >>> app = Application()
        >>> my_obj = MyObject(app)
        >>> my_obj.value = 42
        >>> my_obj.get_double()
        84
        >>> my_obj.data.get_double()
        84

    :param func: The method function.
    :return: Decorated method function.
    """

    @decorator
    def data_method_(func_, *args, **kwargs):
        return func_(*args, **kwargs)

    decorated = data_method_(func)
    setattr(decorated, DATA_METHOD_TAG, True)
    return decorated


def data_relationship(
    types=(),  # type: LazyTypes
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
):
    # type: (...) -> DataRelationship
    """
    Make custom relationship between a data structure and its values.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Value factory.
    :param serialized: Whether should be serialized.
    :param serializer: Custom serializer.
    :param deserializer: Custom deserializer.
    :param represented: Whether should be represented.
    :param compared: Whether the value should be leverage when comparing.
    :return: Custom data relationship.
    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """
    return DataRelationship(
        types=types,
        subtypes=subtypes,
        checked=checked,
        module=module,
        factory=factory,
        serialized=serialized,
        serializer=serializer,
        deserializer=deserializer,
        represented=represented,
        compared=compared,
    )


def attribute(
    types=(),  # type: Union[Type[T], str, Iterable[Union[Type[T], str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=None,  # type: Optional[bool]
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    child=True,  # type: bool
    history=None,  # type: Optional[bool]
    data=None,  # type: Optional[bool]
    custom_data_relationship=None,  # type: Optional[DataRelationship]
    default=MISSING,  # type: Any
    default_factory=None,  # type: LazyFactory
    required=True,  # type: bool
    changeable=None,  # type: Optional[bool]
    deletable=None,  # type: Optional[bool]
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    delegated=False,  # type: bool
    dependencies=None,  # type: Optional[Iterable[Attribute]]
    deserialize_to=None,  # type: Optional[Attribute]
):
    # type: (...) -> Attribute[T]
    """
    Make attribute.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Value factory.
    :param serialized: Whether should be serialized.
    :param serializer: Custom serializer.
    :param deserializer: Custom deserializer.
    :param represented: Whether should be represented.
    :param child: Whether object values should be adopted as children.
    :param history: Whether to propagate the history to the child object value.
    :param data: Whether to generate data for the value.
    :param custom_data_relationship: Custom data relationship.
    :param default: Default value.
    :param default_factory: Default value factory.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :param delegated: Whether attribute allows for delegates to be defined.
    :param dependencies: Attributes needed by the getter delegate.
    :param deserialize_to: Non-serialized attribute to deserialize this into.
    :return: Attribute.
    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'attribute'"):
        if custom_data_relationship is not None:
            assert_is_instance(
                custom_data_relationship, DataRelationship, subtypes=False
            )
        relationship = Relationship(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            child=child,
            history=history,
            data=data,
            data_relationship=custom_data_relationship,
        )

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'attribute'"):
        attribute_ = Attribute(
            relationship=relationship,
            default=default,
            default_factory=default_factory,
            module=module,
            required=required,
            changeable=changeable,
            deletable=deletable,
            finalized=finalized,
            abstracted=abstracted,
            delegated=delegated,
            dependencies=dependencies,
            deserialize_to=deserialize_to,
        )  # type: Attribute[T]

    return attribute_


def dict_attribute(
    types=(),  # type: Union[Type[VT], str, Iterable[Union[Type[VT], str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=None,  # type: Optional[bool]
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], str, Iterable[Union[Type[KT], str]]]
    key_subtypes=False,  # type: bool
    key_factory=None,  # type: LazyFactory
    child=True,  # type: bool
    history=None,  # type: Optional[bool]
    data=None,  # type: Optional[bool]
    custom_data_relationship=None,  # type: Optional[DataRelationship]
    default=MISSING,  # type: Any
    default_factory=None,  # type: LazyFactory
    required=False,  # type: bool
    changeable=True,  # type: bool
    deletable=False,  # type: bool
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
):
    # type: (...) -> Attribute[MutableDictObject[KT, VT]]
    """
    Make dictionary attribute.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Value factory.
    :param serialized: Whether should be serialized.
    :param serializer: Custom serializer.
    :param deserializer: Custom deserializer.
    :param represented: Whether should be represented.
    :param child: Whether object values should be adopted as children.
    :param history: Whether to propagate the history to the child object value.
    :param data: Whether to generate data for the value.
    :param custom_data_relationship: Custom data relationship.
    :param key_types: Key types.
    :param key_subtypes: Whether to accept subtypes for the keys.
    :param key_factory: Key factory.
    :param default: Default value.
    :param default_factory: Default value factory.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :param reactions: Reaction functions ordered by priority.
    :return: Dictionary attribute.
    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make dictionary class.
    with ReraiseContext((TypeError, ValueError), "defining 'dict_attribute'"):
        dict_type = dict_cls(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            key_types=key_types,
            key_subtypes=key_subtypes,
            key_factory=key_factory,
            child=child,
            history=history,
            data=data,
            custom_data_relationship=custom_data_relationship,
            qual_name=qual_name,
            unique=unique,
            reactions=reactions,
        )  # type: Type[MutableDictObject[KT, VT]]

    # Factory for dict object relationship.
    def dict_factory(initial=(), app=None):
        """Factory for the whole dict object."""
        if type(initial) is dict_type and initial.app is app:
            return initial
        else:
            return dict_type(app, initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = {}

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'attribute'"):
        relationship = Relationship(
            types=dict_type,
            subtypes=False,
            checked=False,
            module=module,
            factory=dict_factory,
            serialized=serialized,
            serializer=None,
            deserializer=None,
            represented=represented,
            child=child,
            history=history,
            data=data,
            data_relationship=None,
        )

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'attribute'"):
        attribute_ = Attribute(
            relationship=relationship,
            default=default,
            default_factory=default_factory,
            module=module,
            required=required,
            changeable=changeable,
            deletable=deletable,
            finalized=finalized,
            abstracted=abstracted,
            delegated=False,
            dependencies=None,
            deserialize_to=None,
        )  # type: Attribute[MutableDictObject[KT, VT]]

    return attribute_


def _prepare_reactions(reactions=None):
    # type: (ReactionsType) -> Dict[str, BaseReaction]
    """
    Conform reactions parameter value into a dictionary with reaction methods.

    :param reactions: Input reactions.
    :return: Dictionary with reaction methods.
    """
    dct = {}
    if reactions is None:
        return dct
    if (
        isinstance(reactions, string_types) or
        not isinstance(reactions, collections_abc.Iterable)
    ):
        reactions = (reactions,)
    for i, reaction_ in enumerate(reactions):
        if isinstance(reaction_, BaseReaction) and reaction_.priority != i:
            reaction_ = reaction_.set_priority(i)
        elif reaction_ is None:
            continue
        else:
            # noinspection PyArgumentList
            reaction_ = reaction(priority=i)(import_factory(reaction_))
        dct["__reaction{}".format(i)] = reaction_
    return dct


def dict_cls(
    types=(),  # type: Union[Type[VT], str, Iterable[Union[Type[VT], str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=None,  # type: Optional[bool]
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], str, Iterable[Union[Type[KT], str]]]
    key_subtypes=False,  # type: bool
    key_factory=None,  # type: LazyFactory
    child=True,  # type: bool
    history=None,  # type: Optional[bool]
    data=None,  # type: Optional[bool]
    custom_data_relationship=None,  # type: Optional[DataRelationship]
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
):
    # type: (...) -> Type[MutableDictObject[KT, VT]]
    """
    Make auxiliary dictionary object class.

    :param types: Types.
    :param subtypes: Whether to accept subtypes.
    :param checked: Whether to perform runtime type check.
    :param module: Module path for lazy types/factories.
    :param factory: Value factory.
    :param serialized: Whether should be serialized.
    :param serializer: Custom serializer.
    :param deserializer: Custom deserializer.
    :param represented: Whether should be represented.
    :param key_types: Key types.
    :param key_subtypes: Whether to accept subtypes for the keys.
    :param key_factory: Key factory.
    :param child: Whether object values should be adopted as children.
    :param history: Whether to propagate the history to the child object value.
    :param data: Whether to generate data for the value.
    :param custom_data_relationship: Custom data relationship.
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :param reactions: Reaction functions ordered by priority.
    :return: Dictionary object class.
    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'dict_cls'"):
        relationship = Relationship(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            child=child,
            history=history,
            data=data,
            data_relationship=custom_data_relationship,
        )

    # Key relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'dict_cls'"):
        key_relationship = KeyRelationship(
            types=key_types,
            subtypes=key_subtypes,
            checked=checked,
            module=module,
            factory=key_factory,
        )
        dct = {"_key_relationship": key_relationship}

    # Reactions.
    with ReraiseContext((TypeError, ValueError), "defining 'dict_cls'"):
        dct.update(_prepare_reactions(reactions))

    # Make class.
    base = MutableDictObject  # type: Type[MutableDictObject[KT, VT]]
    with ReraiseContext(TypeError, "defining 'dict_cls'"):
        cls = make_auxiliary_cls(
            base,
            relationship,
            qual_name=qual_name,
            module=module,
            unique_descriptor_name="unique_hash" if unique else None,
            dct=dct,
        )

    return cls
