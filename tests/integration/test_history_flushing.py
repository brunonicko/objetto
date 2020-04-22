# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestHistoryFlushing"]


class TestHistoryFlushing(unittest.TestCase):
    """Tests automatic history flushing."""

    def test_flush_when_parent_changes(self):
        from modelo.models import SequenceModel
        from modelo._components.history import History, CannotRedoError

        seq_a = SequenceModel(parent=True, history=False)
        seq_a._history = hist_a = History()
        seq_b = SequenceModel(parent=True, history=False)
        seq_c = SequenceModel(parent=True, history=False)

        seq_a._insert(0, seq_b)
        self.assertTrue(hist_a.can_undo)

        hist_a.undo()
        self.assertTrue(hist_a.can_redo)
        seq_c._insert(0, seq_b)

        self.assertFalse(hist_a.can_redo)
        self.assertRaises(CannotRedoError, hist_a.redo)

    def test_flush_when_history_changes(self):
        from modelo.models import SequenceModel
        from modelo._components.history import History, CannotRedoError

        seq_a = SequenceModel(parent=True, history=False)
        seq_a._history = hist_a = History()
        hist_b = History()

        seq_a._insert(0, 1)
        self.assertTrue(hist_a.can_undo)
        self.assertEqual(len(hist_b), 1)

        seq_a._history = hist_b
        self.assertFalse(hist_a.can_undo)
        self.assertEqual(len(hist_a), 1)

        seq_a._insert(0, 1)
        self.assertTrue(hist_b.can_undo)
        self.assertEqual(len(hist_b), 2)
        self.assertFalse(hist_a.can_undo)
        self.assertEqual(len(hist_a), 1)

    def test_history_adoption(self):
        from modelo.models import SequenceModel
        from modelo._components.history import History

        seq_a = SequenceModel(parent=False, history=True)
        seq_a._history = hist_a = History()
        seq_b = SequenceModel(parent=False, history=True)
        seq_c = SequenceModel(parent=False, history=True)

        seq_a._insert(0, seq_b)
        seq_b._insert(0, seq_c)

        self.assertIs(seq_a._history, hist_a)
        self.assertIs(seq_b._history, seq_a._history)
        self.assertIs(seq_c._history, seq_a._history)


if __name__ == "__main__":
    unittest.main()
