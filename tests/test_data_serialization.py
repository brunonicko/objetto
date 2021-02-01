# -*- coding: utf-8 -*-

import pytest

from objetto import Data, data_attribute


class HobbyData(Data):
    description = data_attribute()


def _serializer(_, **kwargs):
    return kwargs["super"]()["__state__"]


def _deserializer(serialized, **kwargs):
    return kwargs["super"](
        {"__class__": "test_data_serialization|HobbyData", "__state__": serialized}
    )


class PersonData(Data):
    name = data_attribute()
    hobby = data_attribute(HobbyData)
    special_hobby = data_attribute(
        HobbyData,
        subtypes=True,
        serializer=lambda _, **k: k["super"]()["__state__"],
        deserializer=_deserializer,
    )
    generic_hobby = data_attribute(
        HobbyData,
        subtypes=True,
    )


def test_data_serialization():
    hobby = HobbyData(description="biking")
    special_hobby = HobbyData(description="programming")
    generic_hobby = HobbyData(description="drumming")

    person = PersonData(
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
            "__class__": "test_data_serialization|HobbyData",
            "__state__": {"description": "drumming"},
        },
    }

    person_b = PersonData.deserialize(serialized_person)
    assert person_b.name == person.name
    assert person_b.hobby.description == person.hobby.description
    assert person_b.special_hobby.description == person.special_hobby.description
    assert person_b.generic_hobby.description == person.generic_hobby.description


if __name__ == "__main__":
    pytest.main()
