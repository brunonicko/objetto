# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestChainedActions"]


class TestChainedActions(unittest.TestCase):
    """Tests actions chained by events."""

    def test_multiple_actions_same_history(self):
        from objetto.objects import Object, MutableSequenceObject
        from objetto.attributes import attribute, history_attribute
        from objetto.events import EventPhase, SequenceInsertEvent, SequencePopEvent

        class MyObject(Object):
            last_action = attribute()
            seq = attribute()
            history = history_attribute()

            def __init__(self):
                super(MyObject, self).__init__()
                self.last_action = None

                self.seq = MutableSequenceObject()
                self.seq.events.add_listener(self)

            def __react__(self, event, phase):
                if isinstance(event, SequenceInsertEvent) and phase is EventPhase.PRE:
                    if event.obj is self.seq:
                        self.last_action = "Insert " + str(event.new_values)
                elif isinstance(event, SequencePopEvent) and phase is EventPhase.PRE:
                    if event.obj is self.seq:
                        self.last_action = "Pop " + str(event.old_values)

        obj = MyObject()
        self.assertIsNone(obj.last_action)

        obj.seq.append(1, 2, 3)
        self.assertEqual(obj.last_action, "Insert (1, 2, 3)")

        obj.seq.pop()
        self.assertEqual(obj.last_action, "Pop (3,)")

        obj.history.undo()
        self.assertEqual(obj.last_action, "Insert (3,)")

        obj.history.undo()
        self.assertEqual(obj.last_action, "Pop (1, 2, 3)")


if __name__ == "__main__":
    unittest.main()
