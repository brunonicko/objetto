# -*- coding: utf-8 -*-
"""List objects and proxy."""

from collections import Counter as ValueCounter
from typing import TYPE_CHECKING, TypeVar, cast, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import raise_from, with_metaclass

from .._applications import Application
from .._bases import FINAL_METHOD_TAG, BaseMutableList, final, init_context
from .._changes import ListDelete, ListInsert, ListMove, ListUpdate
from .._data import BaseData, InteractiveDictData, ListData
from .._states import ListState
from .._structures import (
    BaseListStructure,
    BaseListStructureMeta,
    BaseMutableListStructure,
)
from ..utils.list_operations import pre_move, resolve_continuous_slice, resolve_index
from .bases import (
    BaseAuxiliaryObject,
    BaseAuxiliaryObjectFunctions,
    BaseAuxiliaryObjectMeta,
    BaseMutableAuxiliaryObject,
    BaseObject,
    BaseProxyObject,
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
        Optional,
        Set,
        Tuple,
        Type,
        Union,
    )

    from .._applications import Store

__all__ = ["ListObject", "MutableListObject", "ProxyListObject"]


T = TypeVar("T")  # Any type.


@final
class ListObjectFunctions(BaseAuxiliaryObjectFunctions):
    """Static functions for :class:`ListObject`."""

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
        return store.set("data", data)

    @staticmethod
    def insert(
        obj,  # type: ListObject
        index,  # type: int
        input_values,  # type: Iterable[Any]
        factory=True,  # type: bool
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship
        with obj.app.__.write_context(obj) as (read, write):
            if not input_values:
                return

            # Get state, data, and a brand new locations cache.
            store = read()
            state = old_state = store.state  # type: ListState
            data = store.data  # type: ListData
            metadata = store.metadata  # type: InteractiveDictData
            locations = {}  # type: Dict[BaseObject, int]

            # Get resolved index.
            index = resolve_index(len(state), index, clamp=True)

            # Prepare change information.
            child_counter = ValueCounter()  # type: Counter[BaseObject]
            new_children = set()  # type: Set[BaseObject]
            history_adopters = set()  # type: Set[BaseObject]
            new_values = []  # type: List[Any]
            new_data_values = []  # type: List[Any]

            # For every input value.
            for i, value in enumerate(input_values):

                # Fabricate new value.
                if factory:
                    value = relationship.fabricate_value(
                        value, factory=factory, **{"app": obj.app}
                    )
                new_values.append(value)

                # Child relationship.
                if relationship.child:
                    same_app = obj._in_same_application(value)

                    # Update children counter and new children set.
                    if same_app:
                        child_counter[value] += 1
                        new_children.add(value)
                        locations[value] = index + i

                    # Add history adopter.
                    if relationship.history and same_app:
                        history_adopters.add(value)

                    # Update data.
                    if relationship.data:
                        data_relationship = relationship.data_relationship
                        if same_app:
                            with value.app.__.write_context(value) as (v_read, _):
                                data_value = data_relationship.fabricate_value(
                                    v_read().data,
                                )
                        else:
                            data_value = data_relationship.fabricate_value(value)
                        new_data_values.append(data_value)

            # Update state and data.
            state = state.insert(index, *new_values)
            if relationship.data:
                data = data._insert(index, *new_data_values)

            # Get last index and stop.
            stop = index + len(new_values)
            last_index = stop - 1

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = ListInsert(
                __redo__=ListObjectFunctions.redo_insert,
                __undo__=ListObjectFunctions.undo_insert,
                obj=obj,
                old_children=(),
                new_children=new_children,
                index=index,
                last_index=last_index,
                stop=stop,
                new_values=new_values,
                old_state=old_state,
                new_state=state,
                history_adopters=history_adopters,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_insert(change):
        # type: (ListInsert) -> None
        ListObjectFunctions.insert(
            cast("ListObject", change.obj),
            change.index,
            change.new_values,
            factory=False,
        )

    @staticmethod
    def undo_insert(change):
        # type: (ListInsert) -> None
        ListObjectFunctions.delete(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
        )

    @staticmethod
    def delete(
        obj,  # type: ListObject
        item,  # type: Union[int, slice]
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship
        with obj.app.__.write_context(obj) as (read, write):

            # Get state, data, and a brand new locations cache.
            store = read()
            state = old_state = store.state  # type: ListState
            data = store.data  # type: ListData
            metadata = store.metadata  # type: InteractiveDictData
            locations = {}  # type: Dict[BaseObject, int]

            # Get resolved indexes and stop.
            if isinstance(item, slice):
                index, stop = resolve_continuous_slice(len(state), item)
                if stop == index:
                    return
            else:
                index = resolve_index(len(state), item)
                stop = index + 1
            last_index = stop - 1
            slc = slice(index, stop)

            # Prepare change information.
            child_counter = ValueCounter()  # type: Counter[BaseObject]
            old_children = set()  # type: Set[BaseObject]
            old_values = state[index : last_index + 1]  # type: ListState

            # For every value being removed.
            for value in old_values:

                # Child relationship.
                if relationship.child:
                    same_app = obj._in_same_application(value)

                    # Update children counter and new children set.
                    if same_app:
                        child_counter[value] -= 1
                        old_children.add(value)

            # Update state and data.
            state = state.delete_slice(slc)
            if relationship.data:
                data = data._delete_slice(slc)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = ListDelete(
                __redo__=ListObjectFunctions.redo_delete,
                __undo__=ListObjectFunctions.undo_delete,
                obj=obj,
                old_children=old_children,
                new_children=(),
                index=index,
                last_index=last_index,
                stop=stop,
                old_values=old_values,
                old_state=old_state,
                new_state=state,
                history_adopters=(),
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_delete(change):
        # type: (ListDelete) -> None
        ListObjectFunctions.delete(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
        )

    @staticmethod
    def undo_delete(change):
        # type: (ListDelete) -> None
        ListObjectFunctions.insert(
            cast("ListObject", change.obj),
            change.index,
            change.old_values,
            factory=False,
        )

    @staticmethod
    def update(
        obj,  # type: ListObject
        item,  # type: Union[int, slice]
        input_values,  # type: Iterable[Any]
        factory=True,  # type: bool
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship
        with obj.app.__.write_context(obj) as (read, write):

            # Get state, data, and a brand new locations cache.
            store = read()
            state = old_state = store.state  # type: ListState
            data = store.data  # type: ListData
            metadata = store.metadata  # type: InteractiveDictData
            locations = {}  # type: Dict[BaseObject, int]

            # Get old values and check length.
            if isinstance(item, slice):
                index, stop = resolve_continuous_slice(len(state), item)
            else:
                index = resolve_index(len(state), item)
                stop = index + 1
            slc = slice(index, stop)
            last_index = stop - 1
            input_values = list(input_values)
            old_values = state[slc]
            if len(old_values) != len(input_values):
                error = "length of slice and values mismatch"
                raise IndexError(error)
            if len(old_values) == 0:
                return

            # Prepare change information.
            child_counter = ValueCounter()  # type: Counter[BaseObject]
            history_adopters = set()
            old_children = set()
            new_children = set()
            new_values = []
            new_data_values = []

            # For every value being removed.
            for value, old_value in zip(input_values, old_values):

                # Fabricate new value.
                if factory:
                    value = relationship.fabricate_value(
                        value, factory=factory, **{"app": obj.app}
                    )
                new_values.append(value)

                # No change.
                if value is old_value:
                    continue

                # Child relationship.
                if relationship.child:
                    same_app = obj._in_same_application(value)

                    # Update children counter, old/new children sets.
                    if obj._in_same_application(old_value):
                        child_counter[old_value] -= 1
                        old_children.add(old_value)
                    if same_app:
                        child_counter[value] += 1
                        new_children.add(value)

                    # Add history adopter.
                    if relationship.history and same_app:
                        history_adopters.add(value)

                    # Update data.
                    if relationship.data:
                        data_relationship = relationship.data_relationship
                        if same_app:
                            with value.app.__.write_context(value) as (v_read, _):
                                data_value = data_relationship.fabricate_value(
                                    v_read().data,
                                )
                        else:
                            data_value = data_relationship.fabricate_value(value)
                        new_data_values.append(data_value)

            # Update state and data.
            state = state.set_slice(slc, new_values)
            if relationship.data:
                data = data._set_slice(slc, new_data_values)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = ListUpdate(
                __redo__=ListObjectFunctions.redo_update,
                __undo__=ListObjectFunctions.undo_update,
                obj=obj,
                old_children=old_children,
                new_children=new_children,
                history_adopters=history_adopters,
                index=index,
                last_index=last_index,
                stop=stop,
                old_values=old_values,
                new_values=new_values,
                old_state=old_state,
                new_state=state,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_update(change):
        # type: (ListUpdate) -> None
        ListObjectFunctions.update(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
            change.new_values,
            factory=False,
        )

    @staticmethod
    def undo_update(change):
        # type: (ListUpdate) -> None
        ListObjectFunctions.update(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
            change.old_values,
            factory=False,
        )

    @staticmethod
    def move(
        obj,  # type: ListObject
        item,  # type: Union[int, slice]
        target_index,  # type: int
    ):
        # type: (...) -> None
        with obj.app.__.write_context(obj) as (read, write):

            # Get state, data, and a brand new locations cache.
            store = read()
            state = old_state = store.state  # type: ListState
            data = store.data  # type: ListData
            metadata = store.metadata  # type: InteractiveDictData
            locations = {}  # type: Dict[BaseObject, int]

            # Get resolved indexes and stop.
            pre_move_result = pre_move(len(state), item, target_index)
            if pre_move_result is None:
                return
            index, stop, target_index, post_index = pre_move_result
            post_stop = post_index + (stop - index)
            last_index = stop - 1
            post_last_index = post_stop - 1

            # Prepare change information.
            values = state[index : last_index + 1]

            # Update state and data.
            state = state.move(item, target_index)
            data = data._move(item, target_index)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = ListMove(
                __redo__=ListObjectFunctions.redo_move,
                __undo__=ListObjectFunctions.undo_move,
                obj=obj,
                old_children=(),
                new_children=(),
                history_adopters=(),
                index=index,
                last_index=last_index,
                stop=stop,
                target_index=target_index,
                post_index=post_index,
                post_last_index=post_last_index,
                post_stop=post_stop,
                values=values,
                old_state=old_state,
                new_state=state,
            )
            write(state, data, metadata, ValueCounter(), change)

    @staticmethod
    def redo_move(change):
        # type: (ListMove) -> None
        ListObjectFunctions.move(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
            change.target_index,
        )

    @staticmethod
    def undo_move(change):
        # type: (ListMove) -> None
        ListObjectFunctions.move(
            cast("ListObject", change.obj),
            slice(change.post_index, change.post_stop),
            change.index,
        )


type.__setattr__(cast(type, ListObjectFunctions), FINAL_METHOD_TAG, True)


class ListObjectMeta(BaseAuxiliaryObjectMeta, BaseListStructureMeta):
    """Metaclass for :class:`ListObject`."""

    @property
    @final
    def _state_factory(cls):
        # type: () -> Callable[..., ListState]
        """State factory."""
        return ListState

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[ListObject]
        """Base auxiliary object type."""
        return ListObject

    @property
    @final
    def _base_auxiliary_data_type(cls):
        # type: () -> Type[ListData]
        """Base auxiliary data type."""
        return ListData


# noinspection PyTypeChecker
_LO = TypeVar("_LO", bound="ListObject")


class ListObject(
    with_metaclass(
        ListObjectMeta,
        BaseAuxiliaryObject[T],
        BaseListStructure[T],
    )
):
    """
    List object.

    :param app: Application.
    :param initial: Initial values.
    """

    __slots__ = ()
    __functions__ = ListObjectFunctions

    def __init__(self, app, initial=()):
        # type: (Application, Iterable[T]) -> None
        super(ListObject, self).__init__(app=app)
        self.__functions__.insert(self, 0, initial)

    @final
    def _clear(self):
        # type: (_LO) -> _LO
        """
        Clear all values.

        :return: Transformed.
        """
        with self.app.write_context():
            state_length = len(self._state)
            if state_length:
                self._delete(slice(0, state_length))
        return self

    @final
    def _insert(self, index, *values):
        # type: (_LO, int, T) -> _LO
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        if not values:
            error = "no values provided"
            raise ValueError(error)
        self.__functions__.insert(self, index, values)
        return self

    @final
    def _append(self, value):
        # type: (_LO, T) -> _LO
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        self.__functions__.insert(self, len(self._state), (value,))
        return self

    @final
    def _extend(self, iterable):
        # type: (_LO, Iterable[T]) -> _LO
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        self.__functions__.insert(self, len(self._state), iterable)
        return self

    @final
    def _remove(self, value):
        # type: (_LO, T) -> _LO
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        with self.app.write_context():
            index = self.index(value)
            self.__functions__.delete(self, index)
            return self

    @final
    def _reverse(self):
        # type: (_LO) -> _LO
        """
        Reverse values.

        :return: Transformed.
        """
        with self.app.write_context():
            if self._state:
                reversed_values = self._state.reverse()
                self.__functions__.update(
                    self, slice(0, len(self._state)), reversed_values
                )
        return self

    @final
    def _move(self, item, target_index):
        # type: (_LO, Union[slice, int], int) -> _LO
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        self.__functions__.move(self, item, target_index)
        return self

    @final
    def _delete(self, item):
        # type: (_LO, Union[slice, int]) -> _LO
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        self.__functions__.delete(self, item)
        return self

    @final
    def _update(self, index, *values):
        # type: (_LO, int, T) -> _LO
        """
        Update value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        if not input_values:
            error = "no values provided"
            raise ValueError(error)
        self.__functions__.update(self, index, values)
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
            metadata = read().metadata
            try:
                return metadata["locations"][child]
            except KeyError:
                if child in self._children:
                    location = metadata["locations"][child] = self.index(child)
                    return location
                error = "could not locate child {} in {}".format(child, self)
                exc = ValueError(error)
                raise_from(exc, None)
                raise exc

    @final
    def _locate_data(self, child):
        # type: (BaseObject) -> int
        """
        Locate child object's data.

        :param child: Child object.
        :return: Data location.
        :raises ValueError: Could not locate child's data.
        """
        return self._locate(child)

    @classmethod
    @final
    def deserialize(cls, serialized, app=None, **kwargs):
        # type: (Type[_LO], Dict[str, Any], Application, Any) -> _LO
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
            self = cast("ListObject", cls.__new__(cls))
            with init_context(self):
                super(ListObject, self).__init__(app)
                initial = (
                    cls.deserialize_value(v, None, **kwargs)
                    for v in serialized
                    if cls._relationship.serialized
                )
                self.__functions__.insert(self, 0, initial)
            return self

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> List
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
        # type: () -> ListState[T]
        """State."""
        return cast("ListState[T]", super(BaseListStructure, self)._state)

    @property
    @final
    def data(self):
        # type: () -> ListData[T]
        """Data."""
        return cast("ListData[T]", super(BaseListStructure, self).data)


# noinspection PyAbstractClass
class MutableListObject(
    ListObject[T], BaseMutableAuxiliaryObject[T], BaseMutableListStructure[T]
):
    """Mutable dictionary object."""

    __slots__ = ()

    @overload
    def __setitem__(self, index, value):
        # type: (int, T) -> None
        pass

    @overload
    def __setitem__(self, slc, values):
        # type: (slice, Iterable[T]) -> None
        pass

    @final
    def __setitem__(self, item, value):
        # type: (Union[int, slice], Union[T, Iterable[T]]) -> None
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :raises IndexError: Slice is noncontinuous.
        :raises ValueError: Values length does not fit in slice.
        """
        if isinstance(item, slice):
            with self.app.write_context():
                index, stop = self.resolve_continuous_slice(item)
                if len(value) != stop - index:
                    error = "values length ({}) does not fit in slice ({})".format(
                        len(value), stop - index
                    )
                    raise ValueError(error)
                self._update(index, *value)
        else:
            self._update(item, value)

    @overload
    def __delitem__(self, index):
        # type: (int) -> None
        pass

    @overload
    def __delitem__(self, slc):
        # type: (slice) -> None
        pass

    @final
    def __delitem__(self, item):
        # type: (Union[int, slice]) -> None
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :raises IndexError: Slice is noncontinuous.
        """
        self._delete(item)

    @final
    def pop(self, index=-1):
        # type: (int) -> T
        """
        Pop value from index.

        :param index: Index.
        :return: Value.
        """
        with self.app.write_context():
            value = self[index]
            self._delete(index)
        return value


# noinspection PyTypeChecker
_PLO = TypeVar("_PLO", bound="ProxyListObject")


@final
class ProxyListObject(BaseProxyObject[T], BaseMutableList[T]):
    """Mutable proxy list."""

    __slots__ = ()

    __setitem__ = MutableListObject.__setitem__
    __delitem__ = MutableListObject.__delitem__
    pop = MutableListObject.pop

    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._state)

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> ListState[T]
        pass

    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        return self._obj[index]

    def _insert(self, index, *values):
        # type: (_PLO, int, T) -> _PLO
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        self._obj._insert(index, *values)
        return self

    def _append(self, value):
        # type: (_PLO, T) -> _PLO
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        self._obj._append(value)
        return self

    def _extend(self, iterable):
        # type: (_PLO, Iterable[T]) -> _PLO
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        self._obj._extend(iterable)
        return self

    def _remove(self, value):
        # type: (_PLO, T) -> _PLO
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        self._obj._remove(value)
        return self

    def _reverse(self):
        # type: (_PLO) -> _PLO
        """
        Reverse values.

        :return: Transformed.
        """
        self._obj._reverse()
        return self

    def _move(self, item, target_index):
        # type: (_PLO, Union[slice, int], int) -> _PLO
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        self._obj._move(item, target_index)
        return self

    def _delete(self, item):
        # type: (_PLO, Union[slice, int]) -> _PLO
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        self._obj._delete(item)
        return self

    def _update(self, index, *values):
        # type: (_PLO, int, T) -> _PLO
        """
        Update value(s) starting at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        self._obj._update(index, *values)
        return self

    def count(self, value):
        # type: (Any) -> int
        """
        Count number of occurrences of a value.

        :return: Number of occurrences.
        """
        return self._obj.count(value)

    def index(self, value, start=None, stop=None):
        # type: (Any, Optional[int], Optional[int]) -> int
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :return: Index of value.
        :raises ValueError: Provided stop but did not provide start.
        """
        return self._obj.index(value, start=start, stop=stop)

    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return self._obj.resolve_index(index, clamp=clamp)

    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return self._obj.resolve_continuous_slice(slc)

    @property
    def _state(self):
        # type: () -> ListState[T]
        """State."""
        return cast("ListState[T]", super(ProxyListObject, self)._state)

    @property
    def data(self):
        # type: () -> ListData[T]
        """Data."""
        return cast("ListData[T]", super(ProxyListObject, self).data)