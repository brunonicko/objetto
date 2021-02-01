# -*- coding: utf-8 -*-

import pytest

from objetto import Application, Object, attribute


class Hobby(Object):
    description = attribute()


def _serializer(_, **kwargs):
    return kwargs["super"]()["__state__"]


def _deserializer(serialized, **kwargs):
    return kwargs["super"](
        {"__class__": "test_object_serialization|Hobby", "__state__": serialized}
    )


class Person(Object):
    name = attribute()
    hobby = attribute(Hobby)
    special_hobby = attribute(
        Hobby,
        subtypes=True,
        serializer=lambda _, **k: k["super"]()["__state__"],
        deserializer=_deserializer,
    )
    generic_hobby = attribute(
        Hobby,
        subtypes=True,
    )


def test_object_serialization():
    app = Application()

    hobby = Hobby(app, description="biking")
    special_hobby = Hobby(app, description="programming")
    generic_hobby = Hobby(app, description="drumming")

    person = Person(
        app,
        name="Bruno",
        hobby=hobby,
        special_hobby=special_hobby,
        generic_hobby=generic_hobby,
    )

    serialized_person = person.serialize()
    assert serialized_person == {
        "name": "Bruno",
        "hobby": {"description": "biking"},
        "special_hobby": {"description": "programming"},
        "generic_hobby": {
            "__class__": "test_object_serialization|Hobby",
            "__state__": {"description": "drumming"},
        },
    }

    person_b = Person.deserialize(serialized_person, app=app)
    assert person_b.name == person.name
    assert person_b.hobby.description == person.hobby.description
    assert person_b.special_hobby.description == person.special_hobby.description
    assert person_b.generic_hobby.description == person.generic_hobby.description


if __name__ == "__main__":
    pytest.main()
