# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestAutoRender"]


class TestAutoRender(unittest.TestCase):
    """Tests actions chained by events."""

    def test_application(self):
        from collections import defaultdict

        from modelo.models import ObjectModel
        from modelo.attributes import (
            attribute,
            history_attribute,
            permanent_attribute,
            sequence_attribute,
            protected_sequence_attribute_pair,
        )
        from modelo.events import (
            EventPhase,
            ModelEvent,
            SequenceInsertEvent,
            SequenceChangeEvent,
            RejectEventException,
        )

        def ensure_unique_name(container, container_name, event, phase, cache):
            if event.model is container and phase is EventPhase.INTERNAL_PRE:
                if event.adoptions:
                    new_names = set()
                    for layer in event.adoptions:
                        name = layer.name
                        if name in cache:
                            error = (
                                "a {} named '{}' already exists in the template"
                            ).format(container_name, name)
                            raise ValueError(error)
                        new_names.add(name)
                    cache.update(new_names)
                if event.releases:
                    old_names = set(layer.name for layer in event.releases)
                    cache.difference_update(old_names)

        class Layer(ObjectModel):
            name = attribute(value_factory=str, represented=True)

            def __init__(self, name="master"):
                super(Layer, self).__init__()
                self.name = name

        class Comp(ObjectModel):
            name = attribute(value_factory=str, represented=True)
            _nodes, nodes = protected_sequence_attribute_pair(represented=True)

            def __init__(self, name="master"):
                super(Comp, self).__init__()
                self.name = name
                self._nodes.append("Node A", "Node B", "Node C")

        class Template(ObjectModel):

            __slots__ = ("__layer_names", "__comp_names")

            layers = sequence_attribute(Layer)
            comps = sequence_attribute(Comp)

            def __init__(self):
                super(Template, self).__init__()
                self.__layer_names = set()
                self.__comp_names = set()
                self.layers.events.add_listener(self)
                self.comps.events.add_listener(self)

            def __react__(self, event, phase):
                ensure_unique_name(
                    self.layers, "layer", event, phase, self.__layer_names
                )
                ensure_unique_name(self.comps, "comp", event, phase, self.__comp_names)

        class Application(ObjectModel):
            template = permanent_attribute(default_factory=Template)
            history = history_attribute()

        app = Application()

        app.template.layers.append(Layer())
        app.template.layers.append(Layer("layer_a"))
        app.template.layers.append(Layer("layer_b"))
        self.assertRaises(ValueError, app.template.layers.append, Layer())

        app.template.comps.append(Comp())
        app.template.comps.append(Comp("comp_a"))
        app.template.comps.append(Comp("comp_b"))
        self.assertRaises(ValueError, app.template.comps.append, Comp())

        print(app.template.layers)
        print(app.template.comps)

        app.history.undo()

        print(app.template.layers)
        print(app.template.comps)


if __name__ == "__main__":
    unittest.main()
