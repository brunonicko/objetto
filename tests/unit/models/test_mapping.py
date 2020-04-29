# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestMapping"]


class TestMapping(unittest.TestCase):
    """Tests for 'modelo._models.mapping' module."""

    def test_mapping_model(self):
        from modelo.models import MappingModel

        sa = MappingModel(parent=True)
        sb = MappingModel(parent=True)

        sa._update({"a": 1, "b": 2, "c": 3, "d": sb})

    def test_mutable_mapping_model(self):
        from modelo.models import MutableMappingModel

        sa = MutableMappingModel(parent=True)
        sb = MutableMappingModel(parent=True)

        sa.update({"a": 1, "b": 2, "c": 3, "d": sb})
        del sa["a"]
        del sa["b"]
        self.assertIs(sb.hierarchy.parent, sa)


if __name__ == "__main__":
    unittest.main()
