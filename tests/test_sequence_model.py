# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestSequenceModel"]


class TestSequenceModel(unittest.TestCase):
    """Tests for '_sequence_model' module."""

    def test_sequence_model(self):
        from modelo.models import SequenceModel

        sa = SequenceModel(parent=True)
        sb = SequenceModel(parent=True)

        print(sa)
        sa._insert(0, *[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, sb])
        print(sa)
        print(sb._hierarchy.parent)
        sa._move(2, 1, 5)
        print(sa)
        sa._move(1, 6, 4)
        print(sa)
        sa._pop()
        print(sa)
        sa._pop(0, -1)
        print(sa)


if __name__ == "__main__":
    unittest.main()
