import pytest

from objetto.core import Hierarchy, context
from objetto.objects import ValueObject


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


if __name__ == "__main__":
    pytest.main()
