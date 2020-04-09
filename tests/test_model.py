# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestModel"]


class TestModel(unittest.TestCase):
    """Tests for '_model' module."""

    def test_model(self):
        from modelo._model import Model
        from modelo._attributes import attribute
        from modelo._runner import History

        class Person(Model):
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

    def test_layers(self):
        from typing import cast
        from modelo._model import Model
        from modelo._events import AttributesUpdateEvent
        from modelo._constants import EventPhase
        from modelo._attributes import attribute
        from modelo._exceptions import RejectEventException

        class Layer(Model):
            name = attribute()

        class Layers(Model):
            a = attribute()
            b = attribute()
            c = attribute()

            def __init__(self):
                self.a = Layer()
                self.a.name = "a"

                self.b = Layer()
                self.b.name = "b"

                self.c = Layer()
                self.c.name = "c"

                self._events[AttributesUpdateEvent].add_listener(self)

            def __react__(self, model, event, phase):
                if model is self and phase is EventPhase.INTERNAL_PRE:
                    if event.type is AttributesUpdateEvent:
                        event = cast(AttributesUpdateEvent, event)
                        attributes = "a", "b", "c"
                        current_names = dict(
                            (a, getattr(self, a).name) for a in attributes
                        )
                        current_layers = dict(
                            (a, getattr(self, a)) for a in attributes
                        )
                        for na, layer in event.new_values.items():
                            if layer.name in current_names.values():
                                if layer is not current_layers[na]:

                                    def callback(s=self, la=layer, u=event.new_values):
                                        la.name = la.name + "_1"
                                        s.update(u)

                                    raise RejectEventException(callback)

        layers = Layers()

        new_layer = Layer()
        new_layer.name = "b"
        layers.a = new_layer

        new_layer = Layer()
        new_layer.name = "b"
        layers.a = new_layer

        print(layers.a.name)
        print(layers.b.name)
        print(layers.c.name)

    def test_attributes(self):
        from modelo import Model, attribute, dependencies

        class Person(Model):
            first_name = attribute()
            last_name = attribute()
            _tested = attribute()
            tested = attribute(property=True, factory=bool)
            full_name = attribute(property=True)
            __constant = attribute(property=True)
            __cls_constant = 311

            @tested.getter
            @dependencies(gets=("_tested",))
            def tested(self):
                return self._tested

            @tested.setter
            @dependencies(sets=("_tested",))
            def tested(self, value):
                self._tested = value

            @__constant.getter()
            def __constant(self):
                return 3

            @full_name.getter(gets=("first_name", "last_name", "__constant", "__cls_constant"))
            def full_name(self):
                return self.first_name + " " + self.last_name + " " + str(self.__constant) + " " + str(self.__cls_constant)

        p = Person()
        p.first_name = "Bruno"
        p.last_name = "Nicko"
        p.first_name = "Jack"
        p.tested = "Ha"
        print(p.full_name)
        print(p.tested)

    def test_attribute_b(self):
        from modelo import Model, attribute, dependencies

        class Person(Model):
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
