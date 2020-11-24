# -*- coding: utf-8 -*-
"""Set objects and proxy."""

from abc import abstractmethod
from collections import Counter as ValueCounter
from typing import TYPE_CHECKING, TypeVar, cast

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import with_metaclass

from .bases import (
    BaseObject,
    BaseAuxiliaryObjectFunctions,
    BaseAuxiliaryObjectMeta,
    BaseAuxiliaryObject,
)
from .._application import Application
from .._bases import FINAL_METHOD_TAG, final, init_context
from .._changes import SetUpdate, SetRemove
from .._data import BaseData, InteractiveDictData, SetData
from .._states import DictState, SetState
from .._structures import BaseSetStructureMeta, BaseSetStructure

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Counter,
        Iterable,
        Hashable,
        List,
        Set,
        Type,
    )

    from .._application import Store

__all__ = ["SetObject"]


T = TypeVar("T")  # Any type.


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
            "data_map",
            store.metadata.get("data_map", DictState()).set(child, new_child_data),
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
            data_map = metadata.get("data_map", DictState())  # type: DictState

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
            metadata = metadata.set("data_map", data_map)

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
            data_map = metadata.get("data_map", DictState())  # type: DictState

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
            metadata = metadata.set("data_map", data_map)

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
    Setionary object.

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

    @abstractmethod
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
