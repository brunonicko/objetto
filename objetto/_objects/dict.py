# -*- coding: utf-8 -*-
"""Dictionary objects and proxy."""

from collections import Counter as ValueCounter
from typing import TYPE_CHECKING, TypeVar, cast, overload

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # type: ignore

from six import iteritems, iterkeys, itervalues, raise_from, with_metaclass

from .._applications import Application
from .._bases import FINAL_METHOD_TAG, MISSING, BaseMutableDict, final, init_context
from .._changes import DictUpdate
from .._data import BaseData, DictData, InteractiveDictData
from .._states import DictState
from .._structures import (
    BaseDictStructure,
    BaseDictStructureMeta,
    BaseMutableDictStructure,
)
from .bases import (
    DELETED,
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
        Mapping,
        Optional,
        Tuple,
        Type,
        Union,
    )

    from .._applications import Store

__all__ = ["DictObject", "MutableDictObject", "ProxyDictObject"]


KT = TypeVar("KT")  # Key type.
VT = TypeVar("VT")  # Value type.


@final
class DictObjectFunctions(BaseAuxiliaryObjectFunctions):
    """Static functions for :class:`DictObject`."""

    __slots__ = ()

    @staticmethod
    def make_data_cls_dct(auxiliary_cls):
        # type: (Type[BaseAuxiliaryObject]) -> Dict[str, Any]
        """
        Make data class member dictionary.

        :param auxiliary_cls: Base auxiliary object class.
        :return: Data class member dictionary.
        """
        dct = super(DictObjectFunctions, DictObjectFunctions).make_data_cls_dct(
            auxiliary_cls
        )
        dct.update(
            {
                "_key_relationship": cast(
                    "Type[DictObject]", auxiliary_cls
                )._key_relationship
            }
        )
        return dct

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
        data = cast("DictData", original_data)._set(data_location, new_child_data)
        return store.set("data", data)

    @staticmethod
    def update(
        obj,  # type: DictObject
        input_values,  # type: Mapping
        factory=True,  # type: bool
    ):
        # type: (...) -> None
        cls = type(obj)
        relationship = cls._relationship
        key_relationship = cls._key_relationship
        with obj.app.__.write_context(obj) as (read, write):
            if not input_values:
                return

            # Get state, data, and locations cache.
            store = read()
            state = old_state = store.state  # type: DictState
            data = store.data  # type: DictData
            metadata = store.metadata  # type: InteractiveDictData
            locations = metadata.get("locations", DictState())  # type: DictState

            # Prepare change information.
            child_counter = ValueCounter()  # type: Counter[BaseObject]
            old_children = set()
            new_children = set()
            history_adopters = set()
            new_values = {}
            old_values = {}

            # Fabricate keys first.
            if factory and cls._key_relationship.factory is not None:
                input_values = dict(
                    (key_relationship.fabricate_key(k, factory=True), v)
                    for k, v in iteritems(input_values)
                )

            # For every input value.
            for key, value in iteritems(input_values):

                # Are we deleting it?
                delete_item = value is DELETED

                # Fabricate new value if not deleting.
                if not delete_item:
                    if factory:
                        value = relationship.fabricate_value(
                            value, factory=factory, **{"app": obj.app}
                        )
                new_values[key] = value

                # Get old value.
                try:
                    old_value = store.state[key]
                except KeyError:
                    if delete_item:
                        error = "can't delete non-existing key '{}'".format(key)
                        raise KeyError(error)
                    old_value = DELETED
                else:
                    if value is old_value:
                        continue
                old_values[key] = old_value

                # Child relationship.
                if relationship.child:
                    same_app = not delete_item and obj._in_same_application(value)

                    # Update children counter, old/new children sets, and locations.
                    if old_value is not DELETED:
                        if obj._in_same_application(old_value):
                            child_counter[old_value] -= 1
                            old_children.add(old_value)
                            locations = locations.remove(old_value)
                    if same_app:
                        child_counter[value] += 1
                        new_children.add(value)
                        locations = locations.set(value, key)

                    # Add history adopter.
                    if relationship.history and same_app:
                        history_adopters.add(value)

                    # Update data.
                    if relationship.data:
                        if delete_item:
                            data = data._remove(key)
                        else:
                            data_relationship = relationship.data_relationship
                            assert data_relationship is not None
                            if same_app:
                                with value.app.__.write_context(value) as (v_read, _):
                                    data = data._set(
                                        key,
                                        data_relationship.fabricate_value(
                                            v_read().data
                                        ),
                                    )
                            else:
                                data = data._set(
                                    key,
                                    data_relationship.fabricate_value(value),
                                )

                # Update state.
                if not delete_item:
                    state = state.set(key, value)
                else:
                    state = state.remove(key)

            # Store locations in the metadata.
            metadata = metadata.set("locations", locations)

            # Prepare change.
            change = DictUpdate(
                __redo__=DictObjectFunctions.redo_update,
                __undo__=DictObjectFunctions.undo_update,
                obj=obj,
                old_children=old_children,
                new_children=new_children,
                old_values=old_values,
                new_values=new_values,
                old_state=old_state,
                new_state=state,
                history_adopters=history_adopters,
            )
            write(state, data, metadata, child_counter, change)

    @staticmethod
    def redo_update(change):
        # type: (DictUpdate) -> None
        DictObjectFunctions.update(
            cast("DictObject", change.obj),
            change.new_values,
            factory=False,
        )

    @staticmethod
    def undo_update(change):
        # type: (DictUpdate) -> None
        DictObjectFunctions.update(
            cast("DictObject", change.obj),
            change.old_values,
            factory=False,
        )


type.__setattr__(cast(type, DictObjectFunctions), FINAL_METHOD_TAG, True)


class DictObjectMeta(BaseAuxiliaryObjectMeta, BaseDictStructureMeta):
    """Metaclass for :class:`DictObject`."""

    @property
    @final
    def _state_factory(cls):
        # type: () -> Callable[..., DictState]
        """State factory."""
        return DictState

    @property
    @final
    def _base_auxiliary_type(cls):
        # type: () -> Type[DictObject]
        """Base auxiliary object type."""
        return DictObject

    @property
    @final
    def _base_auxiliary_data_type(cls):
        # type: () -> Type[DictData]
        """Base auxiliary data type."""
        return DictData


# noinspection PyTypeChecker
_DO = TypeVar("_DO", bound="DictObject")


class DictObject(
    with_metaclass(
        DictObjectMeta,
        BaseAuxiliaryObject[KT],
        BaseDictStructure[KT, VT],
    )
):
    """
    Dictionary object.

    :param app: Application.
    :param initial: Initial values.
    """

    __slots__ = ()
    __functions__ = DictObjectFunctions

    def __init__(
        self,
        app,  # type: Application
        initial=(),  # type: Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]]
    ):
        # type: (...) -> None
        super(DictObject, self).__init__(app=app)
        self.__functions__.update(self, dict(initial))

    @final
    def _clear(self):
        # type: (_DO) -> _DO
        """
        Clear.

        :return: Transformed.
        :raises AttributeError: No deletable attributes.
        """
        with self.app.write_context():
            self._update((k, DELETED) for k in self._state)
        return self

    @overload
    def _update(self, __m, **kwargs):
        # type: (_DO, Mapping[KT, VT], VT) -> _DO
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (_DO, Iterable[Tuple[KT, VT]], VT) -> _DO
        pass

    @overload
    def _update(self, **kwargs):
        # type: (_DO, VT) -> _DO
        pass

    @final
    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        self.__functions__.update(self, dict(*args, **kwargs))
        return self

    @final
    def _set(self, key, value):
        # type: (_DO, KT, VT) -> _DO
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        self.__functions__.update(self, {key: value})
        return self

    @final
    def _discard(self, key):
        # type: (_DO, KT) -> _DO
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        with self.app.write_context():
            if key in self._state:
                self.__functions__.update(self, {key: DELETED})
        return self

    @final
    def _remove(self, key):
        # type: (_DO, KT) -> _DO
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        self.__functions__.update(self, {key: DELETED})
        return self

    @final
    def _locate(self, child):
        # type: (BaseObject) -> KT
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
                error = "could not locate child {} in {}".format(child, self)
                exc = ValueError(error)
                raise_from(exc, None)
                raise exc

    @final
    def _locate_data(self, child):
        # type: (BaseObject) -> KT
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
        # type: (Type[_DO], Dict[str, Any], Application, Any) -> _DO
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
            self = cast("_DO", cls.__new__(cls))
            with init_context(self):
                super(DictObject, self).__init__(app)
                initial = dict(
                    (n, cls.deserialize_value(v, None, **kwargs))
                    for n, v in iteritems(serialized)
                    if cls._relationship.serialized
                )
                self.__functions__.update(self, initial)
            return self

    @final
    def serialize(self, **kwargs):
        # type: (Any) -> Dict
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to serializer functions.
        :return: Serialized.
        """
        with self.app.read_context():
            return dict(
                (k, self.serialize_value(v, None, **kwargs))
                for (k, v) in iteritems(self._state)
                if type(self)._relationship.serialized
            )

    @property
    @final
    def _state(self):
        # type: () -> DictState[KT, VT]
        """State."""
        return cast("DictState[KT, VT]", super(BaseDictStructure, self)._state)

    @property
    @final
    def data(self):
        # type: () -> DictData[KT, VT]
        """Data."""
        return cast("DictData[KT, VT]", super(BaseDictStructure, self).data)


# noinspection PyAbstractClass
class MutableDictObject(
    DictObject[KT, VT], BaseMutableAuxiliaryObject[KT], BaseMutableDictStructure[KT, VT]
):
    """Mutable dictionary object."""

    __slots__ = ()

    @final
    def __setitem__(self, key, value):
        # type: (KT, VT) -> None
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        """
        self._set(key, value)

    @final
    def __delitem__(self, key):
        # type: (KT) -> None
        """
        Delete key.

        :param key: Key.
        :raises KeyError: Key is not preset.
        """
        self._remove(key)

    @final
    def pop(self, key, fallback=MISSING):
        # type: (KT, Any) -> Union[VT, Any]
        """
        Get value for key and remove it, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        :raises KeyError: Key is not present and fallback value not provided.
        """
        with self.app.write_context():
            try:
                value = self[key]
            except KeyError:
                if fallback is not MISSING:
                    return fallback
                raise
            else:
                self._remove(key)
                return value

    @final
    def popitem(self):
        # type: () -> Tuple[KT, VT]
        """
        Get item and discard key.

        :return: Item.
        :raises KeyError: Dictionary is empty.
        """
        with self.app.write_context():
            if not self:
                error = "dictionary is empty"
                raise KeyError(error)
            key = next(iter(self))
            return key, self.pop(key)

    @final
    def setdefault(self, key, default=None):
        # type: (KT, Optional[VT]) -> VT
        """
        Get the value for the specified key, insert key with default if not present.

        :param key: Key.
        :param default: Default value.
        :return: Existing or default value.
        """
        with self.app.write_context():
            try:
                return self[key]
            except KeyError:
                self._set(key, cast("VT", default))
                return self[key]


# noinspection PyTypeChecker
_PDO = TypeVar("_PDO", bound="ProxyDictObject")


@final
class ProxyDictObject(BaseProxyObject[KT], BaseMutableDict[KT, VT]):
    """Mutable proxy dictionary."""

    __slots__ = ()

    __setitem__ = MutableDictObject.__setitem__
    __delitem__ = MutableDictObject.__delitem__
    pop = MutableDictObject.pop
    popitem = MutableDictObject.popitem
    setdefault = MutableDictObject.setdefault

    def __reversed__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over reversed keys.

        :return: Reversed keys iterator.
        """
        return reversed(self._state)

    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Invalid key.
        """
        return self._obj.__getitem__(key)

    @overload
    def _update(self, __m, **kwargs):
        # type: (_PDO, Mapping[KT, VT], VT) -> _PDO
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (_PDO, Iterable[Tuple[KT, VT]], VT) -> _PDO
        pass

    @overload
    def _update(self, **kwargs):
        # type: (_PDO, VT) -> _PDO
        pass

    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        self._obj._update(*args, **kwargs)
        return self

    def _set(self, key, value):
        # type: (_PDO, KT, VT) -> _PDO
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        self._obj._set(key, value)
        return self

    def _discard(self, key):
        # type: (_PDO, KT) -> _PDO
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        self._obj._remove(key)
        return self

    def _remove(self, key):
        # type: (_PDO, KT) -> _PDO
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        self._obj._remove(key)
        return self

    def get(self, key, fallback=None):
        # type: (KT, Any) -> Union[VT, Any]
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._obj.get(key, fallback)

    def iteritems(self):
        # type: () -> Iterator[Tuple[KT, VT]]
        """
        Iterate over keys.

        :return: Key iterator.
        """
        for key, value in iteritems(self._state):
            yield key, value

    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in iterkeys(self._state):
            yield key

    def itervalues(self):
        # type: () -> Iterator[VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in itervalues(self._state):
            yield value

    @property
    def _obj(self):
        # type: () -> DictObject[KT, VT]
        """Dict object."""
        return cast("DictObject[KT, VT]", super(ProxyDictObject, self)._obj)

    @property
    def _state(self):
        # type: () -> DictState[KT, VT]
        """State."""
        return cast("DictState[KT, VT]", super(ProxyDictObject, self)._state)

    @property
    def data(self):
        # type: () -> DictData[KT, VT]
        """Data."""
        return cast("DictData[KT, VT]", super(ProxyDictObject, self).data)
