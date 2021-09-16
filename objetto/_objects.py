# -*- coding: utf-8 -*-

import inspect
from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar
from contextlib import contextmanager
from weakref import ref

from six import with_metaclass, iteritems, raise_from
from pyrsistent import pmap, pvector

from .utils.base import BaseMeta, Base, final
from .utils.subject_observer import Subject
from .utils.type_checking import assert_is_instance
from .utils.pointer import Pointer
from ._application import Application, resolve_history
from ._constants import DEAD_REF
from ._descriptors import ReactionDescriptor, HistoryDescriptor, HashDescriptor
from ._structures import FrozenStore, Store, State

if TYPE_CHECKING:
    from weakref import ReferenceType
    from typing import Any, Dict, Callable, Optional, Iterator, Tuple, Type

    from ._structures import Storage

    T_Data = TypeVar("T_Data")
    T_Metadata = TypeVar("T_Metadata")

__all__ = [
    "AbstractObjectMeta",
    "AbstractObject",
    "AbstractHistoryObject",
]


# noinspection PyAbstractClass
class AbstractObjectMeta(BaseMeta):
    """Metaclass for :class:`AbstractObject`."""

    def __init__(cls, name, bases, dct):
        super(AbstractObjectMeta, cls).__init__(name, bases, dct)

        # Scan and collect members following the MRO.
        reaction_descriptors = {}  # type: Dict[str, ReactionDescriptor]
        history_descriptors = {}  # type: Dict[str, HistoryDescriptor]
        for base in reversed(inspect.getmro(cls)):
            for member_name, member in iteritems(base.__dict__):
                history_descriptors.pop(member_name, None)
                reaction_descriptors.pop(member_name, None)

                if isinstance(member, ReactionDescriptor):
                    reaction_descriptors[member_name] = member
                elif isinstance(member, HistoryDescriptor):
                    history_descriptors[member_name] = member

        # Store history descriptor, ensure there's only one.
        if len(history_descriptors) > 1:
            error = "'{}' has multiple history descriptors defined as {}".format(
                cls.__name__, ", ".join("'{}'".format(n) for n in history_descriptors)
            )
            raise TypeError(error)
        elif history_descriptors:
            history_descriptor_name, history_descriptor = next(
                iter(history_descriptors.items())
            )
        else:
            history_descriptor_name, history_descriptor = None, None

        cls.__namespace__.__history_descriptor_name = history_descriptor_name
        cls.__namespace__.__history_descriptor = history_descriptor

        # Store reaction descriptors sorted by priority, then name.
        sorted_reaction_descriptor_items = sorted(
            iteritems(reaction_descriptors),
            key=lambda rd: (rd[1].priority is None, rd[1].priority, rd[0]),
        )
        if sorted_reaction_descriptor_items:
            sorted_reaction_descriptor_names, sorted_reaction_descriptors = zip(
                *sorted_reaction_descriptor_items
            )
        else:
            sorted_reaction_descriptor_names, sorted_reaction_descriptors = (), ()

        cls.__namespace__.__reaction_descriptor_names = sorted_reaction_descriptor_names
        cls.__namespace__.__reaction_descriptors = sorted_reaction_descriptors

    @property
    @final
    def _history_descriptor_name(cls):
        # type: () -> Optional[str]
        """History descriptor's name."""
        return cls.__namespace__.__history_descriptor_name

    @property
    @final
    def _history_descriptor(cls):
        # type: () -> Optional[HistoryDescriptor]
        """History descriptor."""
        return cls.__namespace__.__history_descriptor

    @property
    @final
    def _reaction_descriptor_names(cls):
        # type: () -> Tuple[str, ...]
        """Reaction descriptors' names."""
        return cls.__namespace__.__reaction_descriptor_names

    @property
    @final
    def _reaction_descriptors(cls):
        # type: () -> Tuple[ReactionDescriptor, ...]
        """Reaction descriptors."""
        return cls.__namespace__.__reaction_descriptors


T_AbstractObject = TypeVar("T_AbstractObject", bound="AbstractObject")


# noinspection PyAbstractClass
class AbstractObject(with_metaclass(AbstractObjectMeta, Base)):

    __slots__ = (
        "__weakref__",
        "__subject",
        "__pointer",
        "__frozen_store",
        "__frozen_hash",
        "__app",
        "_Writer__acting",
        "_Writer__pinned_count",
        "_Writer__pinned_hierarchy",
    )

    __hash__ = HashDescriptor()  # type: ignore

    def __init__(self, app, *args, **kwargs):
        # type: (T_AbstractObject, Application, Any, Any) -> None
        assert_is_instance(app, Application, accept_subtypes=False)

        with app.require_write_context():
            self.__subject = Subject(self)  # type: Subject[T_AbstractObject]
            self.__pointer = Pointer(self)  # type: Pointer[T_AbstractObject]
            self.__frozen_store = None  # type: Optional[FrozenStore]
            self.__frozen_hash = None  # type: Optional[int]
            self.__app = app  # type: Application

            self._Writer__acting = False  # type: bool
            self._Writer__pinned_count = 0  # type: int
            self._Writer__pinned_hierarchy = (
                None
            )  # type: Optional[Tuple[AbstractObject, ...]]

            # Get init args.
            init_args = {"app": app}  # type: Dict[str, Any]

            try:
                arg_spec = type(self).__namespace__.__init_arg_spec  # type: ignore
            except AttributeError:
                try:
                    arg_spec = inspect.getfullargspec(self.__init__)  # type: ignore
                except AttributeError:
                    # noinspection PyDeprecation
                    arg_spec = inspect.getargspec(self.__init__)  # type: ignore
                type(self).__namespace__.__init_arg_spec = arg_spec

            arg_names = arg_spec.args[2:]
            arg_names_len = len(arg_names)
            if arg_spec.varargs is not None:
                init_args[arg_spec.varargs] = ()
            for i, arg in enumerate(args):
                if i < arg_names_len:
                    init_args[arg_names[i]] = arg
                else:
                    assert arg_spec.varargs is not None
                    init_args[arg_spec.varargs] = args[i:]
                    break
            init_args.update(kwargs)

            # Initialize under a write context.
            with app._AbstractObject__write_context() as writer:

                # Init history if has a descriptor.
                history_descriptor = type(self)._history_descriptor
                if history_descriptor is not None:
                    history_provider_ref = ref(
                        self
                    )  # type: Optional[ReferenceType[AbstractObject]]
                    history = history_descriptor.type(
                        app, history_descriptor
                    )  # type: Optional[AbstractHistoryObject]
                else:
                    history_provider_ref = None
                    history = None

                # Init store.
                state = type(self).__init_state__(init_args)
                store = Store(
                    state=state,
                    parent_ref=None,
                    history_provider_ref=history_provider_ref,
                    last_parent_history_ref=None,
                    history=history,
                )
                writer.init_store(self, store)

                # Run post-init under the same write context.
                self.__post_init__(init_args)

    @classmethod
    @abstractmethod
    def __init_state__(cls, args):
        # type: (Dict[str, Any]) -> State
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def __freeze_data__(
        cls,
        data,  # type: T_Data
        metadata,  # type: T_Metadata
        child_freezer,  # type: Callable[[T_AbstractObject], T_AbstractObject]
    ):
        # type: (...) -> Tuple[T_Data, T_Metadata]
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def __get_hash__(cls, state):
        # type: (State) -> int
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def __get_eq__(cls, state, other_state):
        # type: (State, State) -> bool
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def __locate_child__(cls, child, state):
        # type: (AbstractObject, State) -> Any
        raise NotImplementedError()

    def __post_init__(self, args):
        # type: (Dict[str, Any]) -> None
        pass

    def __repr__(self):
        # type: () -> str
        return "<{}{} at {}>".format(
            "FROZEN " if self.__frozen_store is not None else "",
            type(self).__fullname__,
            hex(id(self)),
        )

    def __eq__(self, other):
        same_type = type(self) is type(other)

        if self.__frozen_store is not None:
            if same_type:
                assert isinstance(other, type(self))
                state = self.__frozen_store.state
                other_state = other._get_state()
                return type(self).__get_eq__(state, other_state)
            else:
                return False

        with self.app.require_context():
            with self.app._AbstractObject__read_context() as storage:
                if same_type:
                    assert isinstance(other, type(self))
                    state = self.__get_store(storage).state
                    other_state = other._get_state()
                    return type(self).__get_eq__(state, other_state)
                else:
                    return False

    @final
    def __get_store(self, storage):
        # type: (Storage[Pointer[AbstractObject], Store]) -> Store
        try:
            return storage.query(self.pointer)
        except KeyError:
            error = "'{}' object not initialized".format(type(self).__fullname__)
            exc = RuntimeError(error)
            raise_from(exc, None)
            raise exc

    @classmethod
    @final
    def __get_frozen(
        cls,  # type: Type[T_AbstractObject]
        storage,  # type: Storage[Pointer[AbstractObject], Store]
        state,  # type: State
        frozen_parent_ref,  # type: Optional[ReferenceType[AbstractObject]]
    ):
        # type: (...) -> T_AbstractObject
        self = cls.__new__(cls)
        self_ref = ref(self)

        memo = {}  # type: Dict[int, AbstractObject]

        def child_freezer(child):
            # type: (AbstractObject) -> AbstractObject
            assert child.pointer in state.children_pointers
            child_id = id(child)
            if child_id in memo:
                return memo[child_id]
            child_state = child.__get_store(storage).state
            memo[child_id] = frozen_child = type(child).__get_frozen(
                storage, child_state, self_ref
            )
            return frozen_child

        frozen_data, frozen_metadata = cls.__freeze_data__(
            state.data, state.metadata, child_freezer
        )
        frozen_children_pointers = pmap(
            (memo[id(c.obj)], r) for c, r in iteritems(state.children_pointers)
        )
        frozen_state = State(
            data=frozen_data,
            metadata=frozen_metadata,
            children_pointers=frozen_children_pointers,
        )

        self.__pointer = Pointer(self)
        self.__frozen_store = FrozenStore(
            state=frozen_state, parent_ref=frozen_parent_ref
        )
        self.__frozen_hash = None

        return self

    @final
    def _get_frozen(self):
        # type: (T_AbstractObject) -> T_AbstractObject
        if self.__frozen_store is not None:
            return self

        with self.app.require_context():
            with self.app._AbstractObject__read_context() as storage:
                store = self.__get_store(storage)
                if store.parent_ref is not None:
                    parent_ref = DEAD_REF  # type: Optional[ReferenceType]
                else:
                    parent_ref = None
                state = store.state
                return self.__get_frozen(storage, state, parent_ref)

    @final
    def _get_hash(self):
        # type: () -> int
        if self.__frozen_hash is not None:
            return self.__frozen_hash

        if self.__frozen_store is not None:
            state = self.__frozen_store.state
            self.__frozen_hash = frozen_hash = type(self).__get_hash__(state)
            return frozen_hash

        error = "'{}' object is not frozen and therefore not hashable".format(
            type(self).__fullname__
        )
        raise RuntimeError(error)

    @final
    def _get_location(self, child):
        # type: (AbstractObject) -> Any
        if self.__frozen_store is not None:
            state = self.__frozen_store.state
            return type(self).__locate_child__(child, state)

        with self.app.require_context():
            with self.app._AbstractObject__read_context() as storage:
                store = self.__get_store(storage)
                state = store.state
                return type(self).__locate_child__(child, state)

    @final
    def _get_parent(self):
        # type: () -> Optional[AbstractObject]
        if self.__frozen_store is not None:
            if self.__frozen_store.parent_ref is not None:
                parent = self.__frozen_store.parent_ref()
                if parent is None:
                    error = "frozen parent object is no longer in memory"
                    raise ReferenceError(error)
                return parent
            else:
                return None

        with self.app.require_context():
            with self.app._AbstractObject__read_context() as storage:
                store = self.__get_store(storage)
                if store.parent_ref is not None:
                    parent = store.parent_ref()
                    if parent is None:
                        error = "parent object is no longer in memory"
                        raise ReferenceError(error)
                    return parent
                else:
                    return None

    @final
    def _get_history(self):
        # type: () -> Optional[AbstractHistoryObject]
        if self.__frozen_store is not None:
            error = "'{}' object is frozen and therefore cannot have a history".format(
                type(self).__fullname__
            )
            raise RuntimeError(error)

        with self.app.require_context():
            with self.app._AbstractObject__read_context() as storage:
                return resolve_history(self, storage)

    @final
    def _get_state(self):
        # type: () -> State
        if self.__frozen_store is not None:
            return self.__frozen_store.state

        with self.app.require_context():
            with self.app._AbstractObject__read_context() as storage:
                store = self.__get_store(storage)
                return store.state

    @final
    def _set_state(self, new_state, event=None, undo_event=None):
        # type: (State, Any, Any) -> None
        if self.__frozen_store is not None:
            error = "'{}' object is frozen and therefore cannot be mutated".format(
                type(self).__fullname__
            )
            raise RuntimeError(error)

        with self.app.require_write_context():
            with self.app._AbstractObject__write_context() as writer:
                writer.act(self, new_state, event=event, undo_event=undo_event)

    @final
    @contextmanager
    def _batch_context(self, name="Batch", **kwargs):
        # type: (str, Any) -> Iterator
        if self.__frozen_store is not None:
            error = "'{}' object is frozen and therefore cannot be mutated".format(
                type(self).__fullname__
            )
            raise RuntimeError(error)

        with self.app.require_write_context():
            with self.app._AbstractObject__write_context() as writer:
                with writer.batch_context(self, name, pmap(kwargs)):
                    yield

    @property
    def _is_frozen(self):
        # type: () -> bool
        return self.__frozen_store is not None

    @property
    @final
    def _subject(self):
        # type: (T_AbstractObject) -> Subject[T_AbstractObject]
        try:
            return self.__subject
        except AttributeError:
            if self.__frozen_store is not None:
                error = "'{}' object is frozen and therefore has no subject".format(
                    type(self).__fullname__
                )
                raise AttributeError(error)
            else:
                raise

    @property
    def pointer(self):
        # type: (T_AbstractObject) -> Pointer[T_AbstractObject]
        return self.__pointer

    @property
    @final
    def app(self):
        # type: () -> Application
        try:
            return self.__app
        except AttributeError:
            if self.__frozen_store is not None:
                error = (
                    "'{}' object is frozen and therefore does not belong to an "
                    "application"
                ).format(type(self).__fullname__)
                raise AttributeError(error)
            else:
                raise


# noinspection PyAbstractClass
class AbstractHistoryObject(AbstractObject):
    __slots__ = ("__descriptor",)

    def __init__(self, app, descriptor, *args, **kwargs):
        # type: (Application, HistoryDescriptor, Any, Any) -> None
        super(AbstractHistoryObject, self).__init__(app, descriptor, *args, **kwargs)
        assert_is_instance(descriptor, HistoryDescriptor, accept_subtypes=False)
        self.__descriptor = descriptor

    @classmethod
    def __init_state__(cls, args):
        return State(
            data=pmap({"index": 0, "commands": pvector([None])}),
            metadata=None,
            children_pointers=pmap(),
        )

    @classmethod
    def __freeze_data__(
        cls,
        data,  # type: T_Data
        metadata,  # type: T_Metadata
        child_freezer,  # type: Callable[[T_AbstractObject], T_AbstractObject]
    ):
        # type: (...) -> Tuple[T_Data, T_Metadata]
        return data, metadata

    @classmethod
    def __get_hash__(cls, state):
        # type: (State) -> int
        return hash(state.data)

    @classmethod
    def __get_eq__(cls, state, other_state):
        # type: (State, State) -> bool
        return state.data == other_state.data

    @classmethod
    def __locate_child__(cls, child, state):
        error = "could not locate child {}".format(child)
        raise ValueError(error)

    def __push_change__(self, change):
        # TODO: ignore when initializing context
        assert self
        assert change
        # print(change)  # TODO

    def flush(self):
        assert self
        # print("FLUSH!")  # TODO

    @property
    @final
    def _descriptor(self):
        return self.__descriptor

    @property
    def index(self):
        return self._get_state().data["index"]

    @property
    def commands(self):
        return self._get_state().data["commands"]
