import pytest

from objetto.core import _REACTION_TAG, Hierarchy, context, reaction, reactions
from objetto.objects import ValueObject
from objetto import exceptions


def test_value():
    hierarchy = Hierarchy()
    with context() as ctx:
        obj_a = ValueObject(3, hierarchy)
        assert obj_a.value == 3
        obj_a.value = 10
        assert obj_a.value == 10
        snap = ctx.get_snapshot()

    with context(snap) as ctx:
        obj_b = ValueObject(100, hierarchy)
        obj_a.value = obj_b
        assert ctx.get_snapshot().get_children(obj_a, hierarchy) == (obj_b,)


def test_parent_checks():
    hierarchy = Hierarchy()
    with context() as ctx:
        obj_a = ValueObject("a", hierarchy)
        obj_b = ValueObject("b", hierarchy)
        obj_c = ValueObject("c", hierarchy)

        obj_a.value = obj_b
        assert ctx.get_snapshot().get_parent(obj_b, hierarchy) is obj_a

        with pytest.raises(exceptions.AlreadyParentedError):
            obj_c.value = obj_b


def test_reactions():

    class MyValueObject(ValueObject):

        @reaction
        def _do_stuff(self, action, phase):
            print(f"----{action}-{phase}-----")

    assert getattr(MyValueObject._do_stuff, _REACTION_TAG, False) is True
    assert reactions(MyValueObject)

    with context() as ctx:
        hierarchy = Hierarchy()
        obj_a = MyValueObject("a", hierarchy)
        obj_b = MyValueObject(obj_a, hierarchy)
        obj_c = MyValueObject(obj_b, hierarchy)
        obj_d = MyValueObject(obj_c, hierarchy)

        obj_a.value = "A"


if __name__ == "__main__":
    pytest.main()
