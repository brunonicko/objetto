# -*- coding: utf-8 -*-
"""Set objects and proxy."""

from collections import Counter as ValueCounter
from typing import TYPE_CHECKING, TypeVar, cast

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import with_metaclass

from .._applications import Application
from .._bases import FINAL_METHOD_TAG, BaseMutableSet, final, init_context
from .._changes import SetRemove, SetUpdate
from .._data import BaseData, InteractiveDictData, SetData
from .._states import DictState, SetState
from .._structures import (
    BaseMutableSetStructure,
    BaseSetStructure,
    BaseSetStructureMeta,
)
from .bases import (
    BaseAuxiliaryObject,
    BaseAuxiliaryObjectFunctions,
    BaseAuxiliaryObjectMeta,
    BaseMutableAuxiliaryObject,
    BaseObject,
    BaseProxyObject,
)

if TYPE_CHECKING:
    from typing import Any, Callable, Counter, Hashable, Iterable, List, Set, Type

    from .._applications import Store

__all__ = ["SetObject", "MutableSetObject", "ProxySetObject"]


T = TypeVar("T")  # Any type.


DATA_MAP_METADATA_KEY = "data_map"
"""Data child locations metadata key."""


@final
class SetObjectFunctions(BaseAuxiliaryObjectFunctions):
    """Static functions for :class:`SetObject`."""

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
        data = store.data._set(data_location, new_child_data)
        metadata = store.metadata.set(
            DATA_MAP_METADATA_KEY,
            store.metadata.get(
                DATA_MAP_METADATA_KEY,
                DictState(),
            ).set(child, new_child_data),
        )
        return store.update({"data": data, "metadata": metadata})

    @staticmethod
    def update(
        obj,  # type: SetObject
        input_values,  # type: Iterable[Hashable]
        factory=True,  # type: bool
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship
        with obj.app.__.write_context(obj) as (read, write):
            if not input_values:
                return

            # Get state, data, and data map.
            store = read()
            state = old_state = store.state  # type: SetState
            data = store.data  # type: SetData
            metadata = store.metadata  # type: InteractiveDictData
            data_map = metadata.get(
                DATA_MAP_METADATA_KEY, DictState()
            )  # type: DictState

            # Prepare change information.
            child_counter = ValueCounter()  # type: Counter[BaseObject]
            new_children = set()  # type: Set[BaseObject]
            history_adopters = set()  # type: Set[BaseObject]
            new_values = set()  # type: Set[Any]

            # For every input value.
            for value in set(input_values):

                # Fabricate new value.
                if factory:
                    value = relationship.fabricate_value(
                        value,
                        factory=factory,
                        kwargs={"app": obj.app},
                    )
                new_values.add(value)

                # Child relationship.
                if relationship.child:
                    same_app = obj._in_same_application(value)
                    child = cast("BaseObject", value) if same_app else None

                    # Update children counter and new children set.
                    if child is not None:
                        child_counter[child] += 1
                        new_children.add(child)

                        # Add history adopter.
                        if relationship.history and same_app:
                            history_adopters.add(child)

                    # Update data.
                    if relationship.data:
                        data_relationship = relationship.data_relationship
                        if child is not None:
                            if type(child)._unique_descriptor is None:
                                error = (
                                    "'{}' objects (which class doesn't define a "
                                    "unique descriptor) can't be added as a child of "
                                    "'{}' object (which is a set object and defines a "
                                    "data relationship)"
                                ).format(
                                    type(child).__fullname__,
                                    type(obj).__fullname__,
                                )
                                raise TypeError(error)

                            with child.app.__.write_context(value) as (v_read, _):
                                data_value = data_relationship.fabricate_value(
                                    v_read().data,
                                )
                        else:
                            data_value = data_relationship.fabricate_value(value)
                        data = data._add(data_value)
                        data_map = data_map.set(value, data_value)

                # Update state.
                state = state.add(value)

            # Store data_map in the metadata.
            metadata = metadata.set(DATA_MAP_METADATA_KEY, data_map)

            # Prepare change.
            change = SetUpdate(
                __redo__=SetObjectFunctions.redo_update,
                __undo__=SetObjectFunctions.undo_update,
                obj=obj,
                old_children=(),
                new_children=new_children,
                new_values=new_values,
                history_adopters=history_adopters,
                old_state=old_state,
                new_state=state,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_update(change):
        # type: (SetUpdate) -> None
        SetObjectFunctions.update(
            cast("SetObject", change.obj),
            change.new_values,
            factory=False,
        )

    @staticmethod
    def undo_update(change):
        # type: (SetUpdate) -> None
        SetObjectFunctions.remove(
            cast("SetObject", change.obj),
            change.new_values,
        )

    @staticmethod
    def remove(
        obj,  # type: SetObject
        input_values,  # type: Iterable[Hashable]
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship
        with obj.app.__.write_context(obj) as (read, write):
            if not input_values:
                return

            # Get state, data, and data map.
            store = read()
            state = old_state = store.state  # type: SetState
            data = store.data  # type: SetData
            metadata = store.metadata  # type: InteractiveDictData
            data_map = metadata.get(
                DATA_MAP_METADATA_KEY, DictState()
            )  # type: DictState

            # Prepare change information.
            child_counter = ValueCounter()  # type: Counter[BaseObject]
            old_children = set()  # type: Set[BaseObject]
            old_values = set()  # type: Set[Hashable]

            # For every input value.
            for value in set(input_values):

                # Check if value is in the set.
                if value not in store.state:
                    raise KeyError(value)
                old_values.add(value)

                # Child relationship.
                if relationship.child:
                    same_app = obj._in_same_application(value)
                    child = cast("BaseObject", value) if same_app else None

                    # Update children counter and new children set.
                    if child is not None:
                        child_counter[child] -= 1
                        old_children.add(child)

                    # Update data.
                    if relationship.data:
                        data = data._remove(data_map[value])
                        data_map = data_map.remove(value)

                # Update state.
                state = state.remove(value)

            # Store data_map in the metadata.
            metadata = metadata.set(DATA_MAP_METADATA_KEY, data_map)

            # Prepare change.
            change = SetRemove(
                __redo__=SetObjectFunctions.redo_remove,
                __undo__=SetObjectFunctions.undo_remove,
                obj=obj,
                old_children=old_children,
                new_children=(),
                old_values=old_values,
                history_adopters=(),
                old_state=old_state,
                new_state=state,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_remove(change):
        # type: (SetRemove) -> None
        SetObjectFunctions.remove(
            cast("SetObject", change.obj),
            change.old_values,
        )

    @staticmethod
    def undo_remove(change):
        # type: (SetRemove) -> None
        SetObjectFunctions.update(
            cast("SetObject", change.obj),
            change.old_values,
            factory=False,
        )


type.__setattr__(cast(type, SetObjectFunctions), FINAL_METHOD_TAG, True)


class SetObjectMeta(BaseAuxiliaryObjectMeta, BaseSetStructureMeta):
    """Metaclass for :class:`SetObject`."""

    @property
    @final
    def _state_factory(cls):
        # type: () -> Callable[..., SetState]
        """State factory."""
        return SetState

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[SetObject]
        """Base auxiliary object type."""
        return SetObject

    @property
    @final
    def _base_auxiliary_data_type(cls):
        # type: () -> Type[SetData]
        """Base auxiliary data type."""
        return SetData


# noinspection PyTypeChecker
_SO = TypeVar("_SO", bound="SetObject")


class SetObject(
    with_metaclass(
        SetObjectMeta,
        BaseAuxiliaryObject[T],
        BaseSetStructure[T],
    )
):
    """
    Set object.

    :param app: Application.
    :param initial: Initial values.
    """

    __slots__ = ()
    __functions__ = SetObjectFunctions

    @classmethod
    @final
    def _from_iterable(cls, iterable):
        # type: (Iterable) -> SetState
        """
        Make set state from iterable.

        :param iterable: Iterable.
        :return: Set data.
        """
        return SetState(iterable)

    def __init__(
        self,
        app,  # type: Application
        initial=(),  # type: Iterable[Hashable]
    ):
        # type: (...) -> None
        super(SetObject, self).__init__(app=app)
        self.__functions__.update(self, initial)

    @final
    def _clear(self):
        # type: (_SO) -> _SO
        """
        Clear all values.

        :return: Transformed.
        """
        self.__functions__.remove(self, self._state)
        return self

    @final
    def _add(self, value):
        # type: (_SO, T) -> _SO
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        self.__functions__.update(self, {value})
        return self

    @final
    def _discard(self, *values):
        # type: (_SO, T) -> _SO
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        with self.app.write_context():
            removes = self._state.intersection(values)
            if not removes:
                return self
            self._remove(*removes)
        return self

    @final
    def _remove(self, *values):
        # type: (_SO, T) -> _SO
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        self.__functions__.remove(self, values)
        return self

    @final
    def _replace(self, old_value, new_value):
        # type: (_SO, T, T) -> _SO
        """
        Replace existing value with a new one.

        :param old_value: Existing value.
        :param new_value: New value.
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        metadata = dict(old_value=old_value, new_value=new_value)
        with self._batch_context("Replace Value", **metadata):
            self._remove(old_value)
            self._add(new_value)
        return self

    @final
    def _update(self, iterable):
        # type: (_SO, Iterable[T]) -> _SO
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        self.__functions__.update(self, iterable)
        return self

    @final
    def _locate(self, child):
        # type: (BaseObject) -> int
        """
        Locate child object.

        :param child: Child object.
        :return: Location.
        :raises ValueError: Could not locate child.
        """
        with self.app.__.read_context(self) as read:
            if child not in read().children:
                error = "could not locate child {} in {}".format(child, self)
                raise ValueError(error)
            return child

    @final
    def _locate_data(self, child):
        # type: (BaseObject) -> int
        """
        Locate child object's data.

        :param child: Child object.
        :return: Data location.
        :raises ValueError: Could not locate child's data.
        """
        with self.app.__.read_context(self) as read:
            if child not in read().children:
                error = "could not locate child {} in {}".format(child, self)
                raise ValueError(error)
            metadata = read().metadata
            try:
                return metadata[DATA_MAP_METADATA_KEY][child]
            except KeyError:
                pass
            error = "could not locate data of child {} in {}".format(child, self)
            raise ValueError(error)

    @classmethod
    @final
    def deserialize(cls, serialized, app=None, **kwargs):
        # type: (Type[_SO], List[Any], Application, Any) -> _SO
        """
        Deserialize.

        :param serialized: Serialized.
        :param app: Application (required).
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized.
        """
        if app is None:
            error = (
                "missing required 'app' keyword argument for '{}.deserialize()' method"
            ).format(cls.__fullname__)
            raise ValueError(error)
        kwargs["app"] = app

        with app.write_context():
            self = cast("SetObject", cls.__new__(cls))
            with init_context(self):
                super(SetObject, self).__init__(app)
                initial = set(
                    cls.deserialize_value(v, None, **kwargs)
                    for v in serialized
                    if cls._relationship.serialized
                )
                self.__functions__.update(self, initial)
            return self

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> List[Hashable]
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized.
        """
        with self.app.read_context():
            return list(
                self.serialize_value(v, None, **kwargs)
                for v in self._state
                if type(self)._relationship.serialized
            )

    @property
    @final
    def _state(self):
        # type: () -> SetState[T]
        """State."""
        return cast("SetState[T]", super(BaseSetStructure, self)._state)

    @property
    @final
    def data(self):
        # type: () -> SetData[T]
        """Data."""
        return cast("SetData[T]", super(BaseSetStructure, self).data)


# noinspection PyAbstractClass
class MutableSetObject(
    SetObject[T], BaseMutableAuxiliaryObject[T], BaseMutableSetStructure[T]
):
    """Mutable set object."""

    __slots__ = ()

    @final
    def pop(self):
        # type: () -> T
        """
        Pop value.

        :return: Value.
        :raises KeyError: Empty set.
        """
        with self.app.write_context():
            state = self._state
            if not state:
                error = "empty set"
                raise KeyError(error)
            value = next(iter(state))
            self._remove(value)
        return value

    @final
    def intersection_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Intersect.

        :param iterable: Iterable.
        """
        with self.app.write_context():
            difference = self.difference(iterable)
            if difference:
                self._remove(*difference)

    @final
    def symmetric_difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Symmetric difference.

        :param iterable: Iterable.
        """
        with self.app.write_context():
            inverse_difference = self.inverse_difference(iterable)
            intersection = self.intersection(iterable)
            self._update(inverse_difference)
            self._remove(*intersection)

    @final
    def difference_update(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Difference.

        :param iterable: Iterable.
        """
        with self.app.write_context():
            intersection = self.intersection(iterable)
            if intersection:
                self._remove(*intersection)


# noinspection PyTypeChecker
_PSO = TypeVar("_PSO", bound="ProxySetObject")


@final
class ProxySetObject(BaseProxyObject[T], BaseMutableSet[T]):
    """Mutable proxy set."""

    __slots__ = ()

    pop = MutableSetObject.pop
    intersection_update = MutableSetObject.intersection_update
    symmetric_difference_update = MutableSetObject.symmetric_difference_update
    difference_update = MutableSetObject.difference_update

    @classmethod
    def _from_iterable(cls, iterable):
        # type: (Iterable) -> SetState
        """
        Make set state from iterable.

        :param iterable: Iterable.
        :return: Set data.
        """
        return SetState(iterable)

    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return self._obj._hash()

    def _add(self, value):
        # type: (_PSO, T) -> _PSO
        """
        Add value.

        :param value: Value.
        :return: Transformed.
        """
        self._obj._add(value)
        return self

    def _discard(self, *values):
        # type: (_PSO, T) -> _PSO
        """
        Discard value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        self._obj._discard(*values)
        return self

    def _remove(self, *values):
        # type: (_PSO, T) -> _PSO
        """
        Remove existing value(s).

        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        :raises KeyError: Value is not present.
        """
        self._obj._remove(*values)
        return self

    def _replace(self, old_value, new_value):
        # type: (_PSO, T, T) -> _PSO
        """
        Replace existing value with a new one.

        :param old_value: Existing value.
        :param new_value: New value.
        :return: Transformed.
        :raises KeyError: Value is not present.
        """
        self._obj._replace(old_value, new_value)
        return self

    def _update(self, iterable):
        # type: (_PSO, Iterable[T]) -> _PSO
        """
        Update with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        self._obj._update(iterable)
        return self

    def isdisjoint(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a disjoint set of an iterable.

        :param iterable: Iterable.
        :return: True if is disjoint.
        """
        return self._obj.isdisjoint(iterable)

    def issubset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a subset of an iterable.

        :param iterable: Iterable.
        :return: True if is subset.
        """
        return self._obj.issubset(iterable)

    def issuperset(self, iterable):
        # type: (Iterable) -> bool
        """
        Get whether is a superset of an iterable.

        :param iterable: Iterable.
        :return: True if is superset.
        """
        return self._obj.issuperset(iterable)

    def intersection(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get intersection.

        :param iterable: Iterable.
        :return: Intersection.
        """
        return self._obj.intersection(iterable)

    def difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get difference.

        :param iterable: Iterable.
        :return: Difference.
        """
        return self._obj.difference(iterable)

    def inverse_difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get an iterable's difference to this.

        :param iterable: Iterable.
        :return: Inverse Difference.
        """
        return self._obj.inverse_difference(iterable)

    def symmetric_difference(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get symmetric difference.

        :param iterable: Iterable.
        :return: Symmetric difference.
        """
        return self._obj.symmetric_difference(iterable)

    def union(self, iterable):
        # type: (Iterable) -> SetState
        """
        Get union.

        :param iterable: Iterable.
        :return: Union.
        """
        return self._obj.union(iterable)
