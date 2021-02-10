# -*- coding: utf-8 -*-
"""Reactions."""

from collections import Counter as ValueCounter
from collections import defaultdict
from typing import TYPE_CHECKING, TypeVar, cast

from six import iteritems

from ._applications import Phase, RejectChangeException
from ._bases import MISSING, final
from ._changes import BaseAtomicChange, Update
from ._constants import BASE_STRING_TYPES, INTEGER_TYPES
from ._data import InteractiveDictData
from ._objects import UNIQUE_ATTRIBUTES_METADATA_KEY, BaseReaction, Object
from ._states import DictState
from .utils.reraise_context import ReraiseContext
from .utils.type_checking import assert_is_callable, assert_is_instance

if TYPE_CHECKING:
    from typing import Any, Callable, Counter, Dict, FrozenSet, Mapping, Optional, Union

    from ._applications import Action
    from ._objects import BaseObject

    if False and BaseObject:  # for PyCharm
        pass

    ReactionDecorator = Callable[
        [Callable[["_BO", Action, Phase], None]], "CustomReaction"
    ]

__all__ = [
    "reaction",
    "CustomReaction",
    "UniqueAttributes",
    "LimitChildren",
    "Limit",
]


_BO = TypeVar("_BO", bound="BaseObject")


# noinspection PyAbstractClass
def reaction(
    func=None,  # type: Optional[Callable[[_BO, Action, Phase], None]]
    priority=None,  # type: Optional[int]
):
    # type: (...) -> Union[CustomReaction, ReactionDecorator]
    """
    Decorates an object's method into a custom reaction.
    Reaction methods are called automatically when an action propagates up the
    hierarchy during the 'PRE' and 'POST' phases.

    . code:: python

        >>> from objetto.applications import Application
        >>> from objetto.objects import Object, attribute
        >>> from objetto.reactions import reaction

        >>> class MyObject(Object):
        ...     value = attribute(int, default=0)
        ...
        ...     @reaction
        ...     def __on_received(self, action, phase):
        ...         if not self._initializing:
        ...             print(("LAST -", action.change.name, phase))
        ...
        ...     @reaction(priority=1)
        ...     def __on_received_first(self, action, phase):
        ...         if not self._initializing:
        ...             print(("FIRST -", action.change.name, phase))
        ...
        >>> app = Application()
        >>> my_obj = MyObject(app)
        >>> my_obj.value = 42
        ('FIRST -', 'Update Attributes', <Phase.PRE: 'PRE'>)
        ('LAST -', 'Update Attributes', <Phase.PRE: 'PRE'>)
        ('FIRST -', 'Update Attributes', <Phase.POST: 'POST'>)
        ('LAST -', 'Update Attributes', <Phase.POST: 'POST'>)

    :param func: Method to be decorated or `None`.
    :type func: function

    :param priority: Priority.
    :type priority: int or None

    :return: Decorated custom reaction method or decorator.
    :rtype: objetto.reactions.CustomReaction
    """

    def _reaction(func_):
        # type: (Callable[[_BO, Action, Phase], None]) -> CustomReaction
        """
        Reaction method decorator.

        :param func_: Method function.
        :return: Custom reaction object.
        """
        if isinstance(func_, CustomReaction):
            if func_.priority == priority:
                return func_
            func_ = func_.func
        return CustomReaction(func_, priority=priority)

    if func is not None:
        return _reaction(func)
    else:
        return _reaction


@final
class CustomReaction(BaseReaction):
    """
    Custom method-like that gets called whenever an action is sent through the object.

    Inherits from:
      - :class:`objetto.bases.BaseReaction`

    :param func: Function.
    :type func: function

    :param priority: Priority.
    :type priority: int or None
    """

    __slots__ = ("__func", "__priority")

    def __init__(self, func, priority=None):
        # type: (Callable[[_BO, Action, Phase], None], Optional[int]) -> None
        super(CustomReaction, self).__init__()

        # 'func'
        with ReraiseContext(TypeError):
            assert_is_callable(func)

        # 'priority'
        if priority is not None:
            with ReraiseContext(TypeError, "'priority' parameter"):
                assert_is_instance(priority, INTEGER_TYPES)

        self.__func = func
        self._priority = priority

    def __call__(self, obj, action, phase):
        """
        Run function.

        :param obj: Object.
        :type obj: objetto.bases.BaseObject

        :param action: Action.
        :type action: objetto.objects.Action

        :param phase: Phase.
        :type phase: `objetto.constants.PRE` or :data:`objetto.constants.POST`
        """
        self.func(obj, action, phase)

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[str, Any]
        """
        dct = super(CustomReaction, self).to_dict()
        dct.update(
            {
                "func": self.func,
            }
        )
        return dct

    @property
    def func(self):
        # type: () -> Callable[[_BO, Action, Phase], None]
        """
        Function.

        :rtype: function
        """
        return self.__func


class UniqueAttributes(BaseReaction):
    """
    Asserts that children have unique attributes within a collection.
    Initialize with attribute names and optional incrementer functions.

    Inherits from:
      - :class:`objetto.bases.BaseReaction`

    :param names: Attribute names.
    :type names: str

    :param incrementers: Incrementer functions.
    :type incrementers: function
    """

    __slots__ = ("__names", "__incrementers")

    def __init__(self, *names, **incrementers):
        # type: (str, Callable[[Any, FrozenSet[Any]], Any]) -> None
        super(UniqueAttributes, self).__init__()

        # Check names.
        for name in names:
            assert_is_instance(name, BASE_STRING_TYPES)
        # noinspection PyTypeChecker
        all_names = frozenset(names).union(incrementers)
        if not all_names:
            error = "no attribute names provided"
            raise ValueError(error)

        # Check incrementers.
        # noinspection PyTypeChecker
        all_incrementers = DictState(
            incrementers
        )  # type: DictState[str, Callable[[Any, FrozenSet[Any]], Any]]
        for name, incrementer in iteritems(all_incrementers):
            if not callable(incrementer):
                error = "expected a callable incrementer for '{}', got '{}'".format(
                    name, type(incrementer).__name__
                )
                raise TypeError(error)

        self.__names = all_names  # type: FrozenSet[str]
        self.__incrementers = all_incrementers

    def __call__(self, obj, action, phase):
        # type: (_BO, Action, Phase) -> None
        """
        React to new children or children's attribute changes.

        :param obj: Object.
        :type obj: objetto.bases.BaseObject

        :param action: Action.
        :type action: objetto.objects.Action

        :param phase: Phase.
        :type phase: `objetto.constants.PRE` or :data:`objetto.constants.POST`
        """

        # Ignore non-atomic changes.
        if not isinstance(action.change, BaseAtomicChange):
            return

        # Adopting or releasing children.
        if not action.locations:

            # Old children.
            if action.change.old_children:

                # After releasing, update metadata.
                if phase is phase.POST:
                    with obj.app.__.update_metadata_context(obj) as (read, update):

                        # Get existing cache.
                        metadata = read()
                        if UNIQUE_ATTRIBUTES_METADATA_KEY not in metadata:
                            cache = InteractiveDictData(
                                ()
                            )  # type: InteractiveDictData[str, Any]
                        else:
                            cache = metadata[UNIQUE_ATTRIBUTES_METADATA_KEY]

                        # For every old child, remove values from cache.
                        for child in action.change.old_children:
                            if not isinstance(child, Object):
                                continue
                            for name in self.__names:
                                if hasattr(child, name):
                                    value = getattr(child, name)
                                    try:
                                        hash(value)
                                    except TypeError:
                                        continue
                                    if name in cache:
                                        cache = cache.set(
                                            name, cache[name].discard(value)
                                        )

                        # Update metadata.
                        update({UNIQUE_ATTRIBUTES_METADATA_KEY: cache})

            # New children.
            if action.change.new_children:

                # Before adopting.
                if phase is Phase.PRE:
                    children = frozenset(
                        c for c in action.change.new_children if isinstance(c, Object)
                    )
                    all_new_values = self.__react(obj, children)

                    # Update children with new values.
                    for child, new_values in iteritems(all_new_values):
                        child.update(new_values)

                # After adopting, update metadata.
                elif phase is phase.POST:
                    with obj.app.__.update_metadata_context(obj) as (read, update):

                        # Get existing cache.
                        metadata = read()
                        if UNIQUE_ATTRIBUTES_METADATA_KEY not in metadata:
                            cache = InteractiveDictData()
                        else:
                            cache = metadata[UNIQUE_ATTRIBUTES_METADATA_KEY]

                        # For every new child, add values to cache.
                        for child in action.change.new_children:
                            if not isinstance(child, Object):
                                continue
                            for name in self.__names:
                                if hasattr(child, name):
                                    value = getattr(child, name)
                                    try:
                                        hash(value)
                                    except TypeError:
                                        continue
                                    if name not in cache:
                                        cache = cache.set(
                                            name,
                                            InteractiveDictData({value: child}),
                                        )
                                    else:
                                        cache = cache.set(
                                            name, cache[name].set(value, child)
                                        )

                        # Update metadata.
                        update({UNIQUE_ATTRIBUTES_METADATA_KEY: cache})

        # Changes in existing children.
        elif len(action.locations) == 1:
            if isinstance(action.change, Update):

                # Before changes.
                if phase is Phase.PRE:
                    child = cast("Object", action.sender)
                    children = frozenset((child,))
                    all_new_values = self.__react(
                        obj, children, {child: action.change.new_values}
                    )
                    if child in all_new_values:
                        new_values = all_new_values[child]
                        new_input_values = dict(
                            (name, new_values.get(name, value))
                            for name, value in iteritems(action.change.new_values)
                        )

                        # Callback to update children with new values.
                        def callback():
                            child.update(new_input_values)

                        # Reject changes and run callback.
                        raise RejectChangeException(
                            "attributes not unique", action.change, callback
                        )

                # After changes, update metadata.
                elif phase is Phase.POST:
                    with obj.app.__.update_metadata_context(obj) as (read, update):

                        # Get existing cache.
                        metadata = read()
                        if UNIQUE_ATTRIBUTES_METADATA_KEY not in metadata:
                            cache = InteractiveDictData()
                        else:
                            cache = metadata[UNIQUE_ATTRIBUTES_METADATA_KEY]

                        # Update cache.
                        child = action.sender
                        if isinstance(child, Object):
                            for name, new_value in iteritems(action.change.new_values):
                                old_value = action.change.old_values.get(name, MISSING)
                                if name not in cache:
                                    cache = cache.set(
                                        name,
                                        InteractiveDictData({new_value: child}),
                                    )
                                else:
                                    cache = cache.set(
                                        name,
                                        cache[name]
                                        .discard(old_value)
                                        .set(new_value, child),
                                    )

                            # Update metadata.
                            update({UNIQUE_ATTRIBUTES_METADATA_KEY: cache})

    def __react(
        self,
        obj,  # type: _BO
        children,  # type: FrozenSet[Object]
        child_new_values=None,  # type: Optional[Dict[Object, Mapping[str, Any]]]
    ):
        # type: (...) -> Dict[Object, Dict[str, Any]]
        """React and return new values."""

        # Get children and existing children.
        children = frozenset(c for c in children if isinstance(c, Object))
        existing_children = frozenset(c for c in obj._children if isinstance(c, Object))
        _child_new_values = child_new_values or {}

        # Build a dictionary with existing values.
        all_values = defaultdict(ValueCounter)  # type: Dict[str, Counter[Any]]
        for child in existing_children.union(children):

            # Get value.
            for name in self.names:

                # Get new value if existing child is changing.
                if child in _child_new_values:
                    if name in _child_new_values[child]:
                        all_values[name][_child_new_values[child][name]] += 1
                        continue

                # Get existing value.
                all_values[name][getattr(child, name)] += 1

        # Prepare dict to store new values.
        all_new_values = defaultdict(dict)  # type: Dict[Object, Dict[str, Any]]

        # Check children's values for collisions.
        for child in children:
            for name in self.names:

                # If specifying children new values, skip the ones not specified.
                if child_new_values is not None:
                    if child not in child_new_values:
                        continue
                    if name not in child_new_values[child]:
                        continue
                    value = child_new_values[child][name]
                else:
                    # Get existing values and child's value for this attribute.
                    value = getattr(child, name)

                # Get all values for this attribute.
                values, values_counter = (
                    frozenset(v for v in all_values[name] if all_values[name][v]),
                    all_values[name],
                )

                # There's a collision.
                if values_counter.get(value, 0) > 1:

                    # Prepare error message.
                    error = ("another object already has '{}' set to {}").format(
                        name, repr(value)
                    )

                    # Try to use incrementer to get a unique value.
                    if name in self.incrementers:
                        incrementer = self.incrementers[name]
                        new_value = incrementer(value, values)

                        # Incrementer was able to provide a unique value, so
                        # keep track of it and update all values dictionary.
                        all_values[name][value] -= 1
                        if values_counter.get(new_value, 0) < 1:
                            all_new_values[child][name] = new_value
                            all_values[name][new_value] += 1
                            continue

                        # Incrementer failed to make it unique, add to the error
                        # message and error out as a runtime error.
                        else:
                            error += (
                                ", incrementer {} failed to make it unique "
                                "(result was {})"
                            ).format(incrementer, repr(new_value))
                            raise RuntimeError(error)

                    # Not unique, raise value error.
                    raise ValueError(error)

        return all_new_values

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[str, Any]
        """
        dct = super(UniqueAttributes, self).to_dict()
        dct.update(
            {
                "names": self.names,
                "incrementers": self.incrementers,
            }
        )
        return dct

    @property
    def names(self):
        # type: () -> FrozenSet[str]
        """
        Names.

        :rtype: tuple[str]
        """
        return self.__names

    @property
    def incrementers(self):
        # type: () -> DictState[str, Callable]
        """
        Incrementer functions.

        :rtype: objetto.states.DictState[str, function]
        """
        return self.__incrementers


class LimitChildren(BaseReaction):
    """
    Limit the number of children.

    Inherits from:
      - :class:`objetto.bases.BaseReaction`

    :param minimum: Minimum.
    :type minimum: int or None

    :param maximum: Maximum.
    :type maximum: int or None
    """

    __slots__ = ("__minimum", "__maximum")

    def __init__(self, minimum=None, maximum=None):
        # type: (Optional[int], Optional[int]) -> None
        super(LimitChildren, self).__init__()

        if minimum is not None:
            minimum = int(minimum)
            if minimum < 0:
                error = "minimum cannot be less than zero"
                raise ValueError(error)
        if maximum is not None:
            maximum = int(maximum)

        self.__minimum = minimum
        self.__maximum = maximum

    def __call__(self, obj, action, phase):
        # type: (_BO, Action, Phase) -> None
        """
        React to atomic changes.

        :param obj: Object.
        :type obj: objetto.bases.BaseObject

        :param action: Action.
        :type action: objetto.objects.Action

        :param phase: Phase.
        :type phase: `objetto.constants.PRE` or :data:`objetto.constants.POST`
        """

        # Ignore non-atomic changes.
        if not isinstance(action.change, BaseAtomicChange):
            return

        if len(action.locations) == 0:
            if phase is Phase.PRE:
                if action.change.new_children or action.change.old_children:
                    current_len = len(obj._children)
                    new_len = current_len + (
                        len(action.change.new_children)
                        - len(action.change.old_children)
                    )

                    # Growing, check for maximum.
                    if self.maximum is not None and new_len > self.maximum:
                        error_msg = (
                            "tried to add too many children (maximum is {})"
                        ).format(self.maximum)
                        raise ValueError(error_msg)

                    # Shrinking, check for minimum.
                    elif self.minimum is not None and current_len >= self.minimum:
                        if new_len < self.minimum:
                            history = obj._history
                            if history is None or not history.undoing:
                                error_msg = (
                                    "tried to remove too many children (minimum is {})"
                                ).format(self.minimum)
                                raise ValueError(error_msg)

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[str, Any]
        """
        dct = super(LimitChildren, self).to_dict()
        dct.update(
            {
                "minimum": self.minimum,
                "maximum": self.maximum,
            }
        )
        return dct

    @property
    def minimum(self):
        # type: () -> Optional[int]
        """
        Minimum.

        :rtype: int or None
        """
        return self.__minimum

    @property
    def maximum(self):
        # type: () -> Optional[int]
        """
        Maximum.

        :rtype: int or None
        """
        return self.__maximum


class Limit(BaseReaction):
    """
    Limit the number of values.

    Inherits from:
      - :class:`objetto.bases.BaseReaction`

    :param minimum: Minimum.
    :type minimum: int or None

    :param maximum: Maximum.
    :type maximum: int or None
    """

    __slots__ = ("__minimum", "__maximum")

    def __init__(self, minimum=None, maximum=None):
        # type: (Optional[int], Optional[int]) -> None
        super(Limit, self).__init__()

        if minimum is not None:
            minimum = int(minimum)
            if minimum < 0:
                error = "minimum cannot be less than zero"
                raise ValueError(error)
        if maximum is not None:
            maximum = int(maximum)

        self.__minimum = minimum
        self.__maximum = maximum

    def __call__(self, obj, action, phase):
        # type: (_BO, Action, Phase) -> None
        """
        React to atomic changes.

        :param obj: Object.
        :param action: Action.
        :param phase: Phase.
        """

        # Ignore non-atomic changes.
        if not isinstance(action.change, BaseAtomicChange):
            return

        if len(action.locations) == 0:
            if phase is Phase.PRE:
                current_len = len(action.change.old_state)
                new_len = len(action.change.new_state)

                # Growing, check for maximum.
                if self.maximum is not None and new_len > self.maximum:
                    error_msg = ("tried to add too many values (maximum is {})").format(
                        self.maximum
                    )
                    raise ValueError(error_msg)

                # Shrinking, check for minimum.
                elif self.minimum is not None and current_len >= self.minimum:
                    if new_len < self.minimum:
                        history = obj._history
                        if history is None or not history.undoing:
                            error_msg = (
                                "tried to remove too many values (minimum is {})"
                            ).format(self.minimum)
                            raise ValueError(error_msg)

    def to_dict(self):
        # type: () -> Dict[str, Any]
        """
        Convert to dictionary.

        :return: Dictionary.
        :rtype: dict[str, Any]
        """
        dct = super(Limit, self).to_dict()
        dct.update(
            {
                "minimum": self.minimum,
                "maximum": self.maximum,
            }
        )
        return dct

    @property
    def minimum(self):
        # type: () -> Optional[int]
        """
        Minimum.

        :rtype: int or None
        """
        return self.__minimum

    @property
    def maximum(self):
        # type: () -> Optional[int]
        """
        Maximum.

        :rtype: int or None
        """
        return self.__maximum
