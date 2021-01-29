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
    SerializationError,
)
from ..utils.dummy_context import DummyContext
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
        MutableSequence,
        Optional,
        Sequence,
        Set,
        Tuple,
        Type,
        Union,
    )

    from .._applications import Store
    from .._history import HistoryObject

__all__ = ["ListObjectMeta", "ListObject", "MutableListObject", "ProxyListObject"]


T = TypeVar("T")  # Any type.


@final
class ListObjectFunctions(BaseAuxiliaryObjectFunctions):
    """Static functions for `ListObject`."""

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
        data = cast("ListData", original_data)._update(data_location, new_child_data)
        return store.set("data", data)

    @staticmethod
    def insert(
        obj,  # type: ListObject
        index,  # type: int
        input_values,  # type: Iterable[Any]
        factory=True,  # type: bool
        history=None,  # type: Optional[HistoryObject]
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship
        input_values = list(input_values)

        # Batch context.
        batch_name = cls._BATCH_INSERT_NAME
        if batch_name is None:
            context = DummyContext()  # type: ignore
        else:
            context = obj._batch_context(name=batch_name)  # type: ignore

        # Write context.
        with context, obj.app.__.write_context(obj) as (read, write):
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
                        assert data_relationship is not None
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
                history=history,
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
            history=change.obj._history,
        )

    @staticmethod
    def undo_insert(change):
        # type: (ListInsert) -> None
        ListObjectFunctions.delete(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
            history=change.obj._history,
        )

    @staticmethod
    def delete(
        obj,  # type: ListObject
        item,  # type: Union[int, slice]
        history=None,  # type: Optional[HistoryObject]
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship

        # Batch context.
        batch_name = cls._BATCH_DELETE_NAME
        if batch_name is None:
            context = DummyContext()  # type: ignore
        else:
            context = obj._batch_context(name=batch_name)  # type: ignore

        # Write context.
        with context, obj.app.__.write_context(obj) as (read, write):

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
            state = state.delete(slc)
            if relationship.data:
                data = data._delete(slc)

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
                history=history,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_delete(change):
        # type: (ListDelete) -> None
        ListObjectFunctions.delete(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
            history=change.obj._history,
        )

    @staticmethod
    def undo_delete(change):
        # type: (ListDelete) -> None
        ListObjectFunctions.insert(
            cast("ListObject", change.obj),
            change.index,
            change.old_values,
            factory=False,
            history=change.obj._history,
        )

    @staticmethod
    def update(
        obj,  # type: ListObject
        item,  # type: Union[int, slice]
        input_values,  # type: Iterable[Any]
        factory=True,  # type: bool
        history=None,  # type: Optional[HistoryObject]
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship

        # Batch context.
        batch_name = cls._BATCH_UPDATE_NAME
        if batch_name is None:
            context = DummyContext()  # type: ignore
        else:
            context = obj._batch_context(name=batch_name)  # type: ignore

        # Write context.
        with context, obj.app.__.write_context(obj) as (read, write):

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
                        assert data_relationship is not None
                        if same_app:
                            with value.app.__.write_context(value) as (v_read, _):
                                data_value = data_relationship.fabricate_value(
                                    v_read().data,
                                )
                        else:
                            data_value = data_relationship.fabricate_value(value)
                        new_data_values.append(data_value)

            # Update state and data.
            state = state.update(index, *new_values)
            if relationship.data:
                data = data._update(index, *new_data_values)

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
                history=history,
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
            history=change.obj._history,
        )

    @staticmethod
    def undo_update(change):
        # type: (ListUpdate) -> None
        ListObjectFunctions.update(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
            change.old_values,
            factory=False,
            history=change.obj._history,
        )

    @staticmethod
    def move(
        obj,  # type: ListObject
        item,  # type: Union[int, slice]
        target_index,  # type: int
        history=None,  # type: Optional[HistoryObject]
    ):
        # type: (...) -> None
        cls = type(obj)

        # Batch context.
        batch_name = cls._BATCH_MOVE_NAME
        if batch_name is None:
            context = DummyContext()  # type: ignore
        else:
            context = obj._batch_context(name=batch_name)  # type: ignore

        # Write context.
        with context, obj.app.__.write_context(obj) as (read, write):

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
                history=history,
            )
            write(state, data, metadata, ValueCounter(), change)

    @staticmethod
    def redo_move(change):
        # type: (ListMove) -> None
        ListObjectFunctions.move(
            cast("ListObject", change.obj),
            slice(change.index, change.stop),
            change.target_index,
            history=change.obj._history,
        )

    @staticmethod
    def undo_move(change):
        # type: (ListMove) -> None
        ListObjectFunctions.move(
            cast("ListObject", change.obj),
            slice(change.post_index, change.post_stop),
            change.index,
            history=change.obj._history,
        )


type.__setattr__(cast(type, ListObjectFunctions), FINAL_METHOD_TAG, True)


class ListObjectMeta(BaseAuxiliaryObjectMeta, BaseListStructureMeta):
    """
    Metaclass for :class:`objetto.objects.ListObject`.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryObjectMeta`
      - :class:`objetto.bases.BaseListStructureMeta`

    Features:
      - Defines a state factory.
      - Defines a base auxiliary type.
      - Defines a base auxiliary data type.
    """

    def __init__(cls, name, bases, dct):
        # type: (str, Tuple[Type, ...], Dict[str, Any]) -> None
        super(ListObjectMeta, cls).__init__(name, bases, dct)

        # Prevent subclasses from overriding '__getitem__'.
        if "__getitem__" in dct:
            allowed_classes = set()
            try:
                allowed_classes.add(ListObject)
                allowed_classes.add(MutableListObject)
            except NameError:
                pass
            if len(allowed_classes) == 2 and cls not in allowed_classes:
                error = "can't override final member '__getitem__'"
                raise TypeError(error)

    @property
    @final
    def _state_factory(cls):
        # type: () -> Callable[..., ListState]
        """
        State factory.

        :rtype: type[objetto.states.ListState]
        """
        return ListState

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[ListObject]
        """
        Base auxiliary object type.

        :rtype: type[objetto.objects.ListObject]
        """
        return ListObject

    @property
    @final
    def _base_auxiliary_data_type(cls):
        # type: () -> Type[ListData]
        """
        Base auxiliary data type.

        :rtype: type[objetto.data.ListData]
        """
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

    Metaclass:
      - :class:`objetto.objects.ListObjectMeta`

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryObject`
      - :class:`objetto.bases.BaseListStructure`

    Inherited by:
      - :class:`objetto.objects.MutableListObject`

    :param app: Application.
    :type app: objetto.applications.Application

    :param initial: Initial values.
    :type initial: collections.abc.Iterable
    """

    __slots__ = ()
    __functions__ = ListObjectFunctions

    _BATCH_INSERT_NAME = None  # type: Optional[str]
    """
    Batch name for insert operations.

    :type: str or None
    """

    _BATCH_DELETE_NAME = None  # type: Optional[str]
    """
    Batch name for delete operations.

    :type: str or None
    """

    _BATCH_UPDATE_NAME = None  # type: Optional[str]
    """
    Batch name for update operations.

    :type: str or None
    """

    _BATCH_MOVE_NAME = None  # type: Optional[str]
    """
    Batch name for move operations.

    :type: str or None
    """

    def __init__(self, app, initial=()):
        # type: (Application, Iterable[T]) -> None
        super(ListObject, self).__init__(app=app)
        self.__functions__.insert(self, 0, initial)

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> Sequence[T]
        pass

    # @final (special case, taken care of by the metaclass)
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :type index: int or slice

        :return: Value/values.
        :rtype: Any or objetto.states.ListState
        """
        return self._state[index]

    @final
    def _clear(self):
        # type: (_LO) -> _LO
        """
        Clear all values.

        :return: Transformed.
        :rtype: objetto.objects.ListObject
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
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :rtype: objetto.objects.ListObject

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
        :rtype: objetto.objects.ListObject
        """
        self.__functions__.insert(self, len(self._state), (value,))
        return self

    @final
    def _extend(self, iterable):
        # type: (_LO, Iterable[T]) -> _LO
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :type iterable: collections.abc.Iterable

        :return: Transformed.
        :rtype: objetto.objects.ListObject
        """
        values = list(iterable)
        if not values:
            return self
        self.__functions__.insert(self, len(self._state), values)
        return self

    @final
    def _remove(self, value):
        # type: (_LO, T) -> _LO
        """
        Remove first occurrence of value.

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.objects.ListObject

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
        :rtype: objetto.objects.ListObject
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
        :type item: int or slice

        :param target_index: Target index.
        :type target_index: int

        :return: Transformed.
        :rtype: objetto.objects.ListObject
        """
        self.__functions__.move(self, item, target_index)
        return self

    @final
    def _delete(self, item):
        # type: (_LO, Union[slice, int]) -> _LO
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :type item: int or slice

        :return: Transformed.
        :rtype: objetto.objects.ListObject
        """
        self.__functions__.delete(self, item)
        return self

    @final
    def _update(self, index, *values):
        # type: (_LO, int, T) -> _LO
        """
        Update value(s) starting at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :rtype: objetto.objects.ListObject

        :raises ValueError: No values provided.
        """
        if not values:
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
        :type child: objetto.bases.BaseObject

        :return: Location.
        :rtype: int

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
        :type child: objetto.bases.BaseObject

        :return: Data location.
        :rtype: int

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
        :type serialized: list

        :param app: Application (required).
        :type app: objetto.applications.Application

        :param kwargs: Keyword arguments to be passed to the deserializers.

        :return: Deserialized.
        :rtype: objetto.objects.ListObject

        :raises objetto.exceptions.SerializationError: Can't deserialize.
        """
        if app is None:
            error = (
                "missing required 'app' keyword argument for '{}.deserialize()' method"
            ).format(cls.__fullname__)
            raise ValueError(error)
        kwargs["app"] = app

        if not cls._relationship.serialized:
            error = "'{}' is not deserializable".format(cls.__name__)
            raise SerializationError(error)

        with app.write_context():
            self = cast("_LO", cls.__new__(cls))
            with init_context(self):
                super(ListObject, self).__init__(app)
                initial = (
                    cls.deserialize_value(v, None, **kwargs)
                    for v in serialized
                    if cls._relationship.serialized
                )
                self.__functions__.insert(self, 0, initial)
            self.__post_deserialize__()
            return self

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> List
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.

        :return: Serialized.
        :rtype: list

        :raises objetto.exceptions.SerializationError: Can't serialize.
        """
        with self.app.read_context():

            if not type(self)._relationship.serialized:
                error = "'{}' is not serializable".format(type(self).__fullname__)
                raise SerializationError(error)

            return list(
                self.serialize_value(v, None, **kwargs)
                for v in self._state
                if type(self)._relationship.serialized
            )

    @property
    @final
    def _state(self):
        # type: () -> ListState[T]
        """
        State.

        :rtype: objetto.states.ListState
        """
        return cast("ListState[T]", super(BaseListStructure, self)._state)

    @property
    @final
    def data(self):
        # type: () -> ListData[T]
        """
        Data.

        :rtype: objetto.data.ListData
        """
        return cast("ListData[T]", super(BaseListStructure, self).data)


# noinspection PyAbstractClass
class MutableListObject(
    BaseMutableListStructure[T], ListObject[T], BaseMutableAuxiliaryObject[T]
):
    """
    Mutable list object.

    Inherits from:
      - :class:`objetto.bases.BaseMutableListStructure`
      - :class:`objetto.objects.ListObject`
      - :class:`objetto.bases.BaseMutableAuxiliaryObject`

    .. code:: python

        >>> from objetto import Application, Object, attribute
        >>> from objetto.objects import MutableListObject, Relationship

        >>> class Hobby(Object):
        ...     description = attribute(str)
        ...
        >>> class HobbiesList(MutableListObject):  # inherit from MutableListObject
        ...     _relationship = Relationship(Hobby)  # define relationship with type
        ...
        >>> app = Application()
        >>> hobby_a = Hobby(app, description="biking")
        >>> hobby_b = Hobby(app, description="gaming")
        >>> hobbies = HobbiesList(app)  # make new instance
        >>> hobbies.extend((hobby_a, hobby_b))  # extend list with 'hobby' objects
    """

    __slots__ = ()

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T]
        pass

    @final
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :type index: int or slice

        :return: Value/values.
        :rtype: Any or list
        """
        if isinstance(index, slice):
            return list(self._state[index])
        else:
            return self._state[index]

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
        :type item: int or slice

        :param value: Value/values.
        :type value: Any or collections.abc.Iterable

        :raises IndexError: Slice is noncontinuous.
        :raises ValueError: Values length does not fit in slice.
        """
        if isinstance(item, slice):
            with self.app.write_context():
                values = tuple(cast("Iterable[T]", value))
                index, stop = self.resolve_continuous_slice(item)
                if len(values) != stop - index:
                    error = "values length ({}) does not fit in slice ({})".format(
                        len(values), stop - index
                    )
                    raise ValueError(error)
                self._update(index, *values)
        else:
            self._update(item, cast("T", value))

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
        :type item: int or slice

        :raises IndexError: Slice is noncontinuous.
        """
        self._delete(item)

    @final
    def pop(self, index=-1):
        # type: (int) -> T
        """
        Pop value from index.

        :param index: Index.
        :type index: int

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
    """
    Mutable proxy list.

    Inherits from:
      - :class:`objetto.bases.BaseProxyObject`
      - :class:`objetto.bases.BaseMutableList`
    """

    __slots__ = ()

    @overload
    def __setitem__(self, index, value):
        # type: (int, T) -> None
        pass

    @overload
    def __setitem__(self, slc, values):
        # type: (slice, Iterable[T]) -> None
        pass

    def __setitem__(self, item, value):
        # type: (Union[int, slice], Union[T, Iterable[T]]) -> None
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :type item: int or slice

        :param value: Value/values.
        :type value: Any or collections.abc.Iterable

        :raises IndexError: Slice is noncontinuous.
        :raises ValueError: Values length does not fit in slice.
        """
        if isinstance(item, slice):
            with self.app.write_context():
                values = tuple(cast("Iterable[T]", value))
                index, stop = self.resolve_continuous_slice(item)
                if len(values) != stop - index:
                    error = "values length ({}) does not fit in slice ({})".format(
                        len(values), stop - index
                    )
                    raise ValueError(error)
                self._update(index, *values)
        else:
            self._update(item, cast("T", value))

    @overload
    def __delitem__(self, index):
        # type: (int) -> None
        pass

    @overload
    def __delitem__(self, slc):
        # type: (slice) -> None
        pass

    def __delitem__(self, item):
        # type: (Union[int, slice]) -> None
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :type item: int or slice

        :raises IndexError: Slice is noncontinuous.
        """
        self._delete(item)

    def __reversed__(self):
        # type: () -> Iterator[T]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        :rtype: collections.abc.Iterator
        """
        return reversed(self._state)

    @overload
    def __getitem__(self, index):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T]
        pass

    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :type index: int or slice

        :return: Value/values.
        :rtype: list
        """
        if isinstance(index, slice):
            return list(self._state[index])
        else:
            return self._obj[index]

    def _insert(self, index, *values):
        # type: (_PLO, int, T) -> _PLO
        """
        Insert value(s) at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :rtype: objetto.objects.ProxyListObject

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
        :rtype: objetto.objects.ProxyListObject
        """
        self._obj._append(value)
        return self

    def _extend(self, iterable):
        # type: (_PLO, Iterable[T]) -> _PLO
        """
        Extend at the end with iterable.

        :param iterable: Iterable.

        :return: Transformed.
        :rtype: objetto.objects.ProxyListObject
        """
        self._obj._extend(iterable)
        return self

    def _remove(self, value):
        # type: (_PLO, T) -> _PLO
        """
        Remove first occurrence of value.

        :param value: Value.

        :return: Transformed.
        :rtype: objetto.objects.ProxyListObject

        :raises ValueError: Value is not present.
        """
        self._obj._remove(value)
        return self

    def _reverse(self):
        # type: (_PLO) -> _PLO
        """
        Reverse values.

        :return: Transformed.
        :rtype: objetto.objects.ProxyListObject
        """
        self._obj._reverse()
        return self

    def _move(self, item, target_index):
        # type: (_PLO, Union[slice, int], int) -> _PLO
        """
        Move values internally.

        :param item: Index/slice.
        :type item: int or slice

        :param target_index: Target index.
        :type target_index: int

        :return: Transformed.
        :rtype: objetto.objects.ProxyListObject
        """
        self._obj._move(item, target_index)
        return self

    def _delete(self, item):
        # type: (_PLO, Union[slice, int]) -> _PLO
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :type item: int or slice

        :return: Transformed.
        :rtype: objetto.objects.ProxyListObject
        """
        self._obj._delete(item)
        return self

    def _update(self, index, *values):
        # type: (_PLO, int, T) -> _PLO
        """
        Update value(s) starting at index.

        :param index: Index.
        :type index: int

        :param values: Value(s).

        :return: Transformed.
        :raises ValueError: No values provided.
        """
        self._obj._update(index, *values)
        return self

    def pop(self, index=-1):
        # type: (int) -> T
        """
        Pop value from index.

        :param index: Index.
        :type index: int

        :return: Value.
        """
        with self.app.write_context():
            value = self[index]
            self._delete(index)
        return value

    def count(self, value):
        # type: (Any) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.

        :return: Number of occurrences.
        :rtype: int
        """
        return self._obj.count(value)

    def index(self, value, start=None, stop=None):
        # type: (Any, Optional[int], Optional[int]) -> int
        """
        Get index of a value.

        :param value: Value.

        :param start: Start index.
        :type start: int or None

        :param stop: Stop index.
        :type stop: int or None

        :return: Index of value.
        :rtype: int

        :raises ValueError: Provided stop but did not provide start.
        """
        return self._obj.index(value, start=start, stop=stop)

    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :type index: int

        :param clamp: Whether to clamp between zero and the length.
        :type clamp: bool

        :return: Resolved index.
        :rtype: int

        :raises IndexError: Index out of range.
        """
        return self._obj.resolve_index(index, clamp=clamp)

    def resolve_continuous_slice(self, slc):
        # type: (slice) -> Tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :type slc: slice

        :return: Index and stop.
        :rtype: tuple[int, int]

        :raises IndexError: Slice is noncontinuous.
        """
        return self._obj.resolve_continuous_slice(slc)

    @property
    def _obj(self):
        # type: () -> ListObject[T]
        """
        List object.

        :rtype: objetto.objects.ListObject
        """
        return cast("ListObject[T]", super(ProxyListObject, self)._obj)

    @property
    def _state(self):
        # type: () -> ListState[T]
        """
        State.

        :rtype: objetto.states.ListState
        """
        return cast("ListState[T]", super(ProxyListObject, self)._state)

    @property
    def data(self):
        # type: () -> Optional[ListData[T]]
        """
        Data.

        :rtype: objetto.data.ListData or None
        """
        return cast("Optional[ListData[T]]", super(ProxyListObject, self).data)
