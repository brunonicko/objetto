

from pickle import loads, dumps
from copy import copy, deepcopy
from gc import collect

from pytest import main, raises, mark

from objetto.utils.storage import AbstractStorage, Storage, Evolver


def test_abstraction():
    assert issubclass(Storage, AbstractStorage)
    assert issubclass(Evolver, AbstractStorage)
    with raises(TypeError):
        AbstractStorage()


@mark.parametrize("abstract_storage_cls", (Storage, Evolver))
def test_common(abstract_storage_cls):
    class Obj(object):
        pass

    obj_a = Obj()
    obj_b = Obj()
    abstract_storage = abstract_storage_cls()

    abstract_storage = abstract_storage.update({obj_a: 1})
    assert abstract_storage.query(obj_a) == 1
    assert abstract_storage.get(obj_b) is None

    abstract_storage = abstract_storage.update({obj_b: 2})
    assert abstract_storage.query(obj_a) == 1
    assert abstract_storage.query(obj_b) == 2

    assert len(abstract_storage.to_dict()) == 2
    assert abstract_storage.to_dict() == {obj_a: 1, obj_b: 2}


def test_storage_garbage_collection():
    class Obj(object):
        pass

    obj_a = Obj()
    obj_b = Obj()
    obj_c = Obj()
    storage_a = Storage({obj_a: 1})
    storage_b = storage_a.update({obj_b: 2})
    storage_c = storage_b.update({obj_c: 3})

    del obj_a
    collect()

    assert storage_a.to_dict() == {}
    assert storage_b.to_dict() == {obj_b: 2}
    assert storage_c.to_dict() == {obj_b: 2, obj_c: 3}

    del obj_b
    collect()

    assert storage_a.to_dict() == {}
    assert storage_b.to_dict() == {}
    assert storage_c.to_dict() == {obj_c: 3}

    del obj_c
    collect()

    assert storage_a.to_dict() == {}
    assert storage_b.to_dict() == {}
    assert storage_c.to_dict() == {}


def test_evolver_garbage_collection():
    class Obj(object):
        pass

    obj_a = Obj()
    obj_b = Obj()
    obj_c = Obj()
    storage = Storage({obj_a: 1})

    evolver = storage.evolver()
    evolver.update({obj_b: 2, obj_c: 3})
    assert evolver.is_dirty()

    del obj_a, obj_b, obj_c
    collect()

    assert len(evolver.to_dict()) == 2

    evolver.commit()
    collect()

    assert not evolver.is_dirty()
    assert not evolver.to_dict()


def test_storage_evolver_roundtrip():
    class Obj(object):
        pass

    obj_a = Obj()
    obj_b = Obj()
    obj_c = Obj()
    storage = Storage({obj_a: 1, obj_b: 2})

    evolver = Evolver(storage)
    assert storage.to_dict() == evolver.to_dict()

    evolver.update({obj_c: 3})
    assert storage.to_dict() != evolver.to_dict()

    new_evolver = evolver.fork()
    evolver.reset()
    assert storage.to_dict() == evolver.to_dict()

    new_storage = new_evolver.storage()
    assert new_storage.to_dict() == new_evolver.to_dict()
    assert new_storage.to_dict() == {obj_a: 1, obj_b: 2, obj_c: 3}


@mark.parametrize("deep_copier", (deepcopy, lambda s: loads(dumps(s))))
def test_deep_copy_and_pickle_storage(deep_copier):
    class _Obj(object):
        __name__ = __qualname__ = "_Obj"

        def __init__(self, name):
            self.name = name

        def __hash__(self):
            return hash(self.name)

        def __eq__(self, other):
            return other.name == self.name

    globals()[_Obj.__name__] = _Obj

    obj_a = _Obj("a")
    obj_b = _Obj("b")
    obj_c = _Obj("c")
    obj_d = _Obj("d")
    objects = obj_a, obj_b, obj_c
    storage = Storage({obj_a: 1, obj_b: 2, obj_c: 3, obj_d: 4})

    copied_objects, copied_storage = deep_copier((objects, storage))
    truth_dict = storage.to_dict()
    del truth_dict[obj_d]
    assert copied_storage.to_dict() == truth_dict


@mark.parametrize("deep_copier", (deepcopy, lambda s: loads(dumps(s))))
def test_deep_copy_and_pickle_evolver(deep_copier):
    class _Obj(object):
        __name__ = __qualname__ = "_Obj"

        def __init__(self, name):
            self.name = name

        def __hash__(self):
            return hash(self.name)

        def __eq__(self, other):
            return other.name == self.name

    globals()[_Obj.__name__] = _Obj

    obj_a = _Obj("a")
    obj_b = _Obj("b")
    obj_c = _Obj("c")
    obj_d = _Obj("d")
    objects = obj_a,
    evolver = Storage({obj_a: 1, obj_d: 4}).evolver().update({obj_b: 2, obj_c: 3})

    copied_objects, copied_evolver = deep_copier((objects, evolver))
    assert len(copied_evolver.to_dict()) == 3
    truth_dict = evolver.to_dict()
    del truth_dict[obj_d]
    assert copied_evolver.to_dict() == truth_dict


def test_shallow_copy_storage():
    class Obj(object):
        pass

    obj_a = Obj()
    storage = Storage({obj_a: 1})

    assert copy(storage) is storage


def test_shallow_copy_evolver():
    class Obj(object):
        pass

    obj_a = Obj()
    evolver = Storage({obj_a: 1}).evolver()
    evolver_copy = copy(evolver)
    evolver_forked = evolver.fork()

    assert evolver_copy is not evolver is not evolver_forked
    assert evolver_copy.to_dict() == evolver.to_dict() == evolver_forked.to_dict()


if __name__ == "__main__":
    main()
