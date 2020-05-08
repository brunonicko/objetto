# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestObject"]


class TestObject(unittest.TestCase):
    """Tests for 'objetto._objects.object' module."""

    def test_usage(self):
        from objetto.objects import Object
        from objetto.attributes import attribute, history_attribute

        class Person(Object):
            name = attribute()
            sibling = attribute(parent=True)
            history = history_attribute()

        bruno = Person()

        bruno.name = "Bruno"
        self.assertEqual(bruno.name, "Bruno")

        bianca = Person()
        bianca.name = "Bianca"
        self.assertEqual(bianca.name, "Bianca")
        bianca_hierarchy = bianca.hierarchy
        self.assertIs(bianca_hierarchy.last_parent, None)

        bruno.sibling = bianca
        self.assertIs(bruno.sibling, bianca)
        self.assertIs(bianca_hierarchy.parent, bruno)
        self.assertIs(bianca_hierarchy.last_parent, bruno)

        bruno.sibling = None
        self.assertIs(bianca_hierarchy.parent, None)
        self.assertIs(bianca_hierarchy.last_parent, bruno)

        bruno.history.undo()
        self.assertIs(bruno.sibling, bianca)
        self.assertIs(bianca_hierarchy.parent, bruno)
        self.assertIs(bianca_hierarchy.last_parent, bruno)

    def test_attributes(self):
        from objetto.objects import Object
        from objetto.attributes import attribute, dependencies, constant_attribute

        class Person(Object):
            first_name = attribute()
            last_name = attribute()
            _tested = attribute()
            tested = attribute(delegated=True, value_factory=bool)
            full_name = attribute(delegated=True)
            __constant = constant_attribute(3)
            constant = attribute(delegated=True, parent=False, history=False)
            constantine = attribute(delegated=True, parent=False, history=False)

            @constant.getter
            @dependencies(gets=("__constant",))
            def constant(self):
                return self.__constant * 2

            @constantine.getter
            @dependencies(gets=("constant",))
            def constantine(self):
                return self.constant * 2

            @tested.getter
            @dependencies(gets=("_tested",))
            def tested(self):
                return self._tested

            @tested.setter
            @dependencies(sets=("_tested",))
            def tested(self, value):
                self._tested = value

            @full_name.getter
            @dependencies(gets=("first_name", "last_name", "__constant"))
            def full_name(self):
                return (
                    self.first_name + " " + self.last_name + " " + str(self.__constant)
                )

        p = Person()
        p.first_name = "Bruno"
        p.last_name = "Nicko"
        p.first_name = "Jack"
        p.tested = "Ha"

        self.assertEqual(p.constantine, 12)
        self.assertEqual(p.full_name, "Jack Nicko 3")
        self.assertEqual(p.tested, True)
        self.assertEqual(Person.constantine, 12)

    def test_attribute_b(self):
        from objetto.events import SlottedEventListenerMixin
        from objetto.objects import Object
        from objetto.attributes import attribute, dependencies

        class Person(Object):
            first_name = attribute(str)  # type: str
            last_name = attribute(str)  # type: str
            age = attribute(int)  # type: int
            sibling = attribute(parent=True)  # type: Person
            full_name = attribute(str, delegated=True, represented=True)

            def __init__(self, first_name, last_name):
                super(Person, self).__init__()
                self.update(("first_name", first_name), ("last_name", last_name))

            @full_name.getter
            @dependencies(gets=("first_name", "last_name"))
            def full_name(self):
                # type: () -> str
                return "{} {}".format(self.first_name, self.last_name)

            @full_name.setter
            @dependencies(sets=("first_name", "last_name"))
            def full_name(self, value):
                # type: (str) -> None
                self.first_name, self.last_name = value.split(" ")

        class PersonListener(SlottedEventListenerMixin):
            def __react__(_, event, phase):
                self.assertEqual(
                    getattr(event, "old_values"),
                    {
                        "first_name": "Jack",
                        "last_name": "Nicholson",
                        "full_name": "Jack Nicholson",
                    },
                )
                self.assertEqual(
                    getattr(event, "new_values"),
                    {
                        "first_name": "Bruno",
                        "last_name": "Nicko",
                        "full_name": "Bruno Nicko",
                    },
                )

        p = Person("Jack", "Nicholson")
        pl = PersonListener()
        p.events.add_listener(pl)
        self.assertEqual(p.full_name, "Jack Nicholson")
        p.full_name = "Bruno Nicko"
        self.assertEqual(p.full_name, "Bruno Nicko")

        pp = Person("Bruno", "Nicko")
        self.assertEqual(p, pp)
        self.assertIsNot(p, pp)

        p.events.remove_listener(pl)
        p.age = 35
        self.assertNotEqual(p, pp)
        pp.age = 35
        self.assertEqual(p, pp)

        p.sibling = pp

    def test_mixin(self):
        from objetto.objects import Object
        from objetto.attributes import attribute

        class ObjectA(Object):
            a = attribute()

        class ObjectB(Object):
            b = attribute()

        class Mixin(object):
            __slots__ = ()
            mixin = attribute()

        class MixedObjectA(ObjectA, Mixin):
            mixed_a = attribute()

        class MixedObjectB(ObjectB, Mixin):
            mixed_b = attribute()

        self.assertEqual(set(MixedObjectA.attributes.keys()), {"a", "mixin", "mixed_a"})
        self.assertEqual(set(MixedObjectB.attributes.keys()), {"b", "mixin", "mixed_b"})

    def test_constant(self):
        from objetto.objects import Object
        from objetto.attributes import constant_attribute

        class ObjectA(Object):
            a = constant_attribute("test")

        obj_a = ObjectA()

        self.assertEqual(ObjectA.a, "test")
        self.assertEqual(obj_a.a, "test")
        self.assertRaises(AttributeError, setattr, obj_a, "a", None)

    def test_dependency_promises(self):
        from objetto.objects import Object
        from objetto.attributes import attribute, dependencies

        class Person(Object):
            first_name = attribute(str)  # type: str
            last_name = attribute(str)  # type: str
            full_name = attribute(str, delegated=True, represented=True)

            def __init__(self, first_name, last_name):
                super(Person, self).__init__()
                self.update(("first_name", first_name), ("last_name", last_name))

            @full_name.getter
            @dependencies(gets=(first_name, last_name))
            def full_name(self):
                # type: () -> str
                return "{} {}".format(self.first_name, self.last_name)

            @full_name.setter
            @dependencies(sets=(first_name, last_name))
            def full_name(self, value):
                # type: (str) -> None
                self.first_name, self.last_name = value.split(" ")

        self.assertEqual(
            getattr(Person.full_name.fget, "gets"),
            frozenset(("first_name", "last_name")),
        )
        self.assertEqual(
            getattr(Person.full_name.fset, "sets"),
            frozenset(("first_name", "last_name")),
        )

        p = Person("Bruno", "Nicko")
        self.assertEqual(p.first_name, "Bruno")
        self.assertEqual(p.last_name, "Nicko")
        self.assertEqual(p.full_name, "Bruno Nicko")

        p.first_name = "Foo"
        self.assertEqual(p.first_name, "Foo")
        self.assertEqual(p.last_name, "Nicko")
        self.assertEqual(p.full_name, "Foo Nicko")

        p.last_name = "Bar"
        self.assertEqual(p.first_name, "Foo")
        self.assertEqual(p.last_name, "Bar")
        self.assertEqual(p.full_name, "Foo Bar")

        p.full_name = "Bar Foo"
        self.assertEqual(p.first_name, "Bar")
        self.assertEqual(p.last_name, "Foo")
        self.assertEqual(p.full_name, "Bar Foo")


if __name__ == "__main__":
    unittest.main()
