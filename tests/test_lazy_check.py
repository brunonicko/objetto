# -*- coding: utf-8 -*-

import pytest

from objetto import Object, attribute


class Person(Object):
    friend = attribute("Person")


def test_lazy_check():
    class Worker(Person):
        friend = attribute(Person)

    with pytest.raises(TypeError):

        class Boss(Worker):
            friend = attribute(None)


if __name__ == "__main__":
    pytest.main()
