# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestModel"]


class TestModel(unittest.TestCase):
    """Tests for '_model' module."""

    def test_model(self):
        from modelo.models import ObjectModel
        from modelo.attributes import attribute
        from modelo._components.runner import History

        class Person(ObjectModel):
            name = attribute()
            sibling = attribute(parent=True)

        history = History(size=500)

        bruno = Person()
        bruno._history = history

        bruno.name = "Bruno"
        self.assertEqual(bruno.name, "Bruno")

        bianca = Person()
        bianca.name = "Bianca"
        self.assertEqual(bianca.name, "Bianca")
        bianca_hierarchy = bianca._hierarchy
        self.assertIs(bianca_hierarchy.last_parent, None)

        bruno.sibling = bianca
        self.assertIs(bruno.sibling, bianca)
        self.assertIs(bianca_hierarchy.parent, bruno)
        self.assertIs(bianca_hierarchy.last_parent, bruno)

        bruno.sibling = None
        self.assertIs(bianca_hierarchy.parent, None)
        self.assertIs(bianca_hierarchy.last_parent, bruno)

        history.undo()
        self.assertIs(bruno.sibling, bianca)
        self.assertIs(bianca_hierarchy.parent, bruno)
        self.assertIs(bianca_hierarchy.last_parent, bruno)

    def test_attributes(self):
        from modelo.models import ObjectModel
        from modelo.attributes import attribute, dependencies, constant_attribute

        class Person(ObjectModel):
            first_name = attribute()
            last_name = attribute()
            _tested = attribute()
            tested = attribute(delegated=True, value_factory=bool)
            full_name = attribute(delegated=True)
            __constant = constant_attribute(3)
            constant = attribute(delegated=True)
            constantine = attribute(delegated=True)

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
        from modelo.events import EventListenerMixin
        from modelo.models import ObjectModel
        from modelo.attributes import attribute, dependencies

        class Person(ObjectModel):
            first_name = attribute(str)  # type: str
            last_name = attribute(str)  # type: str
            full_name = attribute(str, delegated=True)

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

        class PersonListener(EventListenerMixin):
            def __react__(_, obj, event, phase):
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


if __name__ == "__main__":
    unittest.main()
