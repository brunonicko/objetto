# -*- coding: utf-8 -*-

import inspect
from abc import abstractmethod
from typing import TYPE_CHECKING
from contextlib import contextmanager
from weakref import ref

from six import with_metaclass, iteritems, raise_from
from pyrsistent import pmap, pvector

from .utils.base import BaseMeta, Base, final
from .utils.subject_observer import Subject
from .utils.type_checking import assert_is_instance
from .utils.pointer import Pointer
from ._application import Application, resolve_history
from ._descriptors import ReactionDescriptor, HistoryDescriptor
from ._structures import Store, State

if TYPE_CHECKING:
    from typing import Any, Dict, Hashable, Optional, Iterator

    from ._structures import Storage

__all__ = [
    "AbstractObjectMeta",
    "AbstractObject",
    "AbstractHistoryObject",
]


# noinspection PyAbstractClass
class AbstractObjectMeta(BaseMeta):

    def __init__(cls, name, bases, dct):
        super(AbstractObjectMeta, cls).__init__(name, bases, dct)

        always_frozen = None  # type: Any
        reaction_descriptors = {}  # type: Dict[str, ReactionDescriptor]
        history_descriptors = {}  # type: Dict[str, HistoryDescriptor]
        for base in reversed(inspect.getmro(cls)):
            for member_name, member in iteritems(base.__dict__):
                if member_name == "_ALWAYS_FROZEN":
                    always_frozen = member

                history_descriptors.pop(member_name, None)
                reaction_descriptors.pop(member_name, None)

                if isinstance(member, ReactionDescriptor):
                    reaction_descriptors[member_name] = member
                elif isinstance(member, HistoryDescriptor):
                    history_descriptors[member_name] = member

        # Verify if '_ALWAYS_FROZEN' is valid.
        if type(always_frozen) is not bool:
            if always_frozen is None:
                error = "'{}._ALWAYS_FROZEN' not declared or None".format(
                    cls.__name__
                )
            else:
                error = "'{}._ALWAYS_FROZEN' has to be a boolean, not '{}'".format(
                    cls.__name__, type(always_frozen).__name__
                )
            raise TypeError(error)

        # Store history descriptor.
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
        return cls.__namespace__.__history_descriptor_name

    @property
    @final
    def _history_descriptor(cls):
        return cls.__namespace__.__history_descriptor

    @property
    @final
    def _reaction_descriptor_names(cls):
        return cls.__namespace__.__reaction_descriptor_names

    @property
    @final
    def _reaction_descriptors(cls):
        return cls.__namespace__.__reaction_descriptors


# noinspection PyAbstractClass
class AbstractObject(with_metaclass(AbstractObjectMeta, Base)):

    _ALWAYS_FROZEN = False

    __slots__ = (
        "__weakref__",
        "__pointer",
        "__subject",
        "__app",
        "__store",
        "_Writer__acting",
        "_Writer__pinned_count",
        "_Writer__pinned_hierarchy",
    )

    def __init__(self, app, *args, **kwargs):
        assert_is_instance(app, Application, accept_subtypes=False)

        with app.require_write_context():
            self.__pointer = Pointer(self)
            self.__subject = Subject(self)
            self.__app = app
            self.__store = None

            self._Writer__acting = False
            self._Writer__pinned_count = 0
            self._Writer__pinned_hierarchy = None

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
            init_args = {"app": app}  # type: Dict[str, Any]
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

            with app._AbstractObject__write_context() as writer:
                history_descriptor = type(self)._history_descriptor
                if history_descriptor is not None:
                    history_provider_ref = ref(self)
                    history = history_descriptor.type(app, history_descriptor)
                else:
                    history_provider_ref = None
                    history = None

                state = type(self).__init_state__(init_args)
                store = Store(
                    state=state,
                    parent_ref=None,
                    history_provider_ref=history_provider_ref,
                    last_parent_history_ref=None,
                    history=history,
                    frozen=False,
                )
                writer.init_store(self, store)

                self.__post_init__(init_args)

                if type(self)._ALWAYS_FROZEN:
                    self._freeze()

    @abstractmethod
    def __getitem__(self, location):
        # type: (Hashable) -> Any
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def __init_state__(cls, args):
        # type: (Dict[str, Any]) -> State
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def __locate_child__(cls, child, state):
        # type: (AbstractObject, State) -> Hashable
        raise NotImplementedError()

    def __post_init__(self, args):
        # type: (Dict[str, Any]) -> None
        pass

    @final
    def __get_store(self, storage):
        # type: (Storage[Pointer[AbstractObject], Store]) -> Store
        try:
            return storage.query(self.pointer)
        except KeyError:
            error = "'{}' object not initialized".format(
                type(self).__fullname__
            )
            exc = RuntimeError(error)
            raise_from(exc, None)
            raise exc

    @final
    def _freeze(self):
        # type: () -> None
        with self.__app.require_write_context():
            with self.__app._AbstractObject__write_context() as writer:
                writer.freeze(self)

    @final
    def _get_parent(self):
        # type: () -> Optional[AbstractObject]
        with self.__app.require_context():
            with self.__app._AbstractObject__read_context() as storage:
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
        with self.__app.require_context():
            with self.__app._AbstractObject__read_context() as storage:
                return resolve_history(self, storage)

    @final
    def _get_location(self, child):
        # type: (AbstractObject) -> Hashable
        with self.__app.require_context():
            return type(self).__locate_child__(child, self._get_state())

    @final
    def _is_frozen(self):
        # type: (AbstractObject) -> bool
        with self.__app.require_context():
            with self.__app._AbstractObject__read_context() as storage:
                store = self.__get_store(storage)
                return store.frozen

    @final
    def _get_state(self):
        # type: () -> State
        with self.__app.require_context():
            with self.__app._AbstractObject__read_context() as storage:
                store = self.__get_store(storage)
                return store.state

    @final
    def _set_state(self, new_state, event=None, undo_event=None):
        # type: (State, Any, Any) -> None
        with self.__app.require_write_context():
            with self.__app._AbstractObject__write_context() as writer:
                writer.act(self, new_state, event=event, undo_event=undo_event)

    @final
    @contextmanager
    def _batch_context(self, name="Batch", **kwargs):
        # type: (str, Any) -> Iterator
        with self.__app.require_write_context():
            with self.__app._AbstractObject__write_context() as writer:
                with writer.batch_context(self, name, pmap(kwargs)):
                    yield

    @property
    def pointer(self):
        # type: () -> Pointer
        return self.__pointer

    @property
    @final
    def subject(self):
        # type: () -> Subject
        return self.__subject

    @property
    @final
    def app(self):
        # type: () -> Application
        return self.__app


# noinspection PyAbstractClass
class AbstractHistoryObject(AbstractObject):
    __slots__ = ("__descriptor",)

    def __init__(self, app, descriptor, *args, **kwargs):
        # type: (Application, HistoryDescriptor, Any, Any) -> None
        super(AbstractHistoryObject, self).__init__(app, descriptor, *args, **kwargs)
        assert_is_instance(descriptor, HistoryDescriptor, accept_subtypes=False)
        self.__descriptor = descriptor

    def __getitem__(self, location):
        return self.commands[location]

    @classmethod
    def __init_state__(cls, args):
        return State(
            data=pmap({"index": 0, "commands": pvector([None])}),
            metadata=None,
            children_pointers=pmap(),
        )

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
