# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestSequenceModel"]


class TestSequenceModel(unittest.TestCase):
    """Tests for '_sequence_model' module."""

    def test_sequence_model(self):
        from modelo.models import SequenceModel

        s = SequenceModel()

        print(list(s))
        s._insert(0, *[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        print(list(s))
        s._move(2, 1, 5)
        print(list(s))
        s._move(1, 6, 4)
        print(list(s))


if __name__ == "__main__":
    unittest.main()
