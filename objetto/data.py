# -*- coding: utf-8 -*-
"""Data."""

from typing import TYPE_CHECKING, TypeVar, cast

from ._structures import MISSING, make_auxiliary_cls, KeyRelationship
from ._data import (
    Data,
    InteractiveData,
    DataAttribute,
    DataRelationship,
    DictData,
    InteractiveDictData,
    ListData,
    InteractiveListData,
    SetData,
    InteractiveSetData,
)
from .utils.caller_module import get_caller_module

if TYPE_CHECKING:
    from typing import Any, Optional, Type, Union, Iterable

    from .utils.factoring import LazyFactory

__all__ = [
    "Data",
    "InteractiveData",
    "data_attribute",
    "data_dict_attribute",
    "data_list_attribute",
    "data_set_attribute",
    "data_dict_cls",
    "data_list_cls",
    "data_set_cls",
]


_T = TypeVar("_T")  # Any type.
_KT = TypeVar("_KT")  # Any type.
_VT = TypeVar("_VT")  # Any type.


def data_attribute(
    types=(),  # type: Union[Type[_T], str, Iterable[Union[Type[_T], str]]]
    subtypes=False,  # type: bool
    checked=True,  # type: bool
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
    # type: (...) -> DataAttribute[_T]
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
    :param compared: Whether the value should be leverage when comparing for equality.
    :param default: Default value.
    :param default_factory: Default value factory.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :return: Data attribute.
    :raises ValueError: Specified both `default` and `default_factory`.
    :raises ValueError: Both `required` and `deletable` are True.
    :raises ValueError: Both `finalized` and `abstracted` are True.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
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
    )  # type: DataAttribute[_T]

    return attribute


def data_dict_attribute(
    types=(),  # type: Union[Type[_VT], str, Iterable[Union[Type[_VT], str]]]
    subtypes=False,  # type: bool
    checked=True,  # type: bool
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    key_types=(),  # type: Union[Type[_KT], str, Iterable[Union[Type[_KT], str]]]
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
    interactive=True,  # type: bool
):
    # type: (...) -> DataAttribute[InteractiveDictData[_KT, _VT]]
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
    :param compared: Whether the value should be leverage when comparing for equality.
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
    :param interactive: Whether generated class should be interactive.
    :return: Dictionary data class.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make dictionary class.
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
        interactive=interactive,
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
    types=(),  # type: Union[Type[_T], str, Iterable[Union[Type[_T], str]]]
    subtypes=False,  # type: bool
    checked=True,  # type: bool
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
    interactive=True,  # type: bool
):
    # type: (...) -> DataAttribute[InteractiveListData[_T]]
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
    :param compared: Whether the value should be leverage when comparing for equality.
    :param default: Default value.
    :param default_factory: Default value factory.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :param interactive: Whether generated class should be interactive.
    :return: Dictionary data class.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make list class.
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
        interactive=interactive,
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
    types=(),  # type: Union[Type[_T], str, Iterable[Union[Type[_T], str]]]
    subtypes=False,  # type: bool
    checked=True,  # type: bool
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
    interactive=True,  # type: bool
):
    # type: (...) -> DataAttribute[InteractiveSetData[_T]]
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
    :param compared: Whether the value should be leverage when comparing for equality.
    :param default: Default value.
    :param default_factory: Default value factory.
    :param required: Whether attribute is required to have a value or not.
    :param changeable: Whether attribute value can be changed.
    :param deletable: Whether attribute value can be deleted.
    :param finalized: If True, attribute can't be overridden by subclasses.
    :param abstracted: If True, attribute needs to be overridden by subclasses.
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :param interactive: Whether generated class should be interactive.
    :return: Dictionary data class.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Make set class.
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
        interactive=interactive,
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
    types=(),  # type: Union[Type[_VT], str, Iterable[Union[Type[_VT], str]]]
    subtypes=False,  # type: bool
    checked=True,  # type: bool
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    key_types=(),  # type: Union[Type[_KT], str, Iterable[Union[Type[_KT], str]]]
    key_subtypes=False,  # type: bool
    key_checked=True,  # type: bool
    key_factory=None,  # type: LazyFactory
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    interactive=True,  # type: bool
):
    # type: (...) -> Union[Type[InteractiveDictData[_KT, _VT]], Type[DictData[_KT, _VT]]]
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
    :param compared: Whether the value should be leverage when comparing for equality.
    :param key_types: Key types.
    :param key_subtypes: Whether to accept subtypes for the keys.
    :param key_checked: Whether to perform runtime type check for the keys.
    :param key_factory: Key factory.
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :param interactive: Whether generated class should be interactive.
    :return: Dictionary data class.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
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
    key_relationship = KeyRelationship(
        types=key_types,
        subtypes=key_subtypes,
        checked=key_checked,
        module=module,
        factory=key_factory,
    )
    dct = {"_key_relationship": key_relationship}

    # Make class.
    base = (
        cast("Type[InteractiveDictData[_KT, _VT]]", InteractiveDictData)
        if interactive else
        cast("Type[DictData[_KT, _VT]]", DictData)
    )
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
    types=(),  # type: Union[Type[_T], str, Iterable[Union[Type[_T], str]]]
    subtypes=False,  # type: bool
    checked=True,  # type: bool
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    interactive=True,  # type: bool
):
    # type: (...) -> Union[Type[InteractiveListData[_T]], Type[ListData[_T]]]
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
    :param compared: Whether the value should be leverage when comparing for equality.
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :param interactive: Whether generated class should be interactive.
    :return: List data class.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
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
    base = (
        cast("Type[InteractiveListData[_T]]", InteractiveListData)
        if interactive else
        cast("Type[ListData[_T]]", ListData)
    )
    cls = make_auxiliary_cls(
        base,
        relationship,
        qual_name=qual_name,
        module=module,
        unique=unique,
    )

    return cls


def data_set_cls(
    types=(),  # type: Union[Type[_T], str, Iterable[Union[Type[_T], str]]]
    subtypes=False,  # type: bool
    checked=True,  # type: bool
    module=None,  # type: Optional[str]
    factory=None,  # type: LazyFactory
    serialized=True,  # type: bool
    serializer=None,  # type: LazyFactory
    deserializer=None,  # type: LazyFactory
    represented=True,  # type: bool
    compared=True,  # type: bool
    qual_name=None,  # type: Optional[str]
    unique=False,  # type: bool
    interactive=True,  # type: bool
):
    # type: (...) -> Union[Type[InteractiveSetData[_T]], Type[SetData[_T]]]
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
    :param compared: Whether the value should be leverage when comparing for equality.
    :param qual_name: Optional type qualified name for the generated class.
    :param unique: Whether generated class should have a unique descriptor.
    :param interactive: Whether generated class should be interactive.
    :return: Set data class.
    """

    # Get module from caller if not provided.
    module = get_caller_module() if module is None else module

    # Relationship.
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
    base = (
        cast("Type[InteractiveSetData[_T]]", InteractiveSetData)
        if interactive else
        cast("Type[SetData[_T]]", SetData)
    )
    cls = make_auxiliary_cls(
        base,
        relationship,
        qual_name=qual_name,
        module=module,
        unique=unique,
    )

    return cls
