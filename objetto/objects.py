# -*- coding: utf-8 -*-
"""Objects."""

from typing import TYPE_CHECKING, Callable, TypeVar, cast

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from decorator import decorator
from six import string_types

from ._applications import Action
from ._bases import MISSING
from ._data import DataRelationship
from ._objects import (
    DATA_METHOD_TAG,
    Attribute,
    AttributeMeta,
    BaseReaction,
    DictObject,
    DictObjectMeta,
    HistoryDescriptor,
    ListObject,
    ListObjectMeta,
    MutableDictObject,
    MutableListObject,
    MutableSetObject,
    Object,
    ObjectMeta,
    ProxyDictObject,
    ProxyListObject,
    ProxySetObject,
    Relationship,
    SetObject,
    SetObjectMeta,
)
from ._reactions import reaction
from ._structures import (
    KeyRelationship,
    UniqueDescriptor,
    make_auxiliary_cls,
    unique_descriptor,
)
from .utils.caller_module import get_caller_module
from .utils.factoring import import_factory
from .utils.reraise_context import ReraiseContext
from .utils.type_checking import assert_is_instance

if TYPE_CHECKING:
    from typing import Any, Dict, Iterable, Optional, Tuple, Type, Union

    from .utils.factoring import LazyFactory
    from .utils.type_checking import LazyTypes

    ReactionType = Union[LazyFactory, BaseReaction]
    ReactionsType = Union[ReactionType, Iterable[ReactionType]]

__all__ = [
    "ObjectMeta",
    "Object",
    "DictObjectMeta",
    "DictObject",
    "MutableDictObject",
    "ListObjectMeta",
    "ListObject",
    "MutableListObject",
    "SetObjectMeta",
    "SetObject",
    "MutableSetObject",
    "ProxyDictObject",
    "ProxyListObject",
    "ProxySetObject",
    "Relationship",
    "AttributeMeta",
    "Attribute",
    "KeyRelationship",
    "UniqueDescriptor",
    "Action",
    "data_method",
    "data_relationship",
    "unique_descriptor",
    "history_descriptor",
    "attribute",
    "constant_attribute",
    "protected_attribute_pair",
    "dict_attribute",
    "protected_dict_attribute",
    "protected_dict_attribute_pair",
    "list_attribute",
    "protected_list_attribute",
    "protected_list_attribute_pair",
    "set_attribute",
    "protected_set_attribute",
    "protected_set_attribute_pair",
    "protected_dict_cls",
    "dict_cls",
    "protected_list_cls",
    "list_cls",
    "protected_set_cls",
    "set_cls",
]


T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Any key type.
VT = TypeVar("VT")  # Any value type.


if TYPE_CHECKING:
    NT = Union[Type[None], None]
    MutableDictAttribute = Attribute[MutableDictObject[KT, VT]]
    MutableListAttribute = Attribute[MutableListObject[T]]
    MutableSetAttribute = Attribute[MutableSetObject[T]]
    DictAttribute = Attribute[DictObject[KT, VT]]
    ListAttribute = Attribute[ListObject[T]]
    SetAttribute = Attribute[SetObject[T]]
    ProxyDictAttribute = Attribute[ProxyDictObject[KT, VT]]
    ProxyListAttribute = Attribute[ProxyListObject[T]]
    ProxySetAttribute = Attribute[ProxySetObject[T]]


# noinspection PyAbstractClass
def data_method(func):
    # type: (Callable) -> Callable
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
    :type func: function

    :return: Decorated method function.
    :rtype: function
    """

    @decorator
    def data_method_(func_, *args, **kwargs):
        """Data method decorator."""
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
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool or None

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

    :return: Custom data relationship.
    :rtype: objetto.data.DataRelationship

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


# noinspection PyAbstractClass
def history_descriptor(size=None):
    # type: (Optional[int]) -> HistoryDescriptor
    """
    Descriptor to be used when declaring an :class:`objetto.objects.Object` class.

    When used, every instance of the object class will hold a history that will keep
    track of its changes (and the changes of its children that define a history
    relationship), allowing for easy undo/redo operations.
    If accessed through an instance, the descriptor will return the history object.

    .. code:: python

        >>> from objetto import Application, Object, attribute, history_descriptor

        >>> class Person(Object):
        ...     history = history_descriptor()
        ...     name = attribute(str)
        ...
        >>> app = Application()
        >>> person = Person(app, name="Albert")
        >>> person.name = "Einstein"
        >>> person.history.undo()
        >>> person.name
        'Albert'

    :param size: How many changes to remember.
    :type size: int or None

    :return: History descriptor.
    :rtype: objetto.history.HistoryDescriptor
    """
    return HistoryDescriptor(size=size)


def attribute(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    metadata=None,  # type: Any
    delegated=False,  # type: bool
    dependencies=None,  # type: Optional[Union[Iterable[Attribute], Attribute]]
    deserialize_to=None,  # type: Optional[Attribute]
    batch_name=None,  # type: Optional[str]
):
    # type: (...) -> Attribute[T]
    """
    Make attribute.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param required: Whether attribute is required to have a value or not.
    :type required: bool

    :param changeable: Whether attribute value can be changed.
    :type changeable: bool

    :param deletable: Whether attribute value can be deleted.
    :type deletable: bool

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param delegated: Whether attribute allows for delegates to be defined.
    :type delegated: bool

    :param dependencies: Attributes needed by the getter delegate.
    :type dependencies: collections.abc.Iterable[objetto.objects.Attribute] or \
objetto.objects.Attribute or None

    :param deserialize_to: Non-serialized attribute to deserialize this into.
    :type deserialize_to: objetto.objects.Attribute or None

    :param batch_name: Batch name.
    :type batch_name: str or None

    :return: Attribute.
    :rtype: objetto.objects.Attribute

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    :raises ValueError: Can't declare same dependency more than once.
    :raises ValueError: Provided 'changeable' but 'delegated' is True.
    :raises ValueError: Provided 'deletable' but 'delegated' is True.
    :raises ValueError: Provided 'dependencies' but 'delegated' is False.
    :raises ValueError: Provided 'deserialize_to' but 'serialized' is False.
    :raises ValueError: Can't provide a serialized attribute to 'deserialize_to'.
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
            metadata=metadata,
            delegated=delegated,
            dependencies=dependencies,
            deserialize_to=deserialize_to,
            batch_name=batch_name,
        )  # type: Attribute[T]

    return attribute_


def constant_attribute(
    value,  # type: T
    serialized=False,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=False,  # type: bool
    data=True,  # type: bool
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
):
    # type: (...) -> Attribute[T]
    """
    Make constant attribute.

    :param value: Constant value.

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :return: Constant attribute.
    :rtype: objetto.objects.Attribute

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'constant_attribute'"):
        relationship = Relationship(
            types=type(value),
            subtypes=False,
            checked=False,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            child=True,
            history=False,
            data=data,
            data_relationship=None,
        )

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'constant_attribute'"):
        attribute_ = Attribute(
            relationship=relationship,
            default=value,
            default_factory=None,
            required=False,
            changeable=False,
            deletable=False,
            finalized=finalized,
            abstracted=abstracted,
            metadata=metadata,
        )  # type: Attribute[T]

    return attribute_


def protected_attribute_pair(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    changeable=None,  # type: Optional[bool]
    deletable=None,  # type: Optional[bool]
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
    protected_metadata=None,  # type: Any
    batch_name=None,  # type: Optional[str]
):
    # type: (...) -> Tuple[Attribute[T], Attribute[T]]
    """
    Make protected-public attribute pair.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param changeable: Whether attribute value can be changed.
    :type changeable: bool

    :param deletable: Whether attribute value can be deleted.
    :type deletable: bool

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param protected_metadata: Protected metadata.

    :param batch_name: Batch name.
    :type batch_name: str or None

    :return: Protected-public attribute pair.
    :rtype: tuple[objetto.objects.Attribute, objetto.objects.Attribute]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make protected attribute.
    protected_attribute = attribute(
        types=types,
        subtypes=subtypes,
        checked=checked,
        module=module,
        factory=factory,
        represented=False,
        child=False,
        default=default,
        default_factory=default_factory,
        required=False,
        changeable=changeable,
        deletable=deletable,
        finalized=finalized,
        abstracted=abstracted,
        metadata=protected_metadata,
        delegated=False,
        batch_name=batch_name,
    )

    # Make public attribute.
    public_attribute = attribute(
        types=types,
        subtypes=subtypes,
        checked=False,
        module=module,
        serialized=serialized,
        serializer=serializer,
        deserializer=deserializer,
        represented=represented,
        child=child,
        history=history,
        data=data,
        custom_data_relationship=custom_data_relationship,
        required=False,
        finalized=finalized,
        abstracted=abstracted,
        metadata=metadata,
        delegated=True,
        dependencies=(protected_attribute,),
        deserialize_to=protected_attribute if serialized else None,
    )

    def getter(iobj):
        """Getter delegate."""
        protected_name = iobj.__.cls._attribute_names[protected_attribute]
        return iobj[protected_name]

    public_attribute.getter(getter)

    return protected_attribute, public_attribute


def dict_attribute(
    types=(),  # type: Union[Type[VT], NT, str, Iterable[Union[Type[VT], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=None,  # type: Optional[bool]
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], NT, str, Iterable[Union[Type[KT], NT, str]]]
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
    metadata=None,  # type: Any
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_update_name=None,  # type: Optional[str]
):
    # type: (...) -> MutableDictAttribute[KT, VT]
    """
    Make mutable dictionary attribute.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param key_types: Key types.
    :type key_types: str or type or None or tuple[str or type or None]

    :param key_subtypes: Whether to accept subtypes for the keys.
    :type key_subtypes: bool

    :param key_factory: Key factory.
    :type key_factory: str or collections.abc.Callable or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param required: Whether attribute is required to have a value or not.
    :type required: bool

    :param changeable: Whether attribute value can be changed.
    :type changeable: bool

    :param deletable: Whether attribute value can be deleted.
    :type deletable: bool

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :return: Mutable dictionary attribute.
    :rtype: objetto.objects.Attribute[objetto.objects.MutableDictObject]

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
            batch_update_name=batch_update_name,
        )  # type: Type[MutableDictObject[KT, VT]]

    # Factory for dict object relationship.
    def dict_factory(initial=(), app=None, **_):
        """Factory for the whole dict object."""
        if type(initial) is dict_type and initial.app is app:
            return initial
        else:
            return dict_type(app, initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = ()

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'dict_attribute'"):
        relationship = Relationship(
            types=dict_type,
            subtypes=False,
            checked=False,
            module=module,
            factory=dict_factory,
            serialized=serialized if child else False,
            serializer=None,
            deserializer=None,
            represented=represented,
            child=True,
            history=history if child else False,
            data=data if child else False,
            data_relationship=None,
        )

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'dict_attribute'"):
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
            metadata=metadata,
            delegated=False,
            dependencies=None,
            deserialize_to=None,
        )  # type: Attribute[MutableDictObject[KT, VT]]

    return attribute_


def protected_dict_attribute(
    types=(),  # type: Union[Type[VT], NT, str, Iterable[Union[Type[VT], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=None,  # type: Optional[bool]
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], NT, str, Iterable[Union[Type[KT], NT, str]]]
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
    metadata=None,  # type: Any
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_update_name=None,  # type: Optional[str]
):
    # type: (...) -> DictAttribute[KT, VT]
    """
    Make protected dictionary attribute.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param key_types: Key types.
    :type key_types: str or type or None or tuple[str or type or None]

    :param key_subtypes: Whether to accept subtypes for the keys.
    :type key_subtypes: bool

    :param key_factory: Key factory.
    :type key_factory: str or collections.abc.Callable or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param required: Whether attribute is required to have a value or not.
    :type required: bool

    :param changeable: Whether attribute value can be changed.
    :type changeable: bool

    :param deletable: Whether attribute value can be deleted.
    :type deletable: bool

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :return: Protected dictionary attribute.
    :rtype: objetto.objects.Attribute[objetto.objects.DictObject]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make dictionary class.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_dict_attribute'"):
        dict_type = protected_dict_cls(
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
            batch_update_name=batch_update_name,
        )  # type: Type[DictObject[KT, VT]]

    # Factory for dict object relationship.
    def dict_factory(initial=(), app=None, **_):
        """Factory for the whole dict object."""
        if type(initial) is dict_type and initial.app is app:
            return initial
        else:
            return dict_type(app, initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = ()

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_dict_attribute'"):
        relationship = Relationship(
            types=dict_type,
            subtypes=False,
            checked=False,
            module=module,
            factory=dict_factory,
            serialized=serialized if child else False,
            serializer=None,
            deserializer=None,
            represented=represented,
            child=True,
            history=history if child else False,
            data=data if child else False,
            data_relationship=None,
        )

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_dict_attribute'"):
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
            metadata=metadata,
            delegated=False,
            dependencies=None,
            deserialize_to=None,
        )  # type: Attribute[DictObject[KT, VT]]

    return attribute_


def protected_dict_attribute_pair(
    types=(),  # type: Union[Type[VT], NT, str, Iterable[Union[Type[VT], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=None,  # type: Optional[bool]
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], NT, str, Iterable[Union[Type[KT], NT, str]]]
    key_subtypes=False,  # type: bool
    key_factory=None,  # type: LazyFactory
    child=True,  # type: bool
    history=None,  # type: Optional[bool]
    data=None,  # type: Optional[bool]
    custom_data_relationship=None,  # type: Optional[DataRelationship]
    default=MISSING,  # type: Any
    default_factory=None,  # type: LazyFactory
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
    protected_metadata=None,  # type: Any
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_update_name=None,  # type: Optional[str]
):
    # type: (...) -> Tuple[ProxyDictAttribute[KT, VT], DictAttribute[KT, VT]]
    """
    Make protected-public dictionary attribute pair.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param key_types: Key types.
    :type key_types: str or type or None or tuple[str or type or None]

    :param key_subtypes: Whether to accept subtypes for the keys.
    :type key_subtypes: bool

    :param key_factory: Key factory.
    :type key_factory: str or collections.abc.Callable or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param protected_metadata: Protected metadata.

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :return: Protected-public dictionary attribute pair.
    :rtype: tuple[objetto.objects.Attribute[objetto.objects.ProxyDictObject], \
objetto.objects.Attribute[objetto.objects.DictObject]]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make public dictionary attribute.
    if default is MISSING and default_factory is None:
        default = ()

    public_attribute = protected_dict_attribute(
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
        default=default,
        default_factory=default_factory,
        required=False,
        changeable=False,
        deletable=False,
        finalized=finalized,
        abstracted=abstracted,
        metadata=protected_metadata,
        qual_name=qual_name,
        unique=unique,
        reactions=reactions,
        batch_update_name=batch_update_name,
    )  # type: DictAttribute[KT, VT]

    # Make protected attribute.
    protected_attribute = cast(
        "ProxyDictAttribute[KT, VT]",
        attribute(
            types=ProxyDictObject,
            subtypes=False,
            checked=False,
            module=module,
            represented=False,
            child=False,
            required=False,
            finalized=finalized,
            abstracted=abstracted,
            metadata=metadata,
            delegated=True,
            dependencies=(public_attribute,),
        ),
    )

    def getter(iobj):
        """Getter delegate."""
        public_name = iobj.__.cls._attribute_names[public_attribute]
        return ProxyDictObject(iobj[public_name])

    protected_attribute.getter(getter)

    return protected_attribute, public_attribute


def list_attribute(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    required=False,  # type: bool
    changeable=True,  # type: bool
    deletable=False,  # type: bool
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_insert_name=None,  # type: Optional[str]
    batch_delete_name=None,  # type: Optional[str]
    batch_update_name=None,  # type: Optional[str]
    batch_move_name=None,  # type: Optional[str]
):
    # type: (...) -> MutableListAttribute[T]
    """
    Make mutable list attribute.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param required: Whether attribute is required to have a value or not.
    :type required: bool

    :param changeable: Whether attribute value can be changed.
    :type changeable: bool

    :param deletable: Whether attribute value can be deleted.
    :type deletable: bool

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_insert_name: Batch name for insert operations.
    :type batch_insert_name: str or None

    :param batch_delete_name: Batch name for delete operations.
    :type batch_delete_name: str or None

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :param batch_move_name: Batch name for move operations.
    :type batch_move_name: str or None

    :return: Mutable list attribute.
    :rtype: objetto.objects.Attribute[objetto.objects.MutableListObject]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make list class.
    with ReraiseContext((TypeError, ValueError), "defining 'list_attribute'"):
        list_type = list_cls(
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
            custom_data_relationship=custom_data_relationship,
            qual_name=qual_name,
            unique=unique,
            reactions=reactions,
            batch_insert_name=batch_insert_name,
            batch_delete_name=batch_delete_name,
            batch_update_name=batch_update_name,
            batch_move_name=batch_move_name,
        )  # type: Type[MutableListObject[T]]

    # Factory for list object relationship.
    def list_factory(initial=(), app=None, **_):
        """Factory for the whole list object."""
        if type(initial) is list_type and initial.app is app:
            return initial
        else:
            return list_type(app, initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = ()

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'list_attribute'"):
        relationship = Relationship(
            types=list_type,
            subtypes=False,
            checked=False,
            module=module,
            factory=list_factory,
            serialized=serialized if child else False,
            serializer=None,
            deserializer=None,
            represented=represented,
            child=True,
            history=history if child else False,
            data=data if child else False,
            data_relationship=None,
        )

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'list_attribute'"):
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
            metadata=metadata,
            delegated=False,
            dependencies=None,
            deserialize_to=None,
        )  # type: Attribute[MutableListObject[T]]

    return attribute_


def protected_list_attribute(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    required=False,  # type: bool
    changeable=True,  # type: bool
    deletable=False,  # type: bool
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_insert_name=None,  # type: Optional[str]
    batch_delete_name=None,  # type: Optional[str]
    batch_update_name=None,  # type: Optional[str]
    batch_move_name=None,  # type: Optional[str]
):
    # type: (...) -> ListAttribute[T]
    """
    Make protected list attribute.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param required: Whether attribute is required to have a value or not.
    :type required: bool

    :param changeable: Whether attribute value can be changed.
    :type changeable: bool

    :param deletable: Whether attribute value can be deleted.
    :type deletable: bool

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_insert_name: Batch name for insert operations.
    :type batch_insert_name: str or None

    :param batch_delete_name: Batch name for delete operations.
    :type batch_delete_name: str or None

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :param batch_move_name: Batch name for move operations.
    :type batch_move_name: str or None

    :return: Protected list attribute.
    :rtype: objetto.objects.Attribute[objetto.objects.ListObject]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make list class.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_list_attribute'"):
        list_type = protected_list_cls(
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
            custom_data_relationship=custom_data_relationship,
            qual_name=qual_name,
            unique=unique,
            reactions=reactions,
            batch_insert_name=batch_insert_name,
            batch_delete_name=batch_delete_name,
            batch_update_name=batch_update_name,
            batch_move_name=batch_move_name,
        )  # type: Type[ListObject[T]]

    # Factory for list object relationship.
    def list_factory(initial=(), app=None, **_):
        """Factory for the whole list object."""
        if type(initial) is list_type and initial.app is app:
            return initial
        else:
            return list_type(app, initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = ()

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_list_attribute'"):
        relationship = Relationship(
            types=list_type,
            subtypes=False,
            checked=False,
            module=module,
            factory=list_factory,
            serialized=serialized if child else False,
            serializer=None,
            deserializer=None,
            represented=represented,
            child=True,
            history=history if child else False,
            data=data if child else False,
            data_relationship=None,
        )

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_list_attribute'"):
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
            metadata=metadata,
            delegated=False,
            dependencies=None,
            deserialize_to=None,
        )  # type: Attribute[ListObject[T]]

    return attribute_


def protected_list_attribute_pair(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
    protected_metadata=None,  # type: Any
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_insert_name=None,  # type: Optional[str]
    batch_delete_name=None,  # type: Optional[str]
    batch_update_name=None,  # type: Optional[str]
    batch_move_name=None,  # type: Optional[str]
):
    # type: (...) -> Tuple[ProxyListAttribute[T], ListAttribute[T]]
    """
    Make protected-public list attribute pair.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param protected_metadata: Protected metadata.

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_insert_name: Batch name for insert operations.
    :type batch_insert_name: str or None

    :param batch_delete_name: Batch name for delete operations.
    :type batch_delete_name: str or None

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :param batch_move_name: Batch name for move operations.
    :type batch_move_name: str or None

    :return: Protected-public list attribute pair.
    :rtype: tuple[objetto.objects.Attribute[objetto.objects.ProxyListObject], \
objetto.objects.Attribute[objetto.objects.ListObject]]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make public list attribute.
    if default is MISSING and default_factory is None:
        default = ()

    public_attribute = protected_list_attribute(
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
        custom_data_relationship=custom_data_relationship,
        default=default,
        default_factory=default_factory,
        required=False,
        changeable=False,
        deletable=False,
        finalized=finalized,
        abstracted=abstracted,
        metadata=protected_metadata,
        qual_name=qual_name,
        unique=unique,
        reactions=reactions,
        batch_insert_name=batch_insert_name,
        batch_delete_name=batch_delete_name,
        batch_update_name=batch_update_name,
        batch_move_name=batch_move_name,
    )  # type: ListAttribute[T]

    # Make protected attribute.
    protected_attribute = cast(
        "ProxyListAttribute[T]",
        attribute(
            types=ProxyListObject,
            subtypes=False,
            checked=False,
            module=module,
            represented=False,
            child=False,
            required=False,
            finalized=finalized,
            abstracted=abstracted,
            metadata=metadata,
            delegated=True,
            dependencies=(public_attribute,),
        ),
    )

    def getter(iobj):
        """Getter delegate."""
        public_name = iobj.__.cls._attribute_names[public_attribute]
        return ProxyListObject(iobj[public_name])

    protected_attribute.getter(getter)

    return protected_attribute, public_attribute


def set_attribute(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    required=False,  # type: bool
    changeable=True,  # type: bool
    deletable=False,  # type: bool
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_update_name=None,  # type: Optional[str]
    batch_remove_name=None,  # type: Optional[str]
):
    # type: (...) -> MutableSetAttribute[T]
    """
    Make mutable set attribute.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param required: Whether attribute is required to have a value or not.
    :type required: bool

    :param changeable: Whether attribute value can be changed.
    :type changeable: bool

    :param deletable: Whether attribute value can be deleted.
    :type deletable: bool

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :param batch_remove_name: Batch name for remove operations.
    :type batch_remove_name: str or None

    :return: Mutable set attribute.
    :rtype: objetto.objects.Attribute[objetto.objects.MutableSetObject]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make set class.
    with ReraiseContext((TypeError, ValueError), "defining 'set_attribute'"):
        set_type = set_cls(
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
            custom_data_relationship=custom_data_relationship,
            qual_name=qual_name,
            unique=unique,
            reactions=reactions,
            batch_update_name=batch_update_name,
            batch_remove_name=batch_remove_name,
        )  # type: Type[MutableSetObject[T]]

    # Factory for set object relationship.
    def set_factory(initial=(), app=None, **_):
        """Factory for the whole set object."""
        if type(initial) is set_type and initial.app is app:
            return initial
        else:
            return set_type(app, initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = ()

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'set_attribute'"):
        relationship = Relationship(
            types=set_type,
            subtypes=False,
            checked=False,
            module=module,
            factory=set_factory,
            serialized=serialized if child else False,
            serializer=None,
            deserializer=None,
            represented=represented,
            child=True,
            history=history if child else False,
            data=data if child else False,
            data_relationship=None,
        )

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'set_attribute'"):
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
            metadata=metadata,
            delegated=False,
            dependencies=None,
            deserialize_to=None,
        )  # type: Attribute[MutableSetObject[T]]

    return attribute_


def protected_set_attribute(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    required=False,  # type: bool
    changeable=True,  # type: bool
    deletable=False,  # type: bool
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_update_name=None,  # type: Optional[str]
    batch_remove_name=None,  # type: Optional[str]
):
    # type: (...) -> SetAttribute[T]
    """
    Make protected set attribute.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param required: Whether attribute is required to have a value or not.
    :type required: bool

    :param changeable: Whether attribute value can be changed.
    :type changeable: bool

    :param deletable: Whether attribute value can be deleted.
    :type deletable: bool

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :param batch_remove_name: Batch name for remove operations.
    :type batch_remove_name: str or None

    :return: Protected set attribute.
    :rtype: objetto.objects.Attribute[objetto.objects.SetObject]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make set class.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_set_attribute'"):
        set_type = protected_set_cls(
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
            custom_data_relationship=custom_data_relationship,
            qual_name=qual_name,
            unique=unique,
            reactions=reactions,
            batch_update_name=batch_update_name,
            batch_remove_name=batch_remove_name,
        )  # type: Type[SetObject[T]]

    # Factory for set object relationship.
    def set_factory(initial=(), app=None, **_):
        """Factory for the whole set object."""
        if type(initial) is set_type and initial.app is app:
            return initial
        else:
            return set_type(app, initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = ()

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_set_attribute'"):
        relationship = Relationship(
            types=set_type,
            subtypes=False,
            checked=False,
            module=module,
            factory=set_factory,
            serialized=serialized if child else False,
            serializer=None,
            deserializer=None,
            represented=represented,
            child=True,
            history=history if child else False,
            data=data if child else False,
            data_relationship=None,
        )

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_set_attribute'"):
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
            metadata=metadata,
            delegated=False,
            dependencies=None,
            deserialize_to=None,
        )  # type: Attribute[SetObject[T]]

    return attribute_


def protected_set_attribute_pair(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
    protected_metadata=None,  # type: Any
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_update_name=None,  # type: Optional[str]
    batch_remove_name=None,  # type: Optional[str]
):
    # type: (...) -> Tuple[ProxySetAttribute[T], SetAttribute[T]]
    """
    Make protected-public set attribute pair.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :param protected_metadata: Protected metadata.

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :param batch_remove_name: Batch name for remove operations.
    :type batch_remove_name: str or None

    :return: Protected-public set attribute pair.
    :rtype: tuple[objetto.objects.Attribute[objetto.objects.ProxySetObject], \
objetto.objects.Attribute[objetto.objects.SetObject]]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make public set attribute.
    if default is MISSING and default_factory is None:
        default = ()

    public_attribute = protected_set_attribute(
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
        custom_data_relationship=custom_data_relationship,
        default=default,
        default_factory=default_factory,
        required=False,
        changeable=False,
        deletable=False,
        finalized=finalized,
        abstracted=abstracted,
        metadata=protected_metadata,
        qual_name=qual_name,
        unique=unique,
        reactions=reactions,
        batch_update_name=batch_update_name,
        batch_remove_name=batch_remove_name,
    )  # type: SetAttribute[T]

    # Make protected attribute.
    protected_attribute = cast(
        "ProxySetAttribute[T]",
        attribute(
            types=ProxySetObject,
            subtypes=False,
            checked=False,
            module=module,
            represented=False,
            child=False,
            required=False,
            finalized=finalized,
            abstracted=abstracted,
            metadata=metadata,
            delegated=True,
            dependencies=(public_attribute,),
        ),
    )

    def getter(iobj):
        """Getter delegate."""
        public_name = iobj.__.cls._attribute_names[public_attribute]
        return ProxySetObject(iobj[public_name])

    protected_attribute.getter(getter)

    return protected_attribute, public_attribute


def _prepare_reactions(reactions=None):
    # type: (ReactionsType) -> Dict[str, BaseReaction]
    """
    Conform reactions parameter value into a dictionary with reaction methods.

    :param reactions: Input reactions.
    :return: Dictionary with reaction methods.
    """
    dct = {}  # type: Dict[str, BaseReaction]
    if reactions is None:
        return dct
    if isinstance(reactions, string_types) or not isinstance(
        reactions, collections_abc.Iterable
    ):
        reactions = (reactions,)
    for i, reaction_ in enumerate(reactions):
        if isinstance(reaction_, BaseReaction) and reaction_.priority != i:
            reaction_ = reaction_.set_priority(i)
        elif reaction_ is None:
            continue
        else:
            reaction_decorator = reaction(priority=i)  # type: ignore
            # noinspection PyArgumentList
            reaction_ = reaction_decorator(import_factory(reaction_))  # type: ignore
        dct["__reaction{}".format(i)] = cast("BaseReaction", reaction_)
    return dct


def dict_cls(
    types=(),  # type: Union[Type[VT], NT, str, Iterable[Union[Type[VT], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=None,  # type: Optional[bool]
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], NT, str, Iterable[Union[Type[KT], NT, str]]]
    key_subtypes=False,  # type: bool
    key_factory=None,  # type: LazyFactory
    child=True,  # type: bool
    history=None,  # type: Optional[bool]
    data=None,  # type: Optional[bool]
    custom_data_relationship=None,  # type: Optional[DataRelationship]
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_update_name=None,  # type: Optional[str]
):
    # type: (...) -> Type[MutableDictObject[KT, VT]]
    """
    Make auxiliary mutable dictionary object class.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param key_types: Key types.
    :type key_types: str or type or None or tuple[str or type or None]

    :param key_subtypes: Whether to accept subtypes for the keys.
    :type key_subtypes: bool

    :param key_factory: Key factory.
    :type key_factory: str or collections.abc.Callable or None

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :return: Mutable dictionary object class.
    :rtype: type[objetto.objects.MutableDictObject]

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

    # Prepare dct.
    dct = {}  # type: Dict[str, Any]

    # Key relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'dict_cls'"):
        key_relationship = KeyRelationship(
            types=key_types,
            subtypes=key_subtypes,
            checked=checked,
            module=module,
            factory=key_factory,
        )
        dct.update({"_key_relationship": key_relationship})

    # Reactions.
    with ReraiseContext((TypeError, ValueError), "defining 'dict_cls'"):
        dct.update(_prepare_reactions(reactions))

    # Batch names.
    if batch_update_name:
        dct["_BATCH_UPDATE_NAME"] = batch_update_name

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
        dct=dct,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'dict_cls'"):
        mutable_base = MutableDictObject  # type: Type[MutableDictObject[KT, VT]]
        return make_auxiliary_cls(mutable_base, **cls_kwargs)


def protected_dict_cls(
    types=(),  # type: Union[Type[VT], NT, str, Iterable[Union[Type[VT], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=None,  # type: Optional[bool]
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], NT, str, Iterable[Union[Type[KT], NT, str]]]
    key_subtypes=False,  # type: bool
    key_factory=None,  # type: LazyFactory
    child=True,  # type: bool
    history=None,  # type: Optional[bool]
    data=None,  # type: Optional[bool]
    custom_data_relationship=None,  # type: Optional[DataRelationship]
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_update_name=None,  # type: Optional[str]
):
    # type: (...) -> Type[DictObject[KT, VT]]
    """
    Make auxiliary protected dictionary object class.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param key_types: Key types.
    :type key_types: str or type or None or tuple[str or type or None]

    :param key_subtypes: Whether to accept subtypes for the keys.
    :type key_subtypes: bool

    :param key_factory: Key factory.
    :type key_factory: str or collections.abc.Callable or None

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :return: Protected dictionary object class.
    :rtype: type[objetto.objects.DictObject]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_dict_cls'"):
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

    # Prepare dct.
    dct = {}  # type: Dict[str, Any]

    # Key relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_dict_cls'"):
        key_relationship = KeyRelationship(
            types=key_types,
            subtypes=key_subtypes,
            checked=checked,
            module=module,
            factory=key_factory,
        )
        dct.update({"_key_relationship": key_relationship})

    # Reactions.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_dict_cls'"):
        dct.update(_prepare_reactions(reactions))

    # Batch names.
    if batch_update_name:
        dct["_BATCH_UPDATE_NAME"] = batch_update_name

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
        dct=dct,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'protected_dict_cls'"):
        base = DictObject  # type: Type[DictObject[KT, VT]]
        return make_auxiliary_cls(base, **cls_kwargs)


def list_cls(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_insert_name=None,  # type: Optional[str]
    batch_delete_name=None,  # type: Optional[str]
    batch_update_name=None,  # type: Optional[str]
    batch_move_name=None,  # type: Optional[str]
):
    # type: (...) -> Type[MutableListObject[T]]
    """
    Make auxiliary mutable list object class.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_insert_name: Batch name for insert operations.
    :type batch_insert_name: str or None

    :param batch_delete_name: Batch name for delete operations.
    :type batch_delete_name: str or None

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :param batch_move_name: Batch name for move operations.
    :type batch_move_name: str or None

    :return: Mutable list object class.
    :rtype: type[objetto.objects.MutableListObject]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'list_cls'"):
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

    # Prepare dct.
    dct = {}  # type: Dict[str, Any]

    # Reactions.
    with ReraiseContext((TypeError, ValueError), "defining 'list_cls'"):
        dct.update(_prepare_reactions(reactions))

    # Batch names.
    if batch_insert_name:
        dct["_BATCH_INSERT_NAME"] = batch_insert_name
    if batch_delete_name:
        dct["_BATCH_DELETE_NAME"] = batch_delete_name
    if batch_update_name:
        dct["_BATCH_UPDATE_NAME"] = batch_update_name
    if batch_move_name:
        dct["_BATCH_MOVE_NAME"] = batch_move_name

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
        dct=dct,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'list_cls'"):
        mutable_base = MutableListObject  # type: Type[MutableListObject[T]]
        return make_auxiliary_cls(mutable_base, **cls_kwargs)


def protected_list_cls(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_insert_name=None,  # type: Optional[str]
    batch_delete_name=None,  # type: Optional[str]
    batch_update_name=None,  # type: Optional[str]
    batch_move_name=None,  # type: Optional[str]
):
    # type: (...) -> Type[ListObject[T]]
    """
    Make auxiliary protected list object class.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_insert_name: Batch name for insert operations.
    :type batch_insert_name: str or None

    :param batch_delete_name: Batch name for delete operations.
    :type batch_delete_name: str or None

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :param batch_move_name: Batch name for move operations.
    :type batch_move_name: str or None

    :return: Protected list object class.
    :rtype: type[objetto.objects.ListObject]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_list_cls'"):
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

    # Prepare dct.
    dct = {}  # type: Dict[str, Any]

    # Reactions.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_list_cls'"):
        dct.update(_prepare_reactions(reactions))

    # Batch names.
    if batch_insert_name:
        dct["_BATCH_INSERT_NAME"] = batch_insert_name
    if batch_delete_name:
        dct["_BATCH_DELETE_NAME"] = batch_delete_name
    if batch_update_name:
        dct["_BATCH_UPDATE_NAME"] = batch_update_name
    if batch_move_name:
        dct["_BATCH_MOVE_NAME"] = batch_move_name

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
        dct=dct,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'protected_list_cls'"):
        base = ListObject  # type: Type[ListObject[T]]
        return make_auxiliary_cls(base, **cls_kwargs)


def set_cls(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_update_name=None,  # type: Optional[str]
    batch_remove_name=None,  # type: Optional[str]
):
    # type: (...) -> Type[MutableSetObject[T]]
    """
    Make auxiliary mutable set object class.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :param batch_remove_name: Batch name for remove operations.
    :type batch_remove_name: str or None

    :return: Mutable set object class.
    :rtype: type[objetto.objects.MutableSetObject]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'set_cls'"):
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

    # Prepare dct.
    dct = {}  # type: Dict[str, Any]

    # Reactions.
    with ReraiseContext((TypeError, ValueError), "defining 'set_cls'"):
        dct.update(_prepare_reactions(reactions))

    # Batch names.
    if batch_update_name:
        dct["_BATCH_UPDATE_NAME"] = batch_update_name
    if batch_remove_name:
        dct["_BATCH_REMOVE_NAME"] = batch_remove_name

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
        dct=dct,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'set_cls'"):
        mutable_base = MutableSetObject  # type: Type[MutableSetObject[T]]
        return make_auxiliary_cls(mutable_base, **cls_kwargs)


def protected_set_cls(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
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
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    reactions=None,  # type: ReactionsType
    batch_update_name=None,  # type: Optional[str]
    batch_remove_name=None,  # type: Optional[str]
):
    # type: (...) -> Type[SetObject[T]]
    """
    Make auxiliary protected set object class.

    :param types: Types.
    :type types: str or type or None or tuple[str or type or None]

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to perform runtime type check.
    :type checked: bool

    :param module: Module path for lazy types/factories.
    :type module: str or None

    :param factory: Value factory.
    :type factory: str or collections.abc.Callable or None

    :param serialized: Whether should be serialized.
    :type serialized: bool

    :param serializer: Custom serializer.
    :type serializer: str or collections.abc.Callable or None

    :param deserializer: Custom deserializer.
    :type deserializer: str or collections.abc.Callable or None

    :param represented: Whether should be represented.
    :type represented: bool

    :param child: Whether object values should be adopted as children.
    :type child: bool

    :param history: Whether to propagate the history to the child object value.
    :type history: bool

    :param data: Whether to generate data for the value.
    :type data: bool

    :param custom_data_relationship: Custom data relationship.
    :type custom_data_relationship: objetto.data.DataRelationship or None

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :param reactions: Reaction functions ordered by priority.
    :type reactions: str or collections.abc.Callable or None or \
collections.abc.Iterable[str or collections.abc.Callable]

    :param batch_update_name: Batch name for update operations.
    :type batch_update_name: str or None

    :param batch_remove_name: Batch name for remove operations.
    :type batch_remove_name: str or None

    :return: Protected set object class.
    :rtype: type[objetto.objects.SetObject]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_set_cls'"):
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

    # Prepare dct.
    dct = {}  # type: Dict[str, Any]

    # Reactions.
    with ReraiseContext((TypeError, ValueError), "defining 'protected_set_cls'"):
        dct.update(_prepare_reactions(reactions))

    # Batch names.
    if batch_update_name:
        dct["_BATCH_UPDATE_NAME"] = batch_update_name
    if batch_remove_name:
        dct["_BATCH_REMOVE_NAME"] = batch_remove_name

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
        dct=dct,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'protected_set_cls'"):
        base = SetObject  # type: Type[SetObject[T]]
        return make_auxiliary_cls(base, **cls_kwargs)
