# -*- coding: utf-8 -*-

from collections import Counter, namedtuple
from six import with_metaclass
from slotted import SlottedSequence, SlottedHashable

from ._base_model import BaseModelMeta, BaseModel
from ._broadcaster import EventListenerMixin
from ._partial import Partial
from ._events import SequenceInsertEvent, SequencePopEvent


SequenceOptions = namedtuple("SequenceOptions", "parent history")


class SequenceModelMeta(BaseModelMeta):
    pass


class SequenceModel(
    with_metaclass(
        SequenceModelMeta,
        EventListenerMixin,
        SlottedHashable,
        SlottedSequence,
        BaseModel,
    )
):
    __slots__ = ("__options", "__state")
    __event_types__ = frozenset({SequenceInsertEvent, SequencePopEvent})

    def __init__(self, parent=True, history=True):
        self.__options = SequenceOptions(parent=bool(parent), history=bool(history))

    def __hash__(self):
        return object.__hash__(self)

    def __getitem__(self, item):
        return self.__state__[item]

    def __len__(self):
        return len(self.__state__)

    def __react__(self, model, event, phase):
        pass

    def _insert(self, index, *values):

        # Normalize index
        state_len = len(self.__state__)
        if index < 0:
            index += state_len
        if index < 0:
            index = 0
        elif index > state_len:
            index = state_len

        # Count children in values
        child_count = Counter()
        for value in values:
            if isinstance(value, BaseModel):
                if self.__options.parent:
                    child_count[value] += 1

        redo_children = self.__hierarchy__.prepare_children_updates(child_count)
        undo_children = ~redo_children

        redo = Partial(self.__hierarchy__.update_children, redo_children) + Partial(
            self.__state__.__setitem__, slice(index, index), values
        )
        undo = Partial(self.__hierarchy__.update_children, undo_children) + Partial(
            self.__state__.__delitem__, slice(index, index + len(values))
        )

        redo_event = SequenceInsertEvent(redo_children, undo_children, index, values)
        undo_event = SequencePopEvent(undo_children, redo_children, index, values)

        self.__dispatch__("Insert Values", redo, redo_event, undo, undo_event)

    def _pop(self, index=-1, count=1):

        # Normalize index
        state_len = len(self.__state__)
        if index < 0:
            index += state_len

        # Check index
        if index < 0 or index >= state_len:
            raise IndexError("pop index out of range")

        # Check count
        if count < 1 or index + count > state_len:
            raise ValueError("pop count out of range")

        # Get values
        values = self.__state__[index : index + count]

        # Count children in values
        child_count = Counter()
        for value in values:
            if isinstance(value, BaseModel):
                if self.__options.parent:
                    child_count[value] -= 1

        redo_children = self.__hierarchy__.prepare_children_updates(child_count)
        undo_children = ~redo_children

        redo = Partial(self.__hierarchy__.update_children, redo_children) + Partial(
            self.__state__.__delitem__, slice(index, index + count)
        )
        undo = Partial(self.__hierarchy__.update_children, undo_children) + Partial(
            self.__state__.__setitem__, slice(index, index), values
        )

        redo_event = SequencePopEvent(redo_children, undo_children, index, values)
        undo_event = SequenceInsertEvent(undo_children, redo_children, index, values)

        self.__dispatch__("Pop Values", redo, redo_event, undo, undo_event)

    @property
    def __state__(self):
        try:
            state = self.__state
        except AttributeError:
            state = self.__state = []
        return state

    @property
    def _options(self):
        return self.__options
