from slotted import SlottedABC, SlottedABCMeta
from basicco import BaseMeta, Base
from pytest import main

from objetto.utils.slotted_base import SlottedBaseMeta, SlottedBase


def test_inheritance():
    assert issubclass(SlottedBaseMeta, SlottedABCMeta)
    assert issubclass(SlottedBaseMeta, BaseMeta)

    assert isinstance(SlottedBase, SlottedBaseMeta)

    assert issubclass(SlottedBase, Base)
    assert issubclass(SlottedBase, SlottedABC)


if __name__ == "__main__":
    main()
