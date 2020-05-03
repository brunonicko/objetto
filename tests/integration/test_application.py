# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestApplication"]


class TestApplication(unittest.TestCase):
    """Test simple application."""

    def test_default(self):
        from objetto.objects import Object
        from objetto.attributes import (
            attribute,
            history_attribute,
            permanent_attribute,
            list_attribute,
            protected_list_attribute_pair,
        )
        from objetto.factories import integer, curated
        from objetto.reactions import unique_attributes, limit

        class Layer(Object):
            name = attribute(value_factory=str, represented=True)

            def __init__(self, name="master"):
                super(Layer, self).__init__()
                self.name = name

        class Comp(Object):
            name = attribute(value_factory=str, represented=True)
            order = attribute(
                default=0,
                value_factory=integer(maximum=100) + curated(*range(90)),
                represented=True,
            )
            _nodes, nodes = protected_list_attribute_pair(
                represented=True, type_name="CompNodeList"
            )

            def __init__(self, name="master"):
                super(Comp, self).__init__()
                self.name = name
                self._nodes.append("Node A", "Node B", "Node C")

        class Document(Object):
            layers = list_attribute(
                Layer, reaction=unique_attributes("name") + limit(maximum=4)
            )
            comps = list_attribute(
                Comp,
                reaction=unique_attributes("name", order=lambda v, vs: max(vs) + 1),
            )

        class Application(Object):
            template = permanent_attribute(default_factory=Document)
            history = history_attribute()

        app = Application()

        app.template.layers.append(Layer())
        app.template.layers.append(Layer("layer_a"))
        app.template.layers.append(Layer("layer_b"))
        self.assertRaises(ValueError, app.template.layers.append, Layer())
        app.template.layers.append(Layer("layer_c"))
        self.assertRaises(ValueError, app.template.layers.append, Layer("layer_d"))

        app.template.comps.append(Comp())
        app.template.comps.append(Comp("comp_a"))
        app.template.comps.append(Comp("comp_b"))
        self.assertRaises(ValueError, app.template.comps.append, Comp())

        last_comp = app.template.comps[-1]
        self.assertRaises(ValueError, setattr, last_comp, "name", "master")
        last_comp_popped = app.template.comps.pop()
        self.assertIs(last_comp, last_comp_popped)
        last_comp.name = "master"
        self.assertRaises(ValueError, app.template.comps.append, last_comp)

        app.template.comps[1].order = 2
        self.assertEqual(app.template.comps[1].order, 2)
        app.template.comps[1].order = 0
        self.assertEqual(app.template.comps[1].order, 1)

        self.assertRaises(ValueError, setattr, app.template.comps[1], "order", 120)
        self.assertRaises(ValueError, setattr, app.template.comps[1], "order", 95)

        app.history.undo_all()
        app.history.redo_all()


if __name__ == "__main__":
    unittest.main()
