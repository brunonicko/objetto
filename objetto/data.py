# -*- coding: utf-8 -*-
"""Data."""

from typing import TYPE_CHECKING, TypeVar

from ._data import DataAttribute, DataRelationship
from ._data import InteractiveData as Data
from ._data import InteractiveDictData as DictData
from ._data import InteractiveListData as ListData
from ._data import InteractiveSetData as SetData
from ._bases import MISSING
from ._structures import KeyRelationship, make_auxiliary_cls
from .utils.caller_module import get_caller_module
from .utils.reraise_context import ReraiseContext

if TYPE_CHECKING:
    from typing import Any, Iterable, Optional, Type, Union

    from .utils.factoring import LazyFactory

__all__ = [
    "Data",
    "data_attribute",
    "data_dict_attribute",
    "data_list_attribute",
    "data_set_attribute",
    "data_dict_cls",
    "data_list_cls",
    "data_set_cls",
]


T = TypeVar("T")  # Any type.
KT = TypeVar("KT")  # Any key type.
VT = TypeVar("VT")  # Any value type.


def data_attribute(
    types=(),  # type: Union[Type[T], str, Iterable[Union[Type[T], str]]]
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
):
    # type: (...) -> DataAttribute[T]
    """
    Make data attribute.

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
    :param default: Default value.
    :param default_factory: Default value factory.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :return: Data attribute.
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
        )  # type: DataAttribute[T]

    return attribute


def data_dict_attribute(
    types=(),  # type: Union[Type[VT], str, Iterable[Union[Type[VT], str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], str, Iterable[Union[Type[KT], str]]]
    key_subtypes=False,  # type: bool
    key_checked=True,  # type: bool
    key_factory=None,  # type: LazyFactory
    default=MISSING,  # type: Any
    default_factory=None,  # type: LazyFactory
    required=False,  # type: bool
    changeable=True,  # type: bool
    deletable=False,  # type: bool
    finalized=False,  # type: bool
    abstracted=False,  # type: bool
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
):
    # type: (...) -> DataAttribute[DictData[KT, VT]]
    """
    Make dictionary data attribute.

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
    :param key_types: Key types.
    :param key_subtypes: Whether to accept subtypes for the keys.
    :param key_checked: Whether to perform runtime type check for the keys.
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
    :return: Dictionary data attribute.
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
            key_checked=key_checked,
            key_factory=key_factory,
            qual_name=qual_name,
            unique=unique,
        )

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
        return DataAttribute(
            relationship=relationship,
            default=default,
            default_factory=default_factory,
            module=module,
            required=required,
            changeable=changeable,
            deletable=deletable,
            finalized=finalized,
            abstracted=abstracted,
        )


def data_list_attribute(
    types=(),  # type: Union[Type[T], str, Iterable[Union[Type[T], str]]]
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
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
):
    # type: (...) -> DataAttribute[ListData[T]]
    """
    Make dictionary list attribute.

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
    :param default: Default value.
    :param default_factory: Default value factory.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :return: List data attribute.
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
        )

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
        return DataAttribute(
            relationship=relationship,
            default=default,
            default_factory=default_factory,
            module=module,
            required=required,
            changeable=changeable,
            deletable=deletable,
            finalized=finalized,
            abstracted=abstracted,
        )


def data_set_attribute(
    types=(),  # type: Union[Type[T], str, Iterable[Union[Type[T], str]]]
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
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
):
    # type: (...) -> DataAttribute[SetData[T]]
    """
    Make dictionary set attribute.

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
    :param default: Default value.
    :param default_factory: Default value factory.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :return: Set data attribute.
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
        )

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
        return DataAttribute(
            relationship=relationship,
            default=default,
            default_factory=default_factory,
            module=module,
            required=required,
            changeable=changeable,
            deletable=deletable,
            finalized=finalized,
            abstracted=abstracted,
        )


def data_dict_cls(
    types=(),  # type: Union[Type[VT], str, Iterable[Union[Type[VT], str]]]
    subtypes=False,  # type: bool
    checked=None,  # type: Optional[bool]
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    key_types=(),  # type: Union[Type[KT], str, Iterable[Union[Type[KT], str]]]
    key_subtypes=False,  # type: bool
    key_checked=True,  # type: bool
    key_factory=None,  # type: LazyFactory
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
):
    # type: (...) -> Type[DictData[KT, VT]]
    """
    Make auxiliary dictionary data class.

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
    :param key_types: Key types.
    :param key_subtypes: Whether to accept subtypes for the keys.
    :param key_checked: Whether to perform runtime type check for the keys.
    :param key_factory: Key factory.
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :return: Dictionary data class.
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
            checked=key_checked,
            module=module,
            factory=key_factory,
        )
        dct = {"_key_relationship": key_relationship}

    # Make class.
    base = DictData  # type: Type[DictData[KT, VT]]
    with ReraiseContext(TypeError, "defining 'data_dict_cls'"):
        cls = make_auxiliary_cls(
            base,
            relationship,
            qual_name=qual_name,
            module=module,
            unique=unique,
            dct=dct,
        )

    return cls


def data_list_cls(
    types=(),  # type: Union[Type[T], str, Iterable[Union[Type[T], str]]]
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
    Make auxiliary list data class.

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
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :return: List data class.
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
    base = ListData  # type: Type[ListData[T]]
    with ReraiseContext(TypeError, "defining 'data_list_cls'"):
        cls = make_auxiliary_cls(
            base,
            relationship,
            qual_name=qual_name,
            module=module,
            unique=unique,
        )

    return cls


def data_set_cls(
    types=(),  # type: Union[Type[T], str, Iterable[Union[Type[T], str]]]
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
    Make auxiliary set data class.

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
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :return: Set data class.
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
    base = SetData  # type: Type[SetData[T]]
    with ReraiseContext(TypeError, "defining 'data_set_cls'"):
        cls = make_auxiliary_cls(
            base,
            relationship,
            qual_name=qual_name,
            module=module,
            unique=unique,
        )

    return cls
