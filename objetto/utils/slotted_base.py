from six import with_metaclass
from slotted import SlottedABCMeta, SlottedABC
from basicco import BaseMeta, Base, freeze

__all__ = ["SlottedBaseMeta", "SlottedBase"]


class SlottedBaseMeta(BaseMeta, SlottedABCMeta):
    pass


@freeze
class SlottedBase(with_metaclass(SlottedBaseMeta, Base, SlottedABC)):
    __slots__ = ()
