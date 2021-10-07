# -*- coding: utf-8 -*-
"""Objects."""

from functools import wraps

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from ._applications import Action
from ._bases import MISSING
from ._constants import BASE_STRING_TYPES
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
from .utils.simplify_exceptions import simplify_exceptions
from .utils.type_checking import assert_is_instance

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


def data_method(func):
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

    @wraps(func)
    @simplify_exceptions
    def decorated(*args, **kwargs):
        return func(*args, **kwargs)

    setattr(decorated, DATA_METHOD_TAG, True)
    return decorated


def data_relationship(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=True,
    serializer=None,
    deserializer=None,
    represented=True,
    compared=True,
):
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


def history_descriptor(size=None):

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
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    required=True,
    changeable=None,
    deletable=None,
    finalized=False,
    abstracted=False,
    metadata=None,
    delegated=False,
    dependencies=None,
    deserialize_to=None,
    batch_name=None,
):

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
        )

    return attribute_


def constant_attribute(
    value,
    subtypes=False,
    checked=True,
    serialized=False,
    serializer=None,
    deserializer=None,
    represented=False,
    data=True,
    finalized=False,
    abstracted=False,
    metadata=None,
):

    """
    Make constant attribute.

    :param value: Constant value.

    :param subtypes: Whether to accept subtypes.
    :type subtypes: bool

    :param checked: Whether to type check when overriding this constant attribute.
    :type checked: bool

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
            subtypes=subtypes,
            checked=checked,
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
        )

    return attribute_


def protected_attribute_pair(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    changeable=None,
    deletable=None,
    finalized=False,
    abstracted=False,
    metadata=None,
    protected_metadata=None,
    batch_name=None,
):

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
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    key_types=(),
    key_subtypes=False,
    key_factory=None,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    required=False,
    changeable=True,
    deletable=False,
    finalized=False,
    abstracted=False,
    metadata=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_update_name=None,
):

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
        )

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
        )

    return attribute_


def protected_dict_attribute(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    key_types=(),
    key_subtypes=False,
    key_factory=None,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    required=False,
    changeable=True,
    deletable=False,
    finalized=False,
    abstracted=False,
    metadata=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_update_name=None,
):

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
        )

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
        )

    return attribute_


def protected_dict_attribute_pair(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    key_types=(),
    key_subtypes=False,
    key_factory=None,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    finalized=False,
    abstracted=False,
    metadata=None,
    protected_metadata=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_update_name=None,
):

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
    )

    # Make protected attribute.
    protected_attribute = attribute(
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
    )

    def getter(iobj):
        """Getter delegate."""
        public_name = iobj.__.cls._attribute_names[public_attribute]
        return ProxyDictObject(iobj[public_name])

    protected_attribute.getter(getter)

    return protected_attribute, public_attribute


def list_attribute(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    required=False,
    changeable=True,
    deletable=False,
    finalized=False,
    abstracted=False,
    metadata=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_insert_name=None,
    batch_delete_name=None,
    batch_update_name=None,
    batch_move_name=None,
):

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
        )

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
        )

    return attribute_


def protected_list_attribute(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    required=False,
    changeable=True,
    deletable=False,
    finalized=False,
    abstracted=False,
    metadata=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_insert_name=None,
    batch_delete_name=None,
    batch_update_name=None,
    batch_move_name=None,
):

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
        )

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
        )

    return attribute_


def protected_list_attribute_pair(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    finalized=False,
    abstracted=False,
    metadata=None,
    protected_metadata=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_insert_name=None,
    batch_delete_name=None,
    batch_update_name=None,
    batch_move_name=None,
):

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
    )

    # Make protected attribute.
    protected_attribute = attribute(
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
    )

    def getter(iobj):
        """Getter delegate."""
        public_name = iobj.__.cls._attribute_names[public_attribute]
        return ProxyListObject(iobj[public_name])

    protected_attribute.getter(getter)

    return protected_attribute, public_attribute


def set_attribute(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    required=False,
    changeable=True,
    deletable=False,
    finalized=False,
    abstracted=False,
    metadata=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_update_name=None,
    batch_remove_name=None,
):

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
        )

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
        )

    return attribute_


def protected_set_attribute(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    required=False,
    changeable=True,
    deletable=False,
    finalized=False,
    abstracted=False,
    metadata=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_update_name=None,
    batch_remove_name=None,
):

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
        )

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
        )

    return attribute_


def protected_set_attribute_pair(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    default=MISSING,
    default_factory=None,
    finalized=False,
    abstracted=False,
    metadata=None,
    protected_metadata=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_update_name=None,
    batch_remove_name=None,
):

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
    )

    # Make protected attribute.
    protected_attribute = attribute(
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
    )

    def getter(iobj):
        """Getter delegate."""
        public_name = iobj.__.cls._attribute_names[public_attribute]
        return ProxySetObject(iobj[public_name])

    protected_attribute.getter(getter)

    return protected_attribute, public_attribute


def _prepare_reactions(reactions=None):

    """
    Conform reactions parameter value into a dictionary with reaction methods.

    :param reactions: Input reactions.
    :return: Dictionary with reaction methods.
    """
    dct = {}
    if reactions is None:
        return dct
    if isinstance(reactions, BASE_STRING_TYPES) or not isinstance(
        reactions, collections_abc.Iterable
    ):
        reactions = (reactions,)
    for i, reaction_ in enumerate(reactions):
        if isinstance(reaction_, BaseReaction) and reaction_.priority != i:
            reaction_ = reaction_.set_priority(i)
        elif reaction_ is None:
            continue
        else:
            reaction_decorator = reaction(priority=i)
            # noinspection PyArgumentList
            reaction_ = reaction_decorator(import_factory(reaction_))
        dct["__reaction{}".format(i)] = reaction_
    return dct


def dict_cls(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    key_types=(),
    key_subtypes=False,
    key_factory=None,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_update_name=None,
):

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
    dct = {}

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
    )
    with ReraiseContext(TypeError, "defining 'dict_cls'"):
        mutable_base = MutableDictObject
        return make_auxiliary_cls(mutable_base, **cls_kwargs)


def protected_dict_cls(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    key_types=(),
    key_subtypes=False,
    key_factory=None,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_update_name=None,
):

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
    dct = {}

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
    )
    with ReraiseContext(TypeError, "defining 'protected_dict_cls'"):
        base = DictObject
        return make_auxiliary_cls(base, **cls_kwargs)


def list_cls(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_insert_name=None,
    batch_delete_name=None,
    batch_update_name=None,
    batch_move_name=None,
):

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
    dct = {}

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
    )
    with ReraiseContext(TypeError, "defining 'list_cls'"):
        mutable_base = MutableListObject
        return make_auxiliary_cls(mutable_base, **cls_kwargs)


def protected_list_cls(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_insert_name=None,
    batch_delete_name=None,
    batch_update_name=None,
    batch_move_name=None,
):

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
    dct = {}

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
    )
    with ReraiseContext(TypeError, "defining 'protected_list_cls'"):
        base = ListObject
        return make_auxiliary_cls(base, **cls_kwargs)


def set_cls(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_update_name=None,
    batch_remove_name=None,
):

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
    dct = {}

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
    )
    with ReraiseContext(TypeError, "defining 'set_cls'"):
        mutable_base = MutableSetObject
        return make_auxiliary_cls(mutable_base, **cls_kwargs)


def protected_set_cls(
    types=(),
    subtypes=False,
    checked=None,
    module=None,
    factory=None,
    serialized=None,
    serializer=None,
    deserializer=None,
    represented=True,
    child=True,
    history=None,
    data=None,
    custom_data_relationship=None,
    qual_name=None,
    unique=False,
    reactions=None,
    batch_update_name=None,
    batch_remove_name=None,
):

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
    dct = {}

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
    )
    with ReraiseContext(TypeError, "defining 'protected_set_cls'"):
        base = SetObject
        return make_auxiliary_cls(base, **cls_kwargs)
