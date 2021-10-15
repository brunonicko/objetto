
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator, TypeVar

    _T = TypeVar("_T")

__all__ = ["unique_iterator"]


def unique_iterator(iterator):
    # type: (Iterator[_T]) -> Iterator[_T]
    seen = set()
    for value in iterator:
        if value in seen:
            continue
        seen.add(value)
        yield value
