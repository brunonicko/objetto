# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestBroadcaster"]


class TestBroadcaster(unittest.TestCase):
    """Tests for 'objetto._components.broadcaster' module."""

    def test_broadcaster(self):
        from objetto._components.events import (
            Broadcaster,
            EventListenerMixin,
            EventPhase,
            PhaseError,
        )

        event, phase = None, None
        reacted = [False]

        def react(_, event_, phase_):
            self.assertEqual(event_, event)
            self.assertIs(phase_, phase)
            reacted[0] = True

        class Listener(EventListenerMixin):
            __slots__ = ()
            __react__ = react

        broadcaster = Broadcaster()

        listener = Listener()
        broadcaster.emitter.add_listener(listener)

        event, phase = "AbstractEvent A", EventPhase.PRE
        self.assertTrue(broadcaster.emit(event, phase))
        self.assertTrue(reacted[0])
        reacted[0] = False

        event, phase = "AbstractEvent A", EventPhase.POST
        self.assertTrue(broadcaster.emit(event, phase))
        self.assertTrue(reacted[0])
        reacted[0] = False

        self.assertRaises(TypeError, broadcaster.emitter.add_listener, 3)
        self.assertRaises(TypeError, broadcaster.emit, None, phase)
        self.assertRaises(TypeError, broadcaster.emit, event, None)


if __name__ == "__main__":
    unittest.main()
