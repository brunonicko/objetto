from gc import collect
from pytest import main, raises
from weakref import ref

from objetto.utils.pointer import Pointer


class Object(object):
    pass


def test_singleton():
    obj_a = Object()
    obj_b = Object()

    assert Pointer(obj_a) is Pointer(obj_a)
    assert Pointer(obj_b) is Pointer(obj_b)
    assert Pointer(obj_a) is not Pointer(obj_b)

    pointer_a = Pointer(obj_a)
    pointer_b = Pointer(obj_b)

    assert Pointer(obj_a) is pointer_a
    assert Pointer(obj_b) is pointer_b
    assert Pointer(obj_a) is not pointer_b
    assert Pointer(obj_b) is not pointer_a


def test_collect_obj():
    obj_a = Object()
    obj_b = Object()

    pointer_a = Pointer(obj_a)
    pointer_b = Pointer(obj_b)

    del obj_a
    collect()

    with raises(ReferenceError):
        _ = pointer_a.obj
    assert pointer_b.obj is obj_b

    del obj_b
    collect()

    with raises(ReferenceError):
        _ = pointer_b.obj


def test_collect_pointer():
    obj_a = Object()
    obj_b = Object()

    pointer_a = Pointer(obj_a)
    pointer_b = Pointer(obj_b)

    pointer_a_ref = ref(pointer_a)
    pointer_b_ref = ref(pointer_b)

    assert pointer_a_ref() is pointer_a
    assert pointer_b_ref() is pointer_b

    del pointer_a
    collect()

    assert pointer_a_ref() is None
    assert pointer_b_ref() is pointer_b

    del pointer_b
    collect()

    assert pointer_a_ref() is None
    assert pointer_b_ref() is None


if __name__ == "__main__":
    main()
