# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestModel"]


class TestModel(unittest.TestCase):
    """Tests for '_model' module."""

    def test_model(self):
        from modelo._object_model import ObjectModel
        from modelo._attributes import attribute
        from modelo._runner import History

        class Person(ObjectModel):
            name = attribute()
            sibling = attribute()

        history = History()

        bruno = Person()
        bruno._history = history

        bruno.name = "Bruno"
        self.assertEqual(bruno.name, "Bruno")

        bianca = Person()
        bianca.name = "Bianca"
        self.assertEqual(bianca.name, "Bianca")
        self.assertIs(bianca.__hierarchy__.last_parent, None)

        bruno.sibling = bianca
        self.assertIs(bruno.sibling, bianca)
        self.assertIs(bianca.__hierarchy__.parent, bruno)
        self.assertIs(bianca.__hierarchy__.last_parent, bruno)

        bruno.sibling = None
        self.assertIs(bianca.__hierarchy__.parent, None)
        self.assertIs(bianca.__hierarchy__.last_parent, bruno)

        history.undo()
        self.assertIs(bruno.sibling, bianca)
        self.assertIs(bianca.__hierarchy__.parent, bruno)
        self.assertIs(bianca.__hierarchy__.last_parent, bruno)

    def test_attributes(self):
        from modelo import ObjectModel, attribute, dependencies, constant_attribute

        class Person(ObjectModel):
            first_name = attribute()
            last_name = attribute()
            _tested = attribute()
            tested = attribute(property=True, factory=bool)
            full_name = attribute(property=True)
            __constant = constant_attribute(3)
            constant = attribute(property=True)
            constantine = attribute(property=True)

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
                return self.first_name + " " + self.last_name + " " + str(self.__constant)

        p = Person()
        p.first_name = "Bruno"
        p.last_name = "Nicko"
        p.first_name = "Jack"
        p.tested = "Ha"
        print(p.constantine)
        print(p.full_name)
        print(p.tested)

    def test_attribute_b(self):
        from modelo import ObjectModel, attribute, dependencies

        class Person(ObjectModel):
            first_name = attribute(str)  # type: str
            last_name = attribute(str)  # type: str
            full_name = attribute(str, property=True)

            def __init__(self, first_name, last_name):
                self.update(
                    ("first_name", first_name),
                    ("last_name", last_name)
                )

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

        p = Person("Jack", "Nicholson")
        print(p.full_name)
        p.full_name = "Bruno Nicko"
        print(p.full_name)


if __name__ == "__main__":
    unittest.main()
