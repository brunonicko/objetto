# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestAutoRender"]


class TestAutoRender(unittest.TestCase):
    """Tests actions chained by events."""

    def test_application(self):
        from modelo.models import ObjectModel
        from modelo.attributes import (
            attribute,
            history_attribute,
            permanent_attribute,
            sequence_attribute,
            protected_sequence_attribute_pair,
        )
        from modelo.factories import integer, curated
        from modelo.reactions import unique_attributes, limit

        class Layer(ObjectModel):
            name = attribute(value_factory=str, represented=True)

            def __init__(self, name="master"):
                super(Layer, self).__init__()
                self.name = name

        class Comp(ObjectModel):
            name = attribute(value_factory=str, represented=True)
            order = attribute(
                default=0,
                value_factory=integer(maximum=100) + curated(*range(90)),
                represented=True,
            )
            _nodes, nodes = protected_sequence_attribute_pair(
                represented=True, type_name="CompNodeList"
            )

            def __init__(self, name="master"):
                super(Comp, self).__init__()
                self.name = name
                self._nodes.append("Node A", "Node B", "Node C")

        class Template(ObjectModel):
            layers = sequence_attribute(
                Layer, reaction=unique_attributes("name") + limit(maximum=4)
            )
            comps = sequence_attribute(
                Comp,
                reaction=unique_attributes("name", order=lambda v, vs: max(vs) + 1),
            )

        class Application(ObjectModel):
            template = permanent_attribute(default_factory=Template)
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
