# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING, cast

import pytest
from pyrsistent import PClass, field

from objetto import Application, Object, attribute

if TYPE_CHECKING:
    from typing import Union  # noqa
else:
    reveal_type = lambda *_: None


def test_list_object():
    # type: () -> None

    app = Application()

    person = _Person(app, name="Albert", age=36, something=999)
    reveal_type(person.name)
    reveal_type(person.age)
    reveal_type(person.something)

    p_person = _PPerson(name="Albert", age=36, something=999)
    reveal_type(p_person.name)
    reveal_type(p_person.age)
    reveal_type(p_person.something)


class _Person(Object):
    name = attribute(str)
    age = attribute(int)
    something = cast("Union[int, str]", attribute((int, str)))


class _PPerson(PClass):
    name = field(str)
    age = field(int)
    something = cast("Union[int, str]", field((int, str)))


if __name__ == "__main__":
    pytest.main()
