# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestSequence"]


class TestSequence(unittest.TestCase):
    """Tests for '_sequence_model' module."""

    def test_sequence_model(self):
        from modelo.models import SequenceModel

        sa = SequenceModel(parent=True)
        sb = SequenceModel(parent=True)

        sa._insert(0, *[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, sb])
        sa._move(2, 1, 5)
        sa._move(1, 6, 4)
        sa._pop()
        sa._pop(0, -1)

    def test_mutable_sequence_model(self):
        from modelo.models import MutableSequenceModel

        sa = MutableSequenceModel(parent=True)
        sb = MutableSequenceModel(parent=True)

        sa.insert(0, *[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, sb])
        sa.move(2, 1, 5)
        sa.move(1, 6, 4)
        sa.pop()
        sa.pop(0, -1)
        sa[3:3] = "a", "b", "c", "d"
        del sa[2:4]
        del sa[0]


if __name__ == "__main__":
    unittest.main()
