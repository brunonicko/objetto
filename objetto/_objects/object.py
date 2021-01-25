# -*- coding: utf-8 -*-
"""Object with state curated by attribute descriptors."""

from collections import Counter as ValueCounter
from contextlib import contextmanager
from inspect import getmro
from itertools import chain
from typing import TYPE_CHECKING, TypeVar, cast, overload
from weakref import WeakKeyDictionary

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import ensure_str, iteritems, raise_from, with_metaclass

from .._applications import Application
from .._bases import FINAL_METHOD_TAG, MISSING, Base, final, init_context, make_base_cls
from .._changes import Update
from .._data import BaseData, Data, DataAttribute, InteractiveDictData
from .._states import DictState, SetState
from .._structures import (
    BaseAttribute,
    BaseAttributeMeta,
    BaseAttributeStructureMeta,
    BaseMutableAttributeStructure,
)
from ..utils.dummy_context import DummyContext
from ..utils.reraise_context import ReraiseContext
from ..utils.type_checking import (
    assert_is_callable,
    assert_is_instance,
    assert_is_subclass,
)
from ..utils.weak_reference import WeakReference
from .bases import (
    DELETED,
    BaseMutableObject,
    BaseObject,
    BaseObjectFunctions,
    BaseObjectMeta,
    Relationship,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Counter,
        Dict,
        Iterable,
        Iterator,
        List,
        Mapping,
        MutableMapping,
        Optional,
        Set,
        Tuple,
        Type,
        Union,
    )

    from .._applications import Store
    from .._history import HistoryObject
    from ..utils.factoring import LazyFactory

__all__ = ["AttributeMeta", "Attribute", "ObjectMeta", "Object"]


T = TypeVar("T")  # Any type.


# noinspection PyTypeChecker
_A = TypeVar("_A", bound="Attribute")


@final
class AttributeMeta(BaseAttributeMeta):
    """
    Metaclass for :class:`objetto.objects.Attribute`.

    Inherits from:
      - :class:`objetto.bases.BaseAttributeMeta`

    Features:
      - Defines relationship type.
    """

    @property
    def _relationship_type(cls):
        # type: () -> Type[Relationship]
        """
        Relationship type.

        :rtype: type[objetto.objects.Relationship]
        """
        return Relationship


@final
class Attribute(with_metaclass(AttributeMeta, BaseAttribute[T])):
    """
    Attribute descriptor for :class:`objetto.objects.Object` classes.

    Metaclass:
      - :class:`objetto.objects.AttributeMeta`

    Inherits from:
      - :class:`objetto.bases.BaseAttribute`

    :param relationship: Relationship.
    :type relationship: objetto.objects.Relationship

    :param default: Default value.

    :param default_factory: Default value factory.
    :type default_factory: str or collections.abc.Callable or None

    :param module: Optional module path to use in case partial paths are provided.
    :type module: str or None

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

    :raises TypeError: Invalid parameter type.
    :raises ValueError: Invalid parameter value.
    :raises ValueError: Can't declare same dependency more than once.
    :raises ValueError: Provided 'changeable' but 'delegated' is True.
    :raises ValueError: Provided 'deletable' but 'delegated' is True.
    :raises ValueError: Provided 'dependencies' but 'delegated' is False.
    :raises ValueError: Provided 'deserialize_to' but 'serialized' is False.
    :raises ValueError: Can't provide a serialized attribute to 'deserialize_to'.
    """

    __slots__ = (
        "__delegated",
        "__dependencies",
        "__deserialize_to",
        "__fget",
        "__fset",
        "__fdel",
        "__data_attribute",
        "__batch_name",
    )

    def __init__(
        self,
        relationship=Relationship(),  # type: Relationship
        default=MISSING,  # type: Any
        default_factory=None,  # type: LazyFactory
        module=None,  # type: Optional[str]
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
        # type: (...) -> None

        # 'changeable', 'deletable', 'delegated', and 'dependencies'
        if delegated:
            if dependencies is None:
                dependencies = ()
            else:
                with ReraiseContext(
                    (TypeError, ValueError), "'dependencies' parameter"
                ):
                    if isinstance(dependencies, collections_abc.Iterable):
                        visited_dependencies = set()
                        for dependency in dependencies:
                            assert_is_instance(dependency, Attribute, subtypes=False)
                            if dependency in visited_dependencies:
                                error = "can't declare same dependency more than once"
                                raise ValueError(error)
                            visited_dependencies.add(dependency)
                        dependencies = tuple(dependencies)
                    else:
                        assert_is_instance(dependencies, Attribute, subtypes=False)
                        dependencies = (dependencies,)
            if changeable is not None:
                error = "provided 'changeable' but 'delegated' is True"
                raise ValueError(error)
            else:
                changeable = False
            if deletable is not None:
                error = "provided 'deletable' but 'delegated' is True"
                raise ValueError(error)
            else:
                deletable = False
        else:
            if dependencies is not None:
                error = "provided 'dependencies' but 'delegated' is False"
                raise ValueError(error)
            else:
                dependencies = ()
            if changeable is None:
                changeable = True
            else:
                changeable = bool(changeable)
            if deletable is None:
                deletable = False
            else:
                deletable = bool(deletable)

        # 'deserialize_to'
        if deserialize_to is not None:
            if not relationship.serialized:
                error = "provided 'deserialize_to' but 'serialized' is False"
                raise ValueError(error)
            else:
                with ReraiseContext(TypeError, "'deserialize_to' parameter"):
                    assert_is_instance(deserialize_to, Attribute)
                if deserialize_to.relationship.serialized:
                    error = "can't provide a serialized attribute to 'deserialize_to'"
                    raise ValueError(error)

        super(Attribute, self).__init__(
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
        )

        self.__delegated = bool(delegated)
        self.__dependencies = dependencies
        self.__deserialize_to = deserialize_to
        self.__fget = None  # type: Optional[Callable]
        self.__fset = None  # type: Optional[Callable]
        self.__fdel = None  # type: Optional[Callable]
        self.__data_attribute = None  # type: Optional[DataAttribute]
        self.__batch_name = (
            ensure_str(batch_name) if batch_name is not None else None
        )  # type: Optional[str]

    def __set__(self, instance, value):
        # type: (Object, T) -> None
        """
        Set attribute value.

        :param instance: Object instance.
        :type instance: objetto.objects.Object

        :param value: Value.
        """
        self.set_value(instance, value)

    def __delete__(self, instance):
        # type: (Object) -> None
        """
        Delete attribute value.

        :param instance: Object instance.
        :type instance: objetto.objects.Object
        """
        self.delete_value(instance)

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[str, Any]
        """
        dct = super(Attribute, self).to_dict()
        dct.update(
            {
                "delegated": self.delegated,
                "dependencies": self.dependencies,
                "deserialize_to": self.deserialize_to,
                "fget": self.fget,
                "fset": self.fset,
                "fdel": self.fdel,
                "batch_name": self.batch_name,
            }
        )
        return dct

    def set_value(self, instance, value):
        # type: (Object, T) -> None
        """
        Set attribute value.

        :param instance: Object instance.
        :type instance: objetto.objects.Object

        :param value: Value.
        """
        instance[self.get_name(instance)] = value

    def delete_value(self, instance):
        # type: (Object) -> None
        """
        Delete attribute value.

        :param instance: Object instance.
        :type instance: objetto.objects.Object
        """
        del instance[self.get_name(instance)]

    def getter(self, func):
        # type: (_A, Callable) -> _A
        """
        Define a getter delegate method.

        :param func: Delegate function.
        :type func: function

        :return: This attribute.
        :rtype: objetto.objects.Attribute

        :raises ValueError: Cannot define a getter for a non-delegated attribute.
        :raises ValueError: Getter delegate already defined.
        :raises TypeError: Invalid delegate type.
        """
        if not self.__delegated:
            error = "cannot define a getter for a non-delegated attribute"
            raise ValueError(error)
        if self.__fget is not None:
            error = "getter delegate already defined"
            raise ValueError(error)
        with ReraiseContext(TypeError, "attribute 'getter' delegate"):
            assert_is_callable(func)
        self.__fget = func
        return self

    def setter(self, func):
        # type: (_A, Callable) -> _A
        """
        Define a setter delegate method.

        :param func: Delegate function.
        :type func: function

        :return: This attribute.
        :rtype: objetto.objects.Attribute

        :raises ValueError: Cannot define a setter for a non-delegated attribute.
        :raises ValueError: Need to define a getter before defining a setter.
        :raises ValueError: Setter delegate already defined.
        :raises TypeError: Invalid delegate type.
        """
        if not self.__delegated:
            error = "cannot define a setter for a non-delegated attribute"
            raise ValueError(error)
        if self.__fget is None:
            error = "need to define a getter before defining a setter"
            raise ValueError(error)
        if self.__fset is not None:
            error = "setter delegate already defined"
            raise ValueError(error)
        with ReraiseContext(TypeError, "attribute 'setter' delegate"):
            assert_is_callable(func)
        self.__fset = func
        self._changeable = True
        return self

    def deleter(self, func):
        # type: (_A, Callable) -> _A
        """
        Define a deleter delegate method.

        :param func: Delegate function.
        :type func: function

        :return: This attribute.
        :rtype: objetto.objects.Attribute

        :raises ValueError: Cannot define a deleter for a non-delegated attribute.
        :raises ValueError: Need to define a getter before defining a deleter.
        :raises ValueError: Deleter delegate already defined.
        :raises TypeError: Invalid delegate type.
        """
        if not self.__delegated:
            error = "cannot define a deleter for a non-delegated attribute"
            raise ValueError(error)
        if self.__fget is None:
            error = "need to define a getter before defining a deleter"
            raise ValueError(error)
        if self.__fdel is not None:
            error = "deleter delegate already defined"
            raise ValueError(error)
        with ReraiseContext(TypeError, "attribute 'deleter' delegate"):
            assert_is_callable(func)
        self.__fdel = func
        self._deletable = True
        return self

    @property
    def relationship(self):
        # type: () -> Relationship
        """
        Relationship.

        :rtype: objetto.objects.Relationship
        """
        return cast("Relationship", super(Attribute, self).relationship)

    @property
    def delegated(self):
        # type: () -> bool
        """
        Whether attribute allows for delegates to be defined.

        :rtype: bool
        """
        return self.__delegated

    @property
    def dependencies(self):
        # type: () -> Tuple[Attribute, ...]
        """
        Attributes needed by the getter delegate.

        :rtype: tuple[objetto.objects.Attribute]
        """
        return self.__dependencies

    @property
    def deserialize_to(self):
        # type: () -> Optional[Attribute]
        """
        Non-serialized attribute to deserialize this into.

        :rtype: objetto.objects.Attribute or None
        """
        return self.__deserialize_to

    @property
    def fget(self):
        # type: () -> Optional[Callable]
        """
        Getter delegate.

        :rtype: function or None
        """
        return self.__fget

    @property
    def fset(self):
        # type: () -> Optional[Callable]
        """
        Setter delegate.

        :rtype: function or None
        """
        return self.__fset

    @property
    def fdel(self):
        # type: () -> Optional[Callable]
        """
        Deleter delegate.

        :rtype: function or None
        """
        return self.__fdel

    @property
    def constant(self):
        # type: () -> bool
        """
        Whether attribute is constant.

        :rtype: bool
        """
        return super(Attribute, self).constant and not self.delegated

    @property
    def batch_name(self):
        # type: () -> Optional[str]
        """
        Batch name.

        :rtype: str or None
        """
        return self.__batch_name

    @property
    def data_attribute(self):
        # type: () -> Optional[DataAttribute]
        """
        Data attribute.

        :rtype: objetto.data.DataAttribute or None
        """
        if self.__data_attribute is None:
            data_relationship = self.relationship.data_relationship
            if data_relationship is not None:
                self.__data_attribute = DataAttribute(
                    data_relationship,
                    default=MISSING,
                    default_factory=None,
                    module=self.module,
                    required=False,
                    changeable=True,
                    deletable=True,
                    finalized=False,
                    abstracted=False,
                    metadata=self.metadata,
                )
        return self.__data_attribute


@final
class Functions(BaseObjectFunctions):
    """Static functions for `Object`."""

    __slots__ = ()

    @staticmethod
    def replace_child_data(store, child, data_location, new_child_data):
        # type: (Store, BaseObject, Any, BaseData) -> Store
        """
        Replace child data.

        :param store: Object's store.
        :param child: Child getting their data replaced.
        :param data_location: Location of the existing child's data.
        :param new_child_data: New child's data.
        :return: Updated object's store.
        """
        original_data = store.data
        assert original_data is not None
        data = cast("Data", original_data)._set(data_location, new_child_data)
        return store.set("data", data)

    @staticmethod
    def get_initial(
        obj,  # type: Object
        input_values,  # type: Mapping[str, Any]
        factory=True,  # type: bool
    ):
        # type: (...) -> Mapping[str, Any]
        """
        Get initial values.

        :param obj: Object.
        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        :return: Initial values.
        """
        cls = type(obj)
        initial = {}
        kwargs = {"app": obj.app}

        for name, value in iteritems(input_values):
            try:
                attribute = cls._attributes[name]
            except KeyError:
                error = "'{}' has no attribute '{}'".format(cls.__fullname__, name)
                exc = AttributeError(error)
                raise_from(exc, None)
                raise exc
            initial[name] = attribute.relationship.fabricate_value(
                value, factory=factory, **kwargs
            )

        for name, attribute in iteritems(cls._attributes):
            if name not in initial:
                if attribute.has_default:
                    initial[name] = attribute.fabricate_default_value(**kwargs)

        return initial

    @staticmethod
    def check_missing(cls, state):
        # type: (Type[Object], DictState[str, Any]) -> None
        """
        Check for attributes with no values.

        :param cls: Object class.
        :param state: State.
        :raises TypeError: Raised when required attributes are missing.
        """
        missing_attributes = set(cls._attributes).difference(state)  # type: Set[str]
        optional_attributes = set(
            n for n, a in iteritems(cls._attributes) if not a.required
        )  # type: Set[str]
        if missing_attributes.difference(optional_attributes):
            error = "missing required attribute{} {}".format(
                "s" if len(missing_attributes) != 1 else "",
                ", ".join("'{}'".format(n) for n in missing_attributes),
            )
            raise TypeError(error)

    @staticmethod
    def update(obj, input_values, factory=True):
        # type: (Object, Mapping[str, Any], bool) -> None
        """
        Update object with values.

        :param obj: Object.
        :param input_values: Input values.
        :param factory: Whether to run values through factory.
        """
        cls = type(obj)
        with obj.app.__.write_context(obj) as (read, write):
            if not input_values:
                return

            # Set updates through intermediary object, sort by number of dependencies.
            intermediary_object = IntermediaryObject(obj.app, type(obj), read().state)
            sorted_input_values = sorted(
                iteritems(input_values),
                key=lambda i: len(cls._attribute_flattened_dependencies.get(i[0], ())),
            )
            for name, value in sorted_input_values:
                try:
                    attribute = cls._attributes[name]
                except KeyError:
                    error = "'{}' has no attribute '{}'".format(cls.__fullname__, name)
                    exc = AttributeError(error)
                    raise_from(exc, None)
                    raise exc
                else:
                    if value is DELETED:
                        intermediary_object.__.delete_value(name)
                    else:
                        if factory:
                            value = attribute.relationship.fabricate_value(
                                value, factory=True, **{"app": obj.app}
                            )
                    intermediary_object.__.set_value(name, value, factory=False)

            # Get results from changes.
            new_values, old_values = intermediary_object.__.get_results()

            # Process raw updates.
            Functions.raw_update(obj, new_values, old_values)

    @staticmethod
    def raw_update(
        obj,  # type: Object
        new_values,  # type: Mapping[str, Any]
        old_values,  # type: Mapping[str, Any]
        history=None,  # type: Optional[HistoryObject]
    ):
        # type: (...) -> None
        """
        Raw update (without going through intermediary object).

        :param obj: Object.
        :param new_values: New values.
        :param old_values: Old values.
        :param history: History than triggered this change during undo/redo.
        :raises AttributeError: Attribute is not changeable and already has a value.
        :raises AttributeError: Attribute is not deletable.
        """
        cls = type(obj)
        with obj.app.__.write_context(obj) as (read, write):

            # Get state, data, and locations cache.
            store = read()
            state = old_state = store.state  # type: DictState[str, Any]
            data = store.data  # type: Data
            metadata = store.metadata  # type: InteractiveDictData[str, Any]
            locations = metadata.get(
                "locations", DictState()
            )  # type: DictState[BaseObject, str]

            # Prepare change information.
            child_counter = ValueCounter()  # type: Counter[BaseObject]
            old_children = set()  # type: Set[BaseObject]
            new_children = set()  # type: Set[BaseObject]
            history_adopters = set()  # type: Set[BaseObject]

            # For every new value.
            for name, value in iteritems(new_values):

                # Get attribute and relationship.
                attribute = cls._attributes[name]
                relationship = attribute.relationship

                # Are we deleting it?
                delete_item = value is DELETED
                if delete_item and not attribute.deletable and not attribute.delegated:
                    error = "attribute '{}' is not deletable".format(name)
                    raise AttributeError(error)

                # Get old value.
                old_value = old_values[name]

                # Child relationship.
                if relationship.child:
                    same_app = not delete_item and obj._in_same_application(value)

                    # Update children counter, old/new children sets, and locations.
                    if old_value is not DELETED:
                        if not attribute.changeable and not attribute.delegated:
                            error = (
                                "non-changeable attribute '{}' already has a value"
                            ).format(name)
                            raise AttributeError(error)
                        if obj._in_same_application(old_value):
                            child_counter[old_value] -= 1
                            old_children.add(old_value)
                            locations = locations.remove(old_value)
                    if same_app:
                        child_counter[value] += 1
                        new_children.add(value)
                        locations = locations.set(value, name)

                    # Add history adopter.
                    if relationship.history and same_app:
                        history_adopters.add(value)

                    # Update data.
                    if relationship.data:
                        if delete_item:
                            data = data._delete(name)
                        else:
                            data_relationship = relationship.data_relationship
                            assert data_relationship is not None
                            if same_app:
                                with value.app.__.write_context(value) as (v_read, _):
                                    data = data._set(
                                        name,
                                        data_relationship.fabricate_value(
                                            v_read().data
                                        ),
                                    )
                            else:
                                data = data._set(
                                    name,
                                    data_relationship.fabricate_value(value),
                                )

                # Update state.
                if not delete_item:
                    state = state.set(name, value)
                else:
                    state = state.remove(name)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = Update(
                __redo__=Functions.redo_raw_update,
                __undo__=Functions.undo_raw_update,
                obj=obj,
                old_children=old_children,
                new_children=new_children,
                old_values=old_values,
                new_values=new_values,
                old_state=old_state,
                new_state=state,
                history_adopters=history_adopters,
                history=history,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_raw_update(change):
        # type: (Update) -> None
        """
        Raw update object state (REDO).

        :param change: Change.
        """
        Functions.raw_update(
            cast("Object", change.obj),
            change.new_values,
            change.old_values,
            history=change.obj._history,
        )

    @staticmethod
    def undo_raw_update(change):
        # type: (Update) -> None
        """
        Raw update object state (UNDO).

        :param change: Change.
        """
        Functions.raw_update(
            cast("Object", change.obj),
            change.old_values,
            change.new_values,
            history=change.obj._history,
        )


# Mark 'Functions' as a final member.
type.__setattr__(cast(type, Functions), FINAL_METHOD_TAG, True)


class ObjectMeta(BaseAttributeStructureMeta, BaseObjectMeta):
    """
    Metaclass for :class:`objetto.objects.Object`.

    Inherits from:
      - :class:`objetto.bases.BaseAttributeStructureMeta`
      - :class:`objetto.bases.BaseObjectMeta`

    Features:
      - Support for :class:`objetto.objects.Attribute` descriptors.
      - Compute and store attribute dependencies.
      - Constructs automatic `Data` class.

    :raises TypeError: Attribute is delegated but no delegates were defined.
    :raises TypeError: Attribute declares a dependency which is not available.
    """

    __data_type = WeakKeyDictionary({})  # type: MutableMapping[ObjectMeta, Type[Data]]
    __attribute_dependencies = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ObjectMeta, DictState]
    __attribute_dependents = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ObjectMeta, DictState]
    __attribute_flattened_dependencies = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ObjectMeta, DictState]
    __attribute_flattened_dependents = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[ObjectMeta, DictState]

    def __init__(cls, name, bases, dct):
        # type: (str, Tuple[Type, ...], Dict[str, Any]) -> None
        super(ObjectMeta, cls).__init__(name, bases, dct)

        # Check and gather attribute dependencies.
        dependencies = dict(
            (n, SetState()) for n in cls._attributes
        )  # type: Dict[str, SetState[str]]
        dependents = dict(
            (n, SetState()) for n in cls._attributes
        )  # type: Dict[str, SetState[str]]
        for attribute_name, attribute in iteritems(cls._attributes):

            # Delegated, but does not define any delegate.
            if attribute.delegated and attribute.fget is None:
                error = (
                    "attribute '{}.{}' is delegated but no delegates were defined"
                ).format(name, attribute_name)
                raise TypeError(error)

            # Dependencies.
            for dependency in attribute.dependencies:

                # Dependency is not in the same object.
                if dependency not in cls._attribute_names:
                    error = (
                        "attribute '{}.{}' declares an attribute as a dependency which "
                        "is not a valid attribute in the same object"
                    ).format(name, attribute_name)
                    raise TypeError(error)

                # Store dependencies.
                dependency_name = cls._attribute_names[dependency]
                dependencies[attribute_name] = dependencies.get(
                    attribute_name, SetState()
                ).add(dependency_name)
                dependents[dependency_name] = dependents.get(
                    dependency_name, SetState()
                ).add(attribute_name)

        def _resolve(nm, deps):
            return deps[nm].update(
                chain.from_iterable(_resolve(n, deps) for n in deps[nm])
            )

        def _flatten(deps):
            flattened = {}
            for nm in deps:
                flattened[nm] = _resolve(nm, deps)
            return flattened

        # Store dependencies and dependents.
        type(cls).__attribute_dependencies[cls] = DictState(dependencies)
        type(cls).__attribute_dependents[cls] = DictState(dependents)
        type(cls).__attribute_flattened_dependencies[cls] = DictState(
            _flatten(dependencies)
        )
        type(cls).__attribute_flattened_dependents[cls] = DictState(
            _flatten(dependents)
        )

    @property
    @final
    def _attribute_type(cls):
        # type: () -> Type[Attribute]
        """
        Attribute type.

        :rtype: type[objetto.objects.Attribute]
        """
        return Attribute

    @property
    @final
    def _attributes(cls):
        # type: () -> Mapping[str, Attribute]
        """
        Attributes mapped by name.

        :rtype: dict[str, objetto.objects.Attribute]
        """
        return cast("Mapping[str, Attribute]", super(ObjectMeta, cls)._attributes)

    @property
    @final
    def _attribute_names(cls):
        # type: () -> Mapping[Attribute, str]
        """
        Names mapped by attribute.

        :rtype: dict[objetto.objects.Attribute, str]
        """
        return cast("Mapping[Attribute, str]", super(ObjectMeta, cls)._attribute_names)

    @property
    @final
    def _state_factory(cls):
        # type: () -> Callable[..., DictState]
        """
        State factory.

        :rtype: type[objetto.states.DictState]
        """
        return DictState

    @property
    @final
    def _attribute_dependencies(cls):
        # type: () -> DictState[str, SetState[str]]
        """
        Attribute dependencies.

        :rtype: dict[str, set[str]]
        """
        return type(cls).__attribute_dependencies[cls]

    @property
    @final
    def _attribute_dependents(cls):
        # type: () -> DictState[str, SetState[str]]
        """
        Attribute dependents.

        :rtype: dict[str, set[str]]
        """
        return type(cls).__attribute_dependents[cls]

    @property
    @final
    def _attribute_flattened_dependencies(cls):
        # type: () -> DictState[str, SetState[str]]
        """
        Flattened attribute dependencies.

        :rtype: dict[str, set[str]]
        """
        return type(cls).__attribute_flattened_dependencies[cls]

    @property
    @final
    def _attribute_flattened_dependents(cls):
        # type: () -> DictState[str, SetState[str]]
        """
        Flattened attribute dependents.

        :rtype: dict[str, set[str]]
        """
        return type(cls).__attribute_flattened_dependents[cls]

    @property
    @final
    def Data(cls):
        # type: () -> Type[Data]
        """
        Data type.

        :rtype: type[objetto.data.Data]
        """

        # Try to get cached data type.
        mcs = type(cls)
        try:
            data_type = mcs.__data_type[cls]
        except KeyError:
            user_data_type = None
            user_data_type_owner = None
            for base in reversed(getmro(cls)):
                if "Data" in base.__dict__:
                    user_data_type = base.__dict__["Data"]
                    user_data_type_owner = base

            # User-defined data type.
            if user_data_type is not None:
                assert user_data_type_owner is not None
                with ReraiseContext(
                    TypeError,
                    "custom 'Data' class member defined in '{}'".format(
                        user_data_type_owner.__name__
                    ),
                ):
                    assert_is_subclass(user_data_type, Data)
                mcs.__data_type[cls] = data_type = user_data_type

            # Automatically defined data type.
            else:

                # Build data attributes.
                attributes = {}
                for attribute_name, attribute in iteritems(cls._attributes):
                    if attribute.relationship.data:
                        data_attribute = attribute.data_attribute
                        if data_attribute is None:
                            continue
                        attributes[attribute_name] = data_attribute

                # Prepare dct.
                dct = {}  # type: Dict[str, Any]
                dct.update(cls._data_methods)
                dct.update(attributes)
                if cls._unique_descriptor is not None:
                    assert cls._unique_descriptor_name is not None
                    dct[cls._unique_descriptor_name] = cls._unique_descriptor

                # Build data type and cache it.
                data_type = make_base_cls(
                    base=Data,
                    qual_name="{}.{}".format(cls.__fullname__, "Data"),
                    module=cls.__module__,
                    dct=dct,
                )
                mcs.__data_type[cls] = data_type

        return data_type


# noinspection PyTypeChecker
_O = TypeVar("_O", bound="Object")


class Object(
    with_metaclass(ObjectMeta, BaseMutableObject[str], BaseMutableAttributeStructure)
):
    """
    Object.

    Metaclass:
      - :class:`objetto.objects.ObjectMeta`

    Inherits from:
      - :class:`objetto.bases.BaseMutableObject`
      - :class:`objetto.bases.BaseMutableAttributeStructure`

    Inherited by:
      - :class:`objetto.history.HistoryObject`
      - :class:`objetto.history.BatchChanges`

    :param app: Application.
    :type app: objetto.applications.Application

    :param initial: Initial values.
    """

    __slots__ = ()
    __functions__ = Functions

    def __init__(self, app, **initial):
        # type: (Application, Any) -> None
        super(Object, self).__init__(app=app)
        cls = type(self)
        with self.app.write_context():
            self.__functions__.update(
                self,
                self.__functions__.get_initial(self, initial),
                factory=False,
            )
            self.__functions__.check_missing(cls, self._state)

    @classmethod
    @final
    def _get_relationship(cls, location):
        # type: (str) -> Relationship
        """
        Get relationship at location (attribute name).

        :param location: Location (attribute name).
        :type location: str

        :return: Relationship.
        :rtype: objetto.objects.Relationship

        :raises KeyError: Attribute does not exist.
        """
        return cast("Relationship", cls._get_attribute(location).relationship)

    @classmethod
    @final
    def _get_attribute(cls, name):
        # type: (str) -> Attribute
        """
        Get attribute by name.

        :param name: Attribute name.
        :type name: str

        :return: Attribute.
        :rtype: objetto.objects.Attribute

        :raises KeyError: Attribute does not exist.
        """
        return cast("Attribute", cls._attributes[name])

    @final
    def _clear(self):
        # type: (_O) -> _O
        """
        Clear deletable attribute values.

        :return: Transformed.
        :rtype: objetto.objects.Object

        :raises AttributeError: No deletable attributes.
        """
        with self.app.write_context():
            cls = type(self)
            update = {}
            for name in self._state:
                attribute = cls._get_attribute(name)
                if attribute.deletable:
                    update[name] = DELETED
            if not update:
                error = "'{}' has no deletable attributes".format(
                    type(self).__fullname__
                )
                raise AttributeError(error)
            self._update(update)
        return self

    @overload
    def _update(self, __m, **kwargs):
        # type: (_O, Mapping[str, Any], Any) -> _O
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (_O, Iterable[Tuple[str, Any]], Any) -> _O
        pass

    @overload
    def _update(self, **kwargs):
        # type: (_O, Any) -> _O
        pass

    @final
    def _update(self, *args, **kwargs):
        """
        Update multiple attribute values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        :rtype: objetto.objects.Object

        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        self.__functions__.update(self, dict(*args, **kwargs))
        return self

    @final
    def _set(self, name, value):
        # type: (_O, str, Any) -> _O
        """
        Set attribute value.

        :param name: Attribute name.
        :type name: str

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.objects.Object

        :raises AttributeError: Attribute is not changeable and already has a value.
        """
        attribute = self._get_attribute(name)
        batch_name = attribute.batch_name
        if batch_name is None:
            context = DummyContext()  # type: ignore
        else:
            context = self._batch_context(name=batch_name)  # type: ignore
        with context:
            self.__functions__.update(self, {name: value})
            return self

    @final
    def _delete(self, name):
        # type: (_O, str) -> _O
        """
        Delete attribute value.

        :param name: Attribute name.
        :type name: str

        :return: Transformed.
        :rtype: objetto.objects.Object

        :raises KeyError: Attribute does not exist or has no value.
        :raises AttributeError: Attribute is not deletable.
        """
        attribute = self._get_attribute(name)
        batch_name = attribute.batch_name
        if batch_name is None:
            context = DummyContext()  # type: ignore
        else:
            context = self._batch_context(name=batch_name)  # type: ignore
        with context:
            self.__functions__.update(self, {name: DELETED})
            return self

    @final
    def _locate(self, child):
        # type: (BaseObject) -> str
        """
        Locate child object.

        :param child: Child object.
        :type child: objetto.bases.BaseObject

        :return: Location.
        :rtype: str

        :raises ValueError: Could not locate child.
        """
        with self.app.__.read_context(self) as read:
            metadata = read().metadata
            try:
                return metadata["locations"][child]
            except KeyError:
                error = "could not locate child {} in {}".format(child, self)
                exc = ValueError(error)
                raise_from(exc, None)
                raise exc

    @final
    def _locate_data(self, child):
        # type: (BaseObject) -> str
        """
        Locate child object's data.

        :param child: Child object.
        :type child: objetto.bases.BaseObject

        :return: Data location.
        :rtype: str

        :raises ValueError: Could not locate child's data.
        """
        return self._locate(child)

    @classmethod
    @final
    def deserialize(cls, serialized, app=None, **kwargs):
        # type: (Type[_O], Dict[str, Any], Application, Any) -> _O
        """
        Deserialize.

        :param serialized: Serialized.
        :type serialized: dict[str, Any]

        :param app: Application (required).
        :type app: objetto.applications.Application

        :param kwargs: Keyword arguments to be passed to the deserializers.

        :return: Deserialized.
        :rtype: objetto.objects.Object

        :raises ValueError: Missing required 'app' attribute.
        """
        if app is None:
            error = (
                "missing required 'app' keyword argument for '{}.deserialize()' method"
            ).format(cls.__fullname__)
            raise ValueError(error)
        kwargs["app"] = app

        with app.write_context():
            self = cast("_O", cls.__new__(cls))
            with init_context(self):
                super(Object, self).__init__(app)

                initial = {}  # type: Dict[str, Any]
                for name, value in iteritems(serialized):
                    try:
                        attribute = cls._attributes[name]
                    except KeyError:
                        error = "'{}.deserialize'; '{}' has no attribute '{}'".format(
                            cls.__fullname__,
                            cls.__fullname__,
                            name,
                        )
                        exc = AttributeError(error)
                        raise_from(exc, None)
                        raise exc

                    if attribute.deserialize_to is not None:
                        deserialize_to_name = cls._attribute_names[
                            attribute.deserialize_to
                        ]
                    else:
                        deserialize_to_name = name

                    initial[deserialize_to_name] = cls.deserialize_value(
                        value, name, **kwargs
                    )

                self.__functions__.update(
                    self,
                    self.__functions__.get_initial(self, initial),
                    factory=False,
                )
                Functions.check_missing(cls, self._state)
            self.__post_deserialize__()
            return self

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> Dict[str, Any]
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.

        :return: Serialized.
        :rtype: dict[str, Any]
        """
        with self.app.read_context():
            return dict(
                (k, self.serialize_value(v, k, **kwargs))
                for k, v in iteritems(self._state)
                if type(self)._get_relationship(k).serialized
            )

    @property
    @final
    def _state(self):
        # type: () -> DictState[str, Any]
        """
        State.

        :rtype: objetto.states.DictState[str, Any]
        """
        return cast("DictState", super(Object, self)._state)

    @property
    @final
    def data(self):
        # type: () -> Data
        """
        Data.

        :rtype: objetto.data.Data
        """
        return cast("Data", super(Object, self).data)


@final
class IntermediaryObjectInternals(Base):
    """
    Internals for `IntermediaryObject`.

    :param iobj: Internal object.
    :param app: Application.
    :param cls: Object class.
    :param state: Object state.
    """

    __slots__ = (
        "__iobj_ref",
        "__app",
        "__cls",
        "__state",
        "__dependencies",
        "__in_getter",
        "__new_values",
        "__old_values",
        "__dirty",
    )

    def __init__(
        self,
        iobj,  # type: IntermediaryObject
        app,  # type: Application
        cls,  # type: Type[Object]
        state,  # type: DictState[str, Any]
    ):
        # type: (...) -> None
        self.__iobj_ref = WeakReference(iobj)
        self.__app = app
        self.__cls = cls
        self.__state = state
        self.__dependencies = None  # type: Optional[Tuple[Attribute, ...]]
        self.__in_getter = None  # type: Optional[Attribute]
        self.__new_values = {}  # type: Dict[str, Any]
        self.__old_values = {}  # type: Dict[str, Any]
        self.__dirty = set(cls._attributes).difference(state)  # type: Set[str]

    def get_value(self, name):
        """
        Get current value for attribute.

        :param name: Attribute name.
        :return: Value.
        :raises NameError: Can't access attribute not declared as dependency.
        :raises AttributeError: Attribute has no value.
        """
        attribute = self.__get_attribute(name)
        if self.__dependencies is not None and attribute not in self.__dependencies:
            error = (
                "can't access '{}' attribute from '{}' getter delegate since it was "
                "not declared as a dependency"
            ).format(name, self.__cls._attribute_names[self.__in_getter])
            raise NameError(error)

        if name in self.__dirty:
            value = MISSING
        else:
            try:
                value = self.__new_values[name]
            except KeyError:
                try:
                    value = self.__state[name]
                except KeyError:
                    value = MISSING

        if value in (MISSING, DELETED):
            if attribute.delegated:
                with self.__getter_context(attribute):
                    value = attribute.fget(self.iobj)
                value = attribute.relationship.fabricate_value(
                    value, factory=True, **{"app": self.app}
                )
                self.__set_new_value(name, value)
                return value
            else:
                error = "attribute '{}' has no value".format(name)
                raise AttributeError(error)
        else:
            return value

    def set_value(self, name, value, factory=True):
        # type: (str, Any, bool) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        :param factory: Whether to run value through factory.
        :raises AttributeError: Can't set attributes while running getter delegate.
        :raises AttributeError: Attribute is read-only.
        :raises AttributeError: Attribute already has a value and can't be changed.
        :raises AttributeError: Can't delete attributes while running getter delegate.
        :raises AttributeError: Attribute is not deletable.
        """

        if value is DELETED:
            self.delete_value(name)
            return

        if self.__in_getter is not None:
            error = "can't set attributes while running getter delegate"
            raise AttributeError(error)

        attribute = self.__get_attribute(name)
        if not attribute.changeable:
            if attribute.delegated:
                error = "attribute '{}' is read-only".format(name)
                raise AttributeError(error)
            try:
                self.get_value(name)
            except AttributeError:
                pass
            else:
                error = (
                    "attribute '{}' already has a value and can't be changed"
                ).format(name)
                raise AttributeError(error)

        if factory:
            value = attribute.relationship.fabricate_value(
                value, factory=True, **{"app": self.app}
            )
        if attribute.delegated:
            attribute.fset(self.iobj, value)
        else:
            self.__set_new_value(name, value)

    def delete_value(self, name):
        """
        Delete attribute.

        :param name: Attribute name.
        :raises AttributeError: Can't delete attributes while running getter delegate.
        :raises AttributeError: Attribute is not deletable.
        """

        if self.__in_getter is not None:
            error = "can't delete attributes while running getter delegate"
            raise AttributeError(error)

        attribute = self.__get_attribute(name)
        if not attribute.deletable:
            error = "attribute '{}' is not deletable".format(name)
            raise AttributeError(error)

        if attribute.delegated:
            attribute.fdel(self.iobj)
        else:
            self.get_value(name)  # will error if has no value, which we want
            self.__set_new_value(name, DELETED)

    @contextmanager
    def __getter_context(self, attribute):
        # type: (Attribute) -> Iterator
        """
        Getter context.

        :param attribute: Attribute.
        :return: Getter context manager.
        """
        before = self.__in_getter
        before_dependencies = self.__dependencies

        self.__in_getter = attribute
        if attribute.delegated:
            self.__dependencies = attribute.dependencies
        else:
            self.__dependencies = None

        try:
            yield
        finally:
            self.__in_getter = before
            self.__dependencies = before_dependencies

    def __set_new_value(self, name, value):
        # type: (str, Any) -> None
        """
        Set new attribute value.

        :param name: Attribute name.
        :param value: Value.
        """
        try:
            old_value = self.__state[name]
        except KeyError:
            old_value = DELETED

        if value is not old_value:
            self.__old_values[name] = old_value
            self.__new_values[name] = value
        else:
            self.__old_values.pop(name, None)
            self.__new_values.pop(name, None)

        self.__dirty.discard(name)
        for dependent in self.__cls._attribute_flattened_dependents[name]:
            self.__dirty.add(dependent)
            try:
                old_value = self.__state[dependent]
            except KeyError:
                self.__new_values.pop(dependent, None)
                self.__old_values.pop(dependent, None)
            else:
                self.__old_values[dependent] = old_value
                self.__new_values[dependent] = DELETED

    def __get_attribute(self, name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param name: Attribute name.
        :return: Value.
        :raises AttributeError: Has no such attribute.
        """
        try:
            return self.cls._attributes[name]
        except KeyError:
            pass
        error = "'{}' has no attribute '{}'".format(self.cls.__fullname__, name)
        raise AttributeError(error)

    def get_results(self):
        # type: () -> Tuple[Mapping[str, Any], Mapping[str, Any]]
        """
        Get results.

        :return: New values, old values.
        """
        sorted_dirty = sorted(
            self.__dirty,
            key=lambda n: len(self.__cls._attribute_flattened_dependencies[n]),
        )
        failed = set()
        success = set()
        for name in sorted_dirty:
            try:
                self.get_value(name)
            except AttributeError:
                failed.add(name)
            else:
                success.add(name)

        new_values = self.__new_values.copy()
        old_values = self.__old_values.copy()

        return new_values, old_values

    @property
    def iobj(self):
        # type: () -> Optional[IntermediaryObject]
        """Intermediary object."""
        return self.__iobj_ref()

    @property
    def app(self):
        # type: () -> Application
        """Application."""
        return self.__app

    @property
    def cls(self):
        # type: () -> Type[Object]
        """Object class."""
        return self.__cls

    @property
    def state(self):
        # type: () -> DictState[str, Any]
        """Object state."""
        return self.__state

    @property
    def in_getter(self):
        # type: () -> Optional[Attribute]
        """Whether running in an attribute's getter delegate."""
        return self.__in_getter


@final
class IntermediaryObject(Base):
    """
    Intermediary object provided to delegates.

    :param app: Application.
    :param cls: Object class.
    :param state: Object state.
    """

    __slots__ = ("__weakref__", "__")

    def __init__(self, app, cls, state):
        # type: (Application, Type[Object], DictState[str, Any]) -> None
        object.__setattr__(
            self,
            "__",
            IntermediaryObjectInternals(self, app, cls, state),
        )

    def __dir__(self):
        # type: () -> List[str]
        """
        Get attribute names.

        :return: Attribute names.
        """
        if self.__.in_getter is not None:
            attribute = self.__.in_getter
            return sorted(
                n
                for n, a in iteritems(self.__.cls._attributes)
                if a is attribute or a in a.dependencies
            )
        return sorted(self.__.cls._attributes)

    def __getattr__(self, name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param name: Attribute name.
        :return: Value.
        """
        if name != "__" and name in self.__.cls._attributes:
            return self[name]
        else:
            return self.__getattribute__(name)

    def __setattr__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        """
        if name in self.__.cls._attributes:
            self[name] = value
        else:
            super(IntermediaryObject, self).__setattr__(name, value)

    def __delattr__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.

        :param name: Attribute name.
        """
        if name in self.__.cls._attributes:
            del self[name]
        else:
            super(IntermediaryObject, self).__delattr__(name)

    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get attribute value.

        :param name: Attribute name.
        :return: Value.
        """
        return self.__.get_value(name)

    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Value.
        """
        self.__.set_value(name, value)

    def __delitem__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.

        :param name: Attribute name.
        """
        self.__.delete_value(name)
