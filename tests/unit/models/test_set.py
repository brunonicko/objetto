# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestSet"]


class TestSet(unittest.TestCase):
    """Tests for 'modelo._models.set' module."""

    def test_set_model(self):
        from modelo.models import SetModel

        sa = SetModel(parent=True)
        sb = SetModel(parent=True)

        sa._add(*[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, sb])
        sa._pop()

    def test_mutable_set_model(self):
        from modelo.models import MutableSetModel

        sa = MutableSetModel(parent=True)
        sb = MutableSetModel(parent=True)

        sa.add(*[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, sb])
        sa.pop()
        sa.pop()
        sa.pop()
        sa.pop()
        sa.pop()

    def test_update(self):
        from modelo.models import MutableSetModel

        sa = MutableSetModel(parent=True)
        sb = MutableSetModel(parent=True)
        sa.update(range(0, 10))
        sb.update(range(7, 17))

        self.assertEqual(set(sa), set(range(0, 10)))
        self.assertEqual(set(sb), set(range(7, 17)))

    def test_difference_update(self):
        from modelo.models import MutableSetModel

        sa = MutableSetModel(parent=True)
        sb = MutableSetModel(parent=True)
        sa.update(range(0, 10))
        sb.update(range(7, 17))

        expected = set(sa).difference(set(sb))
        sa.difference_update(sb)
        self.assertEqual(set(sa), expected)

    def test_symmetric_difference_update(self):
        from modelo.models import MutableSetModel

        sa = MutableSetModel(parent=True)
        sb = MutableSetModel(parent=True)
        sa.update(range(0, 10))
        sb.update(range(7, 17))

        expected = set(sa).symmetric_difference(set(sb))
        sa.symmetric_difference_update(sb)
        self.assertEqual(set(sa), expected)

    def test_intersection_update(self):
        from modelo.models import MutableSetModel

        sa = MutableSetModel(parent=True)
        sb = MutableSetModel(parent=True)
        sa.update(range(0, 10))
        sb.update(range(7, 17))

        expected = set(sa).intersection(set(sb))
        sa.intersection_update(sb)
        self.assertEqual(set(sa), expected)


if __name__ == "__main__":
    unittest.main()
