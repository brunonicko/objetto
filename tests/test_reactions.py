# -*- coding: utf-8 -*-

import pytest

from objetto import Application, Object, attribute, list_attribute
from objetto.reactions import UniqueAttributes


def test_unique_attributes():
    class Hobby(Object):
        name = attribute(default="cycling")

    class Person(Object):
        hobbies = list_attribute(
            Hobby,
            reactions=UniqueAttributes(
                name=lambda v, a: v if v == "a" else "{}z".format(v)
            ),
        )

    app = Application()
    person = Person(app)

    person.hobbies.append(Hobby(app, name="a"))
    person.hobbies.append(Hobby(app, name="b"))
    person.hobbies.append(Hobby(app, name="c"))

    person.hobbies[-1].name = "c"

    with pytest.raises(RuntimeError):
        person.hobbies[-1].name = "a"

    person.hobbies[-1].name = "b"
    assert person.hobbies[-1].name == "bz"

    person.hobbies.append(Hobby(app))
    person.hobbies.append(Hobby(app))

    with pytest.raises(RuntimeError):
        person.hobbies.append(Hobby(app, name="a"))

    person.hobbies[0].name = "bz"
    person.hobbies[0].name = "a"

    with pytest.raises(RuntimeError):
        person.hobbies[1].name = "a"


if __name__ == "__main__":
    pytest.main()
