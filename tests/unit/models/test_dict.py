# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestDict"]


class TestDict(unittest.TestCase):
    """Tests for 'objetto._objects.dict' module."""

    def test_dict_obj(self):
        from objetto.objects import DictObject

        sa = DictObject(parent=True)
        sb = DictObject(parent=True)

        sa._update({"a": 1, "b": 2, "c": 3, "d": sb})

    def test_mutable_dict_obj(self):
        from objetto.objects import MutableDictObject

        sa = MutableDictObject(parent=True)
        sb = MutableDictObject(parent=True)

        sa.update({"a": 1, "b": 2, "c": 3, "d": sb})
        del sa["a"]
        del sa["b"]
        self.assertIs(sb.hierarchy.parent, sa)


if __name__ == "__main__":
    unittest.main()
