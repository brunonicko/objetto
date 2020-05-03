# -*- coding: utf-8 -*-

import unittest

__all__ = ["TestExample"]


class TestExample(unittest.TestCase):
    """Test example."""

    def test_example(self):
        from objetto import (
            Object, attribute, sequence_attribute, history_attribute, dependencies
        )
        from objetto.factories import regex_match
        from objetto.reactions import unique_attributes

        class Person(Object):
            first_name = attribute(value_type=str)
            last_name = attribute(value_type=str)

            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name

        person = Person("George", "Byron")
        self.assertEqual(person.first_name, "George")
        self.assertEqual(person.last_name, "Byron")

        name_regex = r"^[A-Z][a-zA-Z]*$"

        class Person(Object):
            first_name = attribute(value_factory=regex_match(name_regex))
            last_name = attribute(value_factory=regex_match(name_regex))
            full_name = attribute(value_type=str, delegated=True)

            @full_name.getter
            @dependencies(gets=(first_name, last_name))
            def full_name(self):
                return " ".join((self.first_name, self.last_name))

            @full_name.setter
            @dependencies(sets=(first_name, last_name))
            def full_name(self, full_name):
                self.first_name, self.last_name = full_name.split()

            def __init__(self, full_name):
                self.full_name = full_name

        person = Person("George Byron")
        self.assertEqual(person.first_name, "George")
        self.assertEqual(person.last_name, "Byron")
        self.assertEqual(person.full_name, "George Byron")

        person.first_name = "Ada"
        self.assertEqual(person.first_name, "Ada")
        self.assertEqual(person.last_name, "Byron")
        self.assertEqual(person.full_name, "Ada Byron")

        person.full_name = "Ada Lovelace"
        self.assertEqual(person.first_name, "Ada")
        self.assertEqual(person.last_name, "Lovelace")
        self.assertEqual(person.full_name, "Ada Lovelace")

        class Father(Person):
            children = sequence_attribute(
                value_type=Person,
                reaction=unique_attributes("full_name"),
                parent=True
            )

        elizabeth = Person("Elizabeth Leigh")
        ada = Person("Ada Byron")
        clara = Person("Clara Byron")

        george = Father("George Byron")
        george.children.append(elizabeth, ada, clara)

        self.assertIs(elizabeth.hierarchy.parent, george.children)
        self.assertIs(george.children.hierarchy.parent, george)

        class Family(Object):
            history = history_attribute()
            father = attribute(value_type=Father, parent=True)

            def __init__(self, father):
                self.father = father

        family = Family(Father("George Byron"))

        elizabeth = Person("Elizabeth Leigh")
        ada = Person("Ada Byron")
        clara = Person("Clara Byron")

        family.father.children.append(elizabeth)
        family.father.children.append(ada)
        family.father.children.append(clara)

        self.assertEqual(len(family.father.children), 3)
        family.history.undo()
        self.assertEqual(len(family.father.children), 2)
        family.history.undo()
        self.assertEqual(len(family.father.children), 1)
        family.history.undo()
        self.assertEqual(len(family.father.children), 0)


if __name__ == "__main__":
    unittest.main()
