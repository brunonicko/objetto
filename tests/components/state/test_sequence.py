# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestSequence"]


class TestSequence(unittest.TestCase):
    """Tests for 'modelo._components.state.sequence' module."""

    def test_operations(self):
        from typing import cast

        from modelo._components.state.base import State
        from modelo._components.state.sequence import SequenceState

        composite = Composite()
        added_state = composite._.add_component(SequenceState)
        state = cast(SequenceState, composite._[State])
        self.assertIs(added_state, state)

        self.assertEqual(list(state), [])

        insert = state.prepare_insert(0, *range(10))
        state.insert(insert)
        self.assertEqual(list(state), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

        pop = state.prepare_pop(3, 5)
        values = state.pop(pop)
        self.assertEqual(list(state), [0, 1, 2, 6, 7, 8, 9])
        self.assertEqual(values, (3, 4, 5))

        move = state.prepare_move(3, target_index=1, last_index=5)
        state.move(move)
        self.assertEqual(list(state), [0, 6, 7, 8, 1, 2, 9])

        move = state.prepare_move(1, target_index=4, last_index=2)
        state.move(move)
        self.assertEqual(list(state), [0, 8, 6, 7, 1, 2, 9])

        change = state.prepare_change(1, *(1, 2, 3, 4, 5, 6))
        state.change(change)
        self.assertEqual(list(state), [0, 1, 2, 3, 4, 5, 6])


if __name__ == "__main__":
    unittest.main()
