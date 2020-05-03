# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestMapping"]


class TestMapping(unittest.TestCase):
    """Tests for 'objetto._objects.mapping' module."""

    def test_mapping_obj(self):
        from objetto.objects import MappingObject

        sa = MappingObject(parent=True)
        sb = MappingObject(parent=True)

        sa._update({"a": 1, "b": 2, "c": 3, "d": sb})

    def test_mutable_mapping_obj(self):
        from objetto.objects import MutableMappingObject

        sa = MutableMappingObject(parent=True)
        sb = MutableMappingObject(parent=True)

        sa.update({"a": 1, "b": 2, "c": 3, "d": sb})
        del sa["a"]
        del sa["b"]
        self.assertIs(sb.hierarchy.parent, sa)


if __name__ == "__main__":
    unittest.main()
