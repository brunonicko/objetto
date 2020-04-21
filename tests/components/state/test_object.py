# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestObject"]


class TestObject(unittest.TestCase):
    """Tests for 'modelo._components.attributes' module."""

    def test_make_object_state_class(self):
        from typing import cast

        from modelo._components.state.base import State
        from modelo._components.attributes import (
            Attribute, ObjectState, make_object_state_class, AttributeDelegate
        )

        foo = Attribute("foo")
        bar = Attribute("bar")
        foobar = Attribute("foobar", delegated=True)
        constant = Attribute("constant", delegated=True)

        @foobar.getter
        @AttributeDelegate.get_decorator(gets=("foo", "bar"))
        def foobar(access):
            return access.foo + " " + access.bar

        @constant.getter
        def constant(_):
            return 3

        attributes = foo, bar, foobar, constant

        composite = Composite()
        state_class = make_object_state_class(*attributes)
        print("state_class", state_class)
        print("state_class.get_key_type()", state_class.get_key_type())

        state = composite._.add_component(state_class)
        print("state", state)

        state = cast(ObjectState, composite._[State])
        print("state", state)

        print("attributes", type(state).attributes)
        print("dependencies", type(state).dependencies)
        print("constants", type(state).constants)

        state_update = state.prepare_update(("foo", "Bruno"), ("bar", "Nicko"))
        state.update(state_update)

        print(state["foobar"])


if __name__ == "__main__":
    unittest.main()
