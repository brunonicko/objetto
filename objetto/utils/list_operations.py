# -*- coding: utf-8 -*-
"""List operations helper functions."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Tuple, Union

__all__ = ["resolve_index", "resolve_continuous_slice", "pre_move"]


def resolve_index(length, index, clamp=False):
    # type: (int, int, bool) -> int
    """
    Resolve index to a positive number.

    :param length: Length of the list.
    :type length: int

    :param index: Input index.
    :type index: int

    :param clamp: Whether to clamp between zero and the length.
    :type clamp: bool

    :return: Resolved index.
    :rtype: int

    :raises IndexError: Index out of range.
    """
    if index < 0:
        index += length
    if clamp:
        if index < 0:
            index = 0
        elif index > length:
            index = length
    elif index < 0 or index >= length:
        error = "index out of range"
        raise IndexError(error)
    return index


def resolve_continuous_slice(length, slc):
    # type: (int, slice) -> Tuple[int, int]
    """
    Resolve continuous slice according to length.

    :param length: Length of the list.
    :type length: int

    :param slc: Continuous slice.
    :type slc: slice

    :return: Index and stop.
    :rtype: tuple[int, int]

    :raises IndexError: Slice is noncontinuous.
    """
    index, stop, step = slc.indices(length)
    if step != 1 or stop < index:
        error = "slice {} is noncontinuous".format(slc)
        raise IndexError(error)
    return index, stop


def pre_move(length, item, target_index):
    # type: (int, Union[slice, int], int) -> Optional[Tuple[int, int, int, int]]
    """
    Perform checks before moving values internally.

    :param length: Length of the list.
    :type length: int

    :param item: Index/slice.
    :type item: int or slice

    :param target_index: Target index.
    :type target_index: int

    :return: None or (index, stop, target index, post index).
    :rtype: None or tuple[int, int, int, int]
    """

    # Resolve slice/index.
    if isinstance(item, slice):
        index, stop = resolve_continuous_slice(length, item)
        if index == stop:
            return None
    else:
        index = resolve_index(length, item)
        stop = index + 1

    # Calculate target index and post index.
    target_index = resolve_index(length, target_index, clamp=True)
    if index <= target_index <= stop:
        return None
    elif target_index > stop:
        post_index = target_index - (stop - index)
    else:
        post_index = target_index

    return index, stop, target_index, post_index
