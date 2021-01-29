# -*- coding: utf-8 -*-

import pytest

from objetto import Application, Object, attribute, constant_attribute


class Hobby(Object):
    pass


class Ciclying(Hobby):
    pass


class Programming(Hobby):
    pass


class Person(Object):
    HOBBY_TYPE = constant_attribute(Hobby, abstracted=True)

    hobby = attribute(
        "{{owner.__module__}}|{{owner.__fullname__}}.HOBBY_TYPE",
        default_factory=lambda **k: k["owner"].HOBBY_TYPE(k["app"]),
    )

    friend = attribute(
        ("Person", None),
        subtypes=True,
        default=None,
    )


class Ciclyst(Person):
    HOBBY_TYPE = constant_attribute(Ciclying)


class Programmer(Person):
    HOBBY_TYPE = constant_attribute(Programming)


def test_attribute_factory():
    app = Application()
    ciclyst = Ciclyst(app)
    programmer = Programmer(app, friend=ciclyst)

    assert isinstance(ciclyst.hobby, Ciclying)
    assert isinstance(programmer.hobby, Programming)


if __name__ == "__main__":
    pytest.main()
