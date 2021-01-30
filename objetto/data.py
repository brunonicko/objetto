# -*- coding: utf-8 -*-
"""Data."""

from typing import TYPE_CHECKING, TypeVar

from ._bases import MISSING
from ._data import (
    Data,
    DataAttribute,
    DataAttributeMeta,
    DataMeta,
    DataRelationship,
    DictData,
    DictDataMeta,
    InteractiveData,
    InteractiveDictData,
    InteractiveListData,
    InteractiveSetData,
    ListData,
    ListDataMeta,
    SetData,
    SetDataMeta,
)
from ._structures import (
    KeyRelationship,
    UniqueDescriptor,
    make_auxiliary_cls,
    unique_descriptor,
)
from .utils.caller_module import get_caller_module
from .utils.reraise_context import ReraiseContext

if TYPE_CHECKING:
    from typing import Any, Dict, Iterable, Optional, Type, Union

    from .utils.factoring import LazyFactory

__all__ = [
    "DataRelationship",
    "KeyRelationship",
    "UniqueDescriptor",
    "DataAttributeMeta",
    "DataMeta",
    "Data",
    "InteractiveData",
    "DictDataMeta",
    "DictData",
    "InteractiveDictData",
    "ListDataMeta",
    "ListData",
    "InteractiveListData",
    "SetDataMeta",
    "SetData",
    "InteractiveSetData",
    "DataAttribute",
    "unique_descriptor",
    "data_attribute",
    "data_constant_attribute",
    "data_dict_attribute",
    "data_protected_dict_attribute",
    "data_list_attribute",
    "data_protected_list_attribute",
    "data_set_attribute",
    "data_protected_set_attribute",
    "data_dict_cls",
    "data_list_cls",
    "data_set_cls",
]


T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Any key type.
VT = TypeVar("VT")  # Any value type.


if TYPE_CHECKING:
    NT = Union[Type[None], None]
    InteractiveDictAttribute = DataAttribute[InteractiveDictData[KT, VT]]
    InteractiveListAttribute = DataAttribute[InteractiveListData[T]]
    InteractiveSetAttribute = DataAttribute[InteractiveSetData[T]]
    DictAttribute = DataAttribute[DictData[KT, VT]]
    ListAttribute = DataAttribute[ListData[T]]
    SetAttribute = DataAttribute[SetData[T]]


def data_attribute(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    default=MISSING,  # type: Any
    default_factory=None,  # type: LazyFactory
    required=True,  # type: bool
    changeable=True,  # type: bool
    deletable=False,  # type: bool
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
):
    # type: (...) -> DataAttribute[T]
    """
    Make data attribute.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

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

    :return: Data attribute.
    :rtype: objetto.data.DataAttribute

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_attribute'"):
        relationship = DataRelationship(
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

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'data_attribute'"):
        attribute = DataAttribute(
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
        )  # type: DataAttribute[T]

    return attribute


def data_constant_attribute(
    value,  # type: T
    checked=None,  # type: Optional[bool]
    serialized=False,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=False,  # type: bool
    compared=True,  # type: bool
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    metadata=None,  # type: Any
):
    # type: (...) -> DataAttribute[T]
    """
    Make constant data attribute.

    :param value: Constant value.

    :param checked: Whether to type check when implementing abstract constant attribute.
    :type checked: bool or None

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

    :param finalized: If True, attribute can't be overridden by subclasses.
    :type finalized: bool

    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :type abstracted: bool

    :param metadata: Metadata.

    :return: Constant data attribute.
    :rtype: objetto.data.DataAttribute

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_constant_attribute'"):
        relationship = DataRelationship(
            types=type(value),
            subtypes=False,
            checked=abstracted if checked is None else checked,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            compared=compared,
        )

    # Make attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'data_constant_attribute'"):
        attribute_ = DataAttribute(
            relationship=relationship,
            default=value,
            default_factory=None,
            required=False,
            changeable=False,
            deletable=False,
            finalized=finalized,
            abstracted=abstracted,
            metadata=metadata,
        )  # type: DataAttribute[T]

    return attribute_


def data_dict_attribute(
    types=(),  # type: Union[Type[VT], NT, str, Iterable[Union[Type[VT], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], NT, str, Iterable[Union[Type[KT], NT, str]]]
    key_subtypes=False,  # type: bool
    key_factory=None,  # type: LazyFactory
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
):
    # type: (...) -> InteractiveDictAttribute[KT, VT]
    """
    Make interactive dictionary data attribute.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

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

    :return: Interactive dictionary data attribute.
    :rtype: objetto.data.DataAttribute[objetto.data.InteractiveDictData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make dictionary class.
    with ReraiseContext((TypeError, ValueError), "defining 'data_dict_attribute'"):
        dict_type = data_dict_cls(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=None,
            deserializer=None,
            represented=represented,
            compared=compared,
            key_types=key_types,
            key_subtypes=key_subtypes,
            key_factory=key_factory,
            qual_name=qual_name,
            unique=unique,
        )  # type: Type[InteractiveDictData[KT, VT]]

    # Factory that forces the dictionary type.
    def dict_factory(initial=()):
        if type(initial) is dict_type:
            return initial
        else:
            return dict_type(initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = {}

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_dict_attribute'"):
        relationship = DataRelationship(
            types=dict_type,
            subtypes=False,
            checked=checked,
            module=module,
            factory=dict_factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            compared=compared,
        )

    # Attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'data_dict_attribute'"):
        attribute_ = DataAttribute(
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
        )  # type: DataAttribute[InteractiveDictData[KT, VT]]

    return attribute_


def data_protected_dict_attribute(
    types=(),  # type: Union[Type[VT], NT, str, Iterable[Union[Type[VT], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], NT, str, Iterable[Union[Type[KT], NT, str]]]
    key_subtypes=False,  # type: bool
    key_factory=None,  # type: LazyFactory
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
):
    # type: (...) -> DictAttribute[KT, VT]
    """
    Make protected dictionary data attribute.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

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

    :return: Protected dictionary data attribute.
    :rtype: objetto.data.DataAttribute[objetto.data.DictData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make dictionary class.
    with ReraiseContext(
        (TypeError, ValueError), "defining 'data_protected_dict_attribute'"
    ):
        dict_type = data_protected_dict_cls(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=None,
            deserializer=None,
            represented=represented,
            compared=compared,
            key_types=key_types,
            key_subtypes=key_subtypes,
            key_factory=key_factory,
            qual_name=qual_name,
            unique=unique,
        )  # type: Type[DictData[KT, VT]]

    # Factory that forces the dictionary type.
    def dict_factory(initial=()):
        if type(initial) is dict_type:
            return initial
        else:
            return dict_type(initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = {}

    # Relationship.
    with ReraiseContext(
        (TypeError, ValueError), "defining 'data_protected_dict_attribute'"
    ):
        relationship = DataRelationship(
            types=dict_type,
            subtypes=False,
            checked=checked,
            module=module,
            factory=dict_factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            compared=compared,
        )

    # Attribute.
    with ReraiseContext(
        (TypeError, ValueError), "defining 'data_protected_dict_attribute'"
    ):
        attribute_ = DataAttribute(
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
        )  # type: DataAttribute[DictData[KT, VT]]

    return attribute_


def data_list_attribute(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
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
):
    # type: (...) -> InteractiveListAttribute[T]
    """
    Make interactive list data attribute.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

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

    :return: Interactive list data attribute.
    :rtype: objetto.data.DataAttribute[objetto.data.InteractiveListData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make list class.
    with ReraiseContext((TypeError, ValueError), "defining 'data_list_attribute'"):
        list_type = data_list_cls(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=None,
            deserializer=None,
            represented=represented,
            compared=compared,
            qual_name=qual_name,
            unique=unique,
        )  # type: Type[InteractiveListData[T]]

    # Factory that forces the list type.
    def list_factory(initial=()):
        if type(initial) is list_type:
            return initial
        else:
            return list_type(initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = {}

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_list_attribute'"):
        relationship = DataRelationship(
            types=list_type,
            subtypes=False,
            checked=checked,
            module=module,
            factory=list_factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            compared=compared,
        )

    # Attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'data_list_attribute'"):
        attribute_ = DataAttribute(
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
        )  # type: DataAttribute[InteractiveListData[T]]

    return attribute_


def data_protected_list_attribute(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
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
):
    # type: (...) -> ListAttribute[T]
    """
    Make protected list data attribute.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

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

    :return: Protected list data attribute.
    :rtype: objetto.data.DataAttribute[objetto.data.ListData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make list class.
    with ReraiseContext(
        (TypeError, ValueError), "defining 'data_protected_list_attribute'"
    ):
        list_type = data_protected_list_cls(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=None,
            deserializer=None,
            represented=represented,
            compared=compared,
            qual_name=qual_name,
            unique=unique,
        )  # type: Type[ListData[T]]

    # Factory that forces the list type.
    def list_factory(initial=()):
        if type(initial) is list_type:
            return initial
        else:
            return list_type(initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = {}

    # Relationship.
    with ReraiseContext(
        (TypeError, ValueError), "defining 'data_protected_list_attribute'"
    ):
        relationship = DataRelationship(
            types=list_type,
            subtypes=False,
            checked=checked,
            module=module,
            factory=list_factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            compared=compared,
        )

    # Attribute.
    with ReraiseContext(
        (TypeError, ValueError), "defining 'data_protected_list_attribute'"
    ):
        attribute_ = DataAttribute(
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
        )  # type: DataAttribute[ListData[T]]

    return attribute_


def data_set_attribute(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
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
):
    # type: (...) -> InteractiveSetAttribute[T]
    """
    Make interactive set data attribute.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

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

    :return: Interactive set data attribute.
    :rtype: objetto.data.DataAttribute[objetto.data.InteractiveSetData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make set class.
    with ReraiseContext((TypeError, ValueError), "defining 'data_set_attribute'"):
        set_type = data_set_cls(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=None,
            deserializer=None,
            represented=represented,
            compared=compared,
            qual_name=qual_name,
            unique=unique,
        )  # type: Type[InteractiveSetData[T]]

    # Factory that forces the set type.
    def set_factory(initial=()):
        if type(initial) is set_type:
            return initial
        else:
            return set_type(initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = {}

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_set_attribute'"):
        relationship = DataRelationship(
            types=set_type,
            subtypes=False,
            checked=checked,
            module=module,
            factory=set_factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            compared=compared,
        )

    # Attribute.
    with ReraiseContext((TypeError, ValueError), "defining 'data_set_attribute'"):
        attribute_ = DataAttribute(
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
        )  # type: DataAttribute[InteractiveSetData[T]]

    return attribute_


def data_protected_set_attribute(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
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
):
    # type: (...) -> SetAttribute[T]
    """
    Make protected set data attribute.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

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

    :return: Protected set data attribute.
    :rtype: objetto.data.DataAttribute[objetto.data.SetData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make set class.
    with ReraiseContext(
        (TypeError, ValueError), "defining 'data_protected_set_attribute'"
    ):
        set_type = data_protected_set_cls(
            types=types,
            subtypes=subtypes,
            checked=checked,
            module=module,
            factory=factory,
            serialized=serialized,
            serializer=None,
            deserializer=None,
            represented=represented,
            compared=compared,
            qual_name=qual_name,
            unique=unique,
        )  # type: Type[SetData[T]]

    # Factory that forces the set type.
    def set_factory(initial=()):
        if type(initial) is set_type:
            return initial
        else:
            return set_type(initial)

    # Get default value/factory.
    if changeable and not required and default is MISSING and default_factory is None:
        default = {}

    # Relationship.
    with ReraiseContext(
        (TypeError, ValueError), "defining 'data_protected_set_attribute'"
    ):
        relationship = DataRelationship(
            types=set_type,
            subtypes=False,
            checked=checked,
            module=module,
            factory=set_factory,
            serialized=serialized,
            serializer=serializer,
            deserializer=deserializer,
            represented=represented,
            compared=compared,
        )

    # Attribute.
    with ReraiseContext(
        (TypeError, ValueError), "defining 'data_protected_set_attribute'"
    ):
        attribute_ = DataAttribute(
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
        )  # type: DataAttribute[SetData[T]]

    return attribute_


def data_dict_cls(
    types=(),  # type: Union[Type[VT], NT, str, Iterable[Union[Type[VT], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], NT, str, Iterable[Union[Type[KT], NT, str]]]
    key_subtypes=False,  # type: bool
    key_factory=None,  # type: LazyFactory
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
):
    # type: (...) -> Type[InteractiveDictData[KT, VT]]
    """
    Make auxiliary interactive dictionary data class.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

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

    :return: Interactive dictionary data class.
    :type: type[objetto.data.InteractiveDictData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_dict_cls'"):
        relationship = DataRelationship(
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

    # Key relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_dict_cls'"):
        key_relationship = KeyRelationship(
            types=key_types,
            subtypes=key_subtypes,
            checked=checked,
            module=module,
            factory=key_factory,
        )
        dct = {"_key_relationship": key_relationship}

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
        dct=dct,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'data_dict_cls'"):
        interactive_base = (
            InteractiveDictData
        )  # type: Type[InteractiveDictData[KT, VT]]
        return make_auxiliary_cls(interactive_base, **cls_kwargs)


def data_protected_dict_cls(
    types=(),  # type: Union[Type[VT], NT, str, Iterable[Union[Type[VT], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], NT, str, Iterable[Union[Type[KT], NT, str]]]
    key_subtypes=False,  # type: bool
    key_factory=None,  # type: LazyFactory
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
):
    # type: (...) -> Type[DictData[KT, VT]]
    """
    Make auxiliary protected dictionary data class.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

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

    :return: Protected dictionary data class.
    :type: type[objetto.data.DictData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_protected_dict_cls'"):
        relationship = DataRelationship(
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

    # Key relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_protected_dict_cls'"):
        key_relationship = KeyRelationship(
            types=key_types,
            subtypes=key_subtypes,
            checked=checked,
            module=module,
            factory=key_factory,
        )
        dct = {"_key_relationship": key_relationship}

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
        dct=dct,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'data_protected_dict_cls'"):
        base = DictData  # type: Type[DictData[KT, VT]]
        return make_auxiliary_cls(base, **cls_kwargs)


def data_list_cls(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
):
    # type: (...) -> Type[InteractiveListData[T]]
    """
    Make auxiliary interactive list data class.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :return: Interactive list data class.
    :type: type[objetto.data.InteractiveListData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_list_cls'"):
        relationship = DataRelationship(
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

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'data_list_cls'"):
        interactive_base = InteractiveListData  # type: Type[InteractiveListData[T]]
        return make_auxiliary_cls(interactive_base, **cls_kwargs)


def data_protected_list_cls(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
):
    # type: (...) -> Type[ListData[T]]
    """
    Make auxiliary protected list data class.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :return: Protected list data class.
    :type: type[objetto.data.ListData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_protected_list_cls'"):
        relationship = DataRelationship(
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

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'data_protected_list_cls'"):
        base = ListData  # type: Type[ListData[T]]
        return make_auxiliary_cls(base, **cls_kwargs)


def data_set_cls(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
):
    # type: (...) -> Type[InteractiveSetData[T]]
    """
    Make auxiliary interactive set data class.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :return: Interactive set data class.
    :type: type[objetto.data.InteractiveSetData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_set_cls'"):
        relationship = DataRelationship(
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

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'data_set_cls'"):
        interactive_base = InteractiveSetData  # type: Type[InteractiveSetData[T]]
        return make_auxiliary_cls(interactive_base, **cls_kwargs)


def data_protected_set_cls(
    types=(),  # type: Union[Type[T], NT, str, Iterable[Union[Type[T], NT, str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
):
    # type: (...) -> Type[SetData[T]]
    """
    Make auxiliary protected set data class.

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

    :param compared: Whether the value should be leverage when comparing.
    :type compared: bool

    :param qual_name: Optional type qualified name for the generated class.
    :type qual_name: str or None

    :param unique: Whether generated class should have a unique descriptor.
    :type unique: bool

    :return: Protected set data class.
    :type: type[objetto.data.SetData]

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
    with ReraiseContext((TypeError, ValueError), "defining 'data_protected_set_cls'"):
        relationship = DataRelationship(
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

    # Make class.
    cls_kwargs = dict(
        relationship=relationship,
        qual_name=qual_name,
        module=module,
        unique_descriptor_name="unique_hash" if unique else None,
    )  # type: Dict[str, Any]
    with ReraiseContext(TypeError, "defining 'data_protected_set_cls'"):
        base = SetData  # type: Type[SetData[T]]
        return make_auxiliary_cls(base, **cls_kwargs)
