from gc import collect
from pytest import main, raises, mark
from collections import namedtuple
from threading import Thread
from random import randint

from attr import evolve
from pyrsistent import pmap

from objetto._structures import (
    Relationship,
    InitializedChange,
    StateChange,
    BatchChange,
    FrozenChange,
    State,
)
from objetto._descriptors import (
    ReactionDescriptor,
    HistoryDescriptor,
)
from objetto._application import Application
from objetto._constants import Phase
from objetto._objects import AbstractObject, AbstractHistoryObject
from objetto._exceptions import RevertException, RejectException
from objetto.utils.subject_observer import Observer


ValueChangedEvent = namedtuple("ValueChangedEvent", ("old_value", "new_value"))
ChildChangedEvent = namedtuple("ChildChangedEvent", ("old_child", "new_child"))


def reaction(func):
    return ReactionDescriptor(func=func, priority=None)


class SimpleHistoryObject(AbstractHistoryObject):
    __slots__ = ()


class ValueObject(AbstractObject):
    __slots__ = ("__initial_value",)

    history_a = HistoryDescriptor(type=SimpleHistoryObject, args=(), kwargs=pmap())

    def __init__(self, app, value=0, child=None):
        self.__initial_value = value
        super(ValueObject, self).__init__(app, value, child)

    def __getitem__(self, location):
        if location == "value":
            return self.value
        elif location == "child":
            return self.child
        else:
            error = "invalid location {}".format(repr(location))
            raise KeyError(error)

    @classmethod
    def __init_state__(cls, args):
        value, child = args["value"], args["child"]
        if child is not None:
            assert isinstance(child, ValueObject)
            if child.app is args["app"]:
                children_pointers = pmap(
                    {child.pointer: Relationship(historied=True, serialized=True)}
                )
            else:
                error = "child app mismatch"
                raise RuntimeError(error)
        else:
            children_pointers = pmap()
        return State(
            data=pmap({"value": value, "child": child}),
            metadata=None,
            children_pointers=children_pointers,
        )

    @classmethod
    def __locate_child__(cls, child, state):
        if child is state.data.child:
            return "child"
        error = "could not locate child {}".format(child)
        raise ValueError(error)

    @property
    def value(self):
        return self._get_state().data["value"]

    @value.setter
    def value(self, new_value):
        new_value = int(new_value)
        old_value = self.value

        old_state = self._get_state()
        new_state = evolve(old_state, data=old_state.data.set("value", new_value))

        self._set_state(
            new_state,
            ValueChangedEvent(old_value=old_value, new_value=new_value),
        )

    @property
    def child(self):
        return self._get_state().data["child"]

    @child.setter
    def child(self, new_child):
        if new_child is not None:
            assert isinstance(new_child, ValueObject)
            children_pointers = pmap(
                {new_child.pointer: Relationship(historied=True, serialized=True)}
            )
        else:
            children_pointers = pmap()
        old_state = self._get_state()
        old_child = self.child
        new_state = State(
            data=old_state.data.set("child", new_child),
            metadata=None,
            children_pointers=children_pointers,
        )
        self._set_state(
            new_state,
            ChildChangedEvent(old_child=old_child, new_child=new_child),
        )

    @reaction
    def __reaction(self, action, phase):
        if isinstance(action.change, BatchChange):
            return

        if action.source is self:
            assert self._Writer__acting

        if isinstance(action.change, StateChange):
            if phase is Phase.POST:
                if isinstance(action.change.event, ValueChangedEvent):
                    change = action.change
                    if action.locations == ("child",):
                        diff = change.event.new_value - change.event.old_value
                        self.value += diff
                    elif not action.locations:
                        if change.event.new_value == 999:
                            raise RejectException(
                                "invalid value 999",
                                action.uuid,
                                lambda: setattr(self, "value", 99),
                            )
        elif isinstance(action.change, InitializedChange):
            assert action.source is self
            assert action.sender is self
            if phase is Phase.PRE:
                with raises(RuntimeError):
                    _ = self.value
            elif phase is Phase.POST:
                assert self.value == self.__initial_value
        elif isinstance(action.change, FrozenChange):
            assert action.source is self
            assert action.sender is self
            if phase is Phase.PRE:
                assert not self._is_frozen()
            elif phase is Phase.POST:
                assert self._is_frozen()
                assert self.app is not None

    @reaction
    def __batch_reaction(self, action, phase):
        if isinstance(action.change, BatchChange):
            if action.change.name == "value":
                if phase is Phase.PRE:
                    assert self.value == action.change.kwargs["old_value"]
                    self.child.value = 2
                elif phase is Phase.POST:
                    assert self.value == action.change.kwargs["new_value"]
                    self.child.value = 3
            elif action.change.name == "set_value_to_1000":
                if phase is Phase.POST:
                    raise RejectException(
                        "set the value to 1000",
                        action.uuid,
                        lambda: setattr(self, "value", 1000),
                    )


class AlwaysFrozenValueObject(ValueObject):
    _ALWAYS_FROZEN = True


class ValueObjectObserver(Observer):

    def __init__(self):
        self.pre_data = {}
        self.post_data = {}
        self.pre_snapshots = []
        self.post_snapshots = []

    def __observe__(self, action, phase):
        if isinstance(action.change, StateChange):
            if phase is Phase.PRE:
                assert action.source.value == action.change.event.old_value
                self.pre_data[action.source] = action.change.event.new_value
            elif phase is Phase.POST:
                assert action.source.value == action.change.event.new_value
                self.post_data[action.source] = action.change.event.new_value
            else:
                raise AssertionError()


def test_class_properties():
    assert ValueObject._history_descriptor is not None
    assert ValueObject._history_descriptor_name == "history_a"

    assert len(ValueObject._reaction_descriptor_names) == 2
    assert len(ValueObject._reaction_descriptors) == 2


@mark.parametrize("thread_safe", (True, False))
def test_value(thread_safe):
    app = Application(thread_safe=thread_safe)
    observer = ValueObjectObserver()
    app_observer = ValueObjectObserver()

    with app.write_context():
        obj_a = ValueObject(app, 1)
        obj_b = ValueObject(app, 2)

        observer.start_observing(obj_a.subject)
        observer.start_observing(obj_b.subject)
        app_observer.start_observing(app.subject)

        assert obj_a.value == 1
        assert obj_b.value == 2

        obj_a.value = 3
        obj_b.value = 4

        assert obj_a.value == 3
        assert obj_b.value == 4

        assert not observer.pre_data
        assert not observer.post_data

        assert not app_observer.pre_data
        assert not app_observer.post_data

    assert observer.pre_data[obj_a] == 3
    assert observer.post_data[obj_a] == 3

    assert observer.pre_data[obj_b] == 4
    assert observer.post_data[obj_b] == 4

    assert app_observer.pre_data[obj_a] == 3
    assert app_observer.post_data[obj_a] == 3

    assert app_observer.pre_data[obj_b] == 4
    assert app_observer.post_data[obj_b] == 4


@mark.parametrize("thread_safe", (True, False))
def test_child(thread_safe):
    app = Application(thread_safe=thread_safe)
    with app.write_context():
        obj_a = ValueObject(app)
        obj_b = ValueObject(app)

        assert obj_a._get_parent() is None
        assert obj_b._get_parent() is None

        obj_a.child = obj_b

        assert obj_a._get_parent() is None
        assert obj_b._get_parent() is obj_a

        with raises(RuntimeError):
            obj_b.child = obj_a

        obj_c = ValueObject(app)

        with raises(RuntimeError):
            obj_c.child = obj_b

        obj_b.child = obj_c

        assert obj_a._get_parent() is None
        assert obj_b._get_parent() is obj_a
        assert obj_c._get_parent() is obj_b

        with raises(RuntimeError):
            obj_c.child = obj_a

        assert obj_a.child is obj_b
        assert obj_b.child is obj_c
        assert obj_c.child is None

        obj_d = ValueObject(app, child=obj_a)

        assert obj_d.child is obj_a
        assert obj_a._get_parent() is obj_d

        obj_d.value = 2
        obj_a.value = 2
        obj_b.value = 2
        obj_c.value = 2

        assert obj_d.value == 8
        assert obj_a.value == 6
        assert obj_b.value == 4
        assert obj_c.value == 2


@mark.parametrize("thread_safe", (True, False))
def test_prevent_write_while_reading(thread_safe):
    app = Application(thread_safe=thread_safe)
    with app.read_context():
        with raises(RuntimeError):
            with app.write_context():
                assert False


@mark.parametrize("thread_safe", (True, False))
def test_prevent_write_when_parent_not_in_memory(thread_safe):
    app = Application(thread_safe=thread_safe)
    with app.write_context():
        obj0 = ValueObject(app, 0)
        obj1 = ValueObject(app, 1, obj0)
        obj2 = ValueObject(app, 2, obj1)
        obj3 = ValueObject(app, 3, obj2)
        ValueObject(app, 4, obj3)

    collect()

    with app.write_context():
        with raises(RuntimeError):
            obj0.value = 1


@mark.parametrize("thread_safe", (True, False))
def test_pinned_hierarchy(thread_safe):
    app = Application(thread_safe=thread_safe)
    with app._AbstractObject__write_context() as writer:
        obj0 = ValueObject(app, 0)
        obj1 = ValueObject(app, 1, obj0)
        obj2 = ValueObject(app, 2, obj1)
        obj3 = ValueObject(app, 3, obj2)
        obj4 = ValueObject(app, 4, obj3)

        with writer._pinned_hierarcy_context(obj0):
            assert obj0._Writer__pinned_count == 1
            assert obj0._Writer__pinned_hierarchy == (obj0, obj1, obj2, obj3, obj4)
            assert obj1._Writer__pinned_count == 2
            assert obj1._Writer__pinned_hierarchy == (obj1, obj2, obj3, obj4)
            assert obj2._Writer__pinned_count == 2
            assert obj2._Writer__pinned_hierarchy == (obj2, obj3, obj4)
            assert obj3._Writer__pinned_count == 2
            assert obj3._Writer__pinned_hierarchy == (obj3, obj4)
            assert obj4._Writer__pinned_count == 2
            assert obj4._Writer__pinned_hierarchy == (obj4,)

            with writer._pinned_hierarcy_context(obj2):
                assert obj0._Writer__pinned_count == 1
                assert obj0._Writer__pinned_hierarchy == (obj0, obj1, obj2, obj3, obj4)
                assert obj1._Writer__pinned_count == 2
                assert obj1._Writer__pinned_hierarchy == (obj1, obj2, obj3, obj4)
                assert obj2._Writer__pinned_count == 3
                assert obj2._Writer__pinned_hierarchy == (obj2, obj3, obj4)
                assert obj3._Writer__pinned_count == 3
                assert obj3._Writer__pinned_hierarchy == (obj3, obj4)
                assert obj4._Writer__pinned_count == 3
                assert obj4._Writer__pinned_hierarchy == (obj4,)

                with raises(RuntimeError):
                    obj2.child = None

        assert obj0._Writer__pinned_count == 0
        assert obj0._Writer__pinned_hierarchy is None
        assert obj1._Writer__pinned_count == 0
        assert obj1._Writer__pinned_hierarchy is None
        assert obj2._Writer__pinned_count == 0
        assert obj2._Writer__pinned_hierarchy is None
        assert obj3._Writer__pinned_count == 0
        assert obj3._Writer__pinned_hierarchy is None
        assert obj4._Writer__pinned_count == 0
        assert obj4._Writer__pinned_hierarchy is None


@mark.parametrize("thread_safe", (True, False))
def test_batch(thread_safe):
    app = Application(thread_safe=thread_safe)
    with app.write_context():
        obj_b = ValueObject(app, 1)
        obj_a = ValueObject(app, 0, obj_b)

        with obj_a._batch_context("value", old_value=0, new_value=1):
            assert obj_b.value == 2
            obj_a.value = 1
        assert obj_b.value == 3


@mark.parametrize("thread_safe", (True, False))
def test_history_descriptor(thread_safe):

    with raises(TypeError):

        # noinspection PyAbstractClass
        class BadObject(AbstractObject):
            history_a = HistoryDescriptor(
                type=SimpleHistoryObject, args=(), kwargs=pmap()
            )
            history_b = HistoryDescriptor(
                type=SimpleHistoryObject, args=(), kwargs=pmap()
            )

        assert not BadObject

    # noinspection PyAbstractClass
    class GoodObject(ValueObject):
        history_a = None

    assert GoodObject._history_descriptor_name is None
    assert GoodObject._history_descriptor is None

    assert ValueObject._history_descriptor_name == "history_a"
    assert isinstance(ValueObject._history_descriptor, HistoryDescriptor)

    app = Application(thread_safe=thread_safe)
    with app.write_context():
        obj_a = ValueObject(app, 1)
        assert isinstance(obj_a.history_a, AbstractObject)
        assert isinstance(obj_a._get_history(), AbstractObject)
        assert obj_a._get_history() is obj_a.history_a

        obj_b = GoodObject(app, 2)
        assert obj_b.history_a is None
        assert obj_b._get_history() is None


def test_thread_safety():
    app = Application(thread_safe=True)
    total_value = [0]
    with app.write_context():
        obj = ValueObject(app)

    def reader(_i):
        with app.read_context():
            value = obj.value
            assert obj.value == value

    def writer(_i):
        with app.write_context():
            value = obj.value
            increment = randint(1, 10)
            obj.value += increment
            total_value[0] += increment
            assert obj.value == value + increment

    threads = []
    for i in range(100):
        if i % 3:
            reader_thread = Thread(target=reader, args=(i,))
            threads.append(reader_thread)
        if i % 2:
            writer_thread = Thread(target=writer, args=(i,))
            threads.append(writer_thread)

    for thread in threads:
        thread.start()
        thread.join()

    with app.read_context():
        assert obj.value == total_value[0]


@mark.parametrize("thread_safe", (True, False))
def test_frozen(thread_safe):
    app = Application(thread_safe=thread_safe)

    snapshot = app.take_snapshot()
    with app.read_context(snapshot):
        pass

    with app.write_context():
        obj0 = ValueObject(app, 0)
        obj1 = ValueObject(app, 1, obj0)
        obj2 = ValueObject(app, 2, obj1)
        obj3 = ValueObject(app, 3, obj2)
        obj4 = ValueObject(app, 4, obj3)

        assert not obj0._is_frozen()
        assert not obj1._is_frozen()
        assert not obj2._is_frozen()
        assert not obj3._is_frozen()
        assert not obj4._is_frozen()

        obj4._freeze()

        assert obj0._is_frozen()
        assert obj1._is_frozen()
        assert obj2._is_frozen()
        assert obj3._is_frozen()
        assert obj4._is_frozen()

        assert obj0.app is app
        assert obj1.app is app
        assert obj2.app is app
        assert obj3.app is app
        assert obj4.app is app

    with app.write_context():
        with raises(RuntimeError):
            obj0.value = 10
        with raises(RuntimeError):
            obj1.value = 10
        with raises(RuntimeError):
            obj2.value = 10
        with raises(RuntimeError):
            obj3.value = 10
        with raises(RuntimeError):
            obj4.value = 10

    with app.read_context():
        assert obj0._is_frozen()
        assert obj1._is_frozen()
        assert obj2._is_frozen()
        assert obj3._is_frozen()
        assert obj4._is_frozen()

        assert obj0.app is app
        assert obj1.app is app
        assert obj2.app is app
        assert obj3.app is app
        assert obj4.app is app

        assert obj0.value == 0
        assert obj1.value == 1
        assert obj2.value == 2
        assert obj3.value == 3
        assert obj4.value == 4


@mark.parametrize("thread_safe", (True, False))
def test_revert_exception(thread_safe):
    app = Application(thread_safe=thread_safe)

    with app.write_context():
        obj1 = ValueObject(app, 1)
        obj2 = ValueObject(app, 2)
        obj3 = ValueObject(app, 3)
        obj4 = ValueObject(app, 4)

    with app.read_context():
        assert obj1.value == 1
        assert obj2.value == 2
        assert obj3.value == 3
        assert obj4.value == 4

    with app.write_context():
        obj1.value = 11
        obj2.value = 22

        with app.write_context():
            obj3.value = 33
            obj4.value = 44
            raise RevertException()

        assert obj1.value == 11
        assert obj2.value == 22
        assert obj3.value == 3
        assert obj4.value == 4

    with app.read_context():
        assert obj1.value == 11
        assert obj2.value == 22
        assert obj3.value == 3
        assert obj4.value == 4

    with app.write_context(temporary=True):
        obj1.value = 1111
        obj2.value = 2222
        obj3.value = 3333
        obj4.value = 4444
        assert obj1.value == 1111
        assert obj2.value == 2222
        assert obj3.value == 3333
        assert obj4.value == 4444

    with app.read_context():
        assert obj1.value == 11
        assert obj2.value == 22
        assert obj3.value == 3
        assert obj4.value == 4


@mark.parametrize("thread_safe", (True, False))
def test_reject_action_exception(thread_safe):
    app = Application(thread_safe=thread_safe)

    with app.write_context():
        obj1 = ValueObject(app, 1)

    with app.read_context():
        assert obj1.value == 1

    with app.write_context():
        obj1.value = 999
        assert obj1.value == 99

    with app.read_context():
        assert obj1.value == 99


@mark.parametrize("thread_safe", (True, False))
def test_reject_batch_exception(thread_safe):
    app = Application(thread_safe=thread_safe)

    with app.write_context():
        obj1 = ValueObject(app, 1)

    with app.read_context():
        assert obj1.value == 1

    with app.write_context():
        with obj1._batch_context("set_value_to_1000"):
            obj1.value = 10
            assert obj1.value == 10
        assert obj1.value == 1000

    with app.read_context():
        assert obj1.value == 1000


@mark.parametrize("thread_safe", (True, False))
def test_always_frozen(thread_safe):
    app = Application(thread_safe=thread_safe)

    with app.write_context():
        obj1 = ValueObject(app, 0)
        assert not obj1._is_frozen()
        assert obj1.app is app
        obj1.value = 1

        obj2 = AlwaysFrozenValueObject(app, 2, child=obj1)
        assert obj2.child is obj1
        assert obj2._is_frozen()
        assert obj2.app is app

        assert obj1._is_frozen()
        assert obj1.app is app

    with app.read_context():
        assert obj2.child is obj1
        assert obj2._is_frozen()
        assert obj2.app is app

        assert obj1._is_frozen()
        assert obj1.app is app
        assert obj1.value == 1


def test_pointer():
    app = Application()

    with app.write_context():
        obj1 = ValueObject(app, 1)
        obj2 = ValueObject(app, 2)

    assert obj1.pointer.obj is obj1
    assert obj2.pointer.obj is obj2


if __name__ == "__main__":
    main()
