# -*- coding: utf-8 -*-

import pytest
from six import with_metaclass

from objetto import Data, data_constant_attribute


def test_attribute_type_check():
    class CustomMeta(type):
        pass

    class Custom(with_metaclass(CustomMeta, object)):
        pass

    class MyData(Data):
        CustomType = data_constant_attribute(Custom, abstracted=True, subtypes=True)

    class OtherCustomMeta(CustomMeta):
        pass

    class OtherCustom(with_metaclass(OtherCustomMeta, Custom)):
        pass

    class MyOtherData(MyData):
        CustomType = OtherCustom

    assert MyOtherData


if __name__ == "__main__":
    pytest.main()
