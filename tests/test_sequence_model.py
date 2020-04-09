# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestSequenceModel"]


class TestSequenceModel(unittest.TestCase):
    """Tests for '_sequence_model' module."""

    def test_sequence_model(self):
        from modelo._sequence_model import SequenceModel
        from modelo._runner import History

        s = SequenceModel()
        h = History()
        s.__runner__.history = h

        print(list(s))
        s._insert(0, 1, 2, 3, 4, 5)
        print(list(s))
        s._pop(2, 2)
        print(list(s))
        h.undo()
        print(list(s))
        h.undo()
        print(list(s))

        print(hash(s))


if __name__ == "__main__":
    unittest.main()
