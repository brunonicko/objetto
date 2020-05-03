# -*- coding: utf-8 -*-
"""Parent-Child tree hierarchy."""

from abc import abstractmethod
from weakref import ref
from collections import Counter, namedtuple, deque
from typing import Iterator, Optional, FrozenSet
from slotted import Slotted

from .._base.constants import DEAD_WEAKREF
from .._base.exceptions import ObjettoError, ObjettoException

__all__ = [
    "HierarchyException",
    "HierarchyError",
    "AlreadyParentedError",
    "NotParentedError",
    "ParentCycleError",
    "MultipleParentingError",
    "MultipleUnparentingError",
    "Hierarchy",
    "HierarchicalMixin",
    "ChildrenUpdates",
    "HierarchyAccess",
    "HierarchyException",
    "HierarchyError",
    "AlreadyParentedError",
    "NotParentedError",
    "ParentCycleError",
    "MultipleParentingError",
    "MultipleUnparentingError",
]


class HierarchyException(ObjettoException):
    """Hierarchy exception."""


class HierarchyError(ObjettoError):
    """Hierarchy error."""


class AlreadyParentedError(HierarchyError):
    """Raised when already parented to another parent."""


class NotParentedError(HierarchyError):
    """Raised when not parented to given parent."""


class ParentCycleError(HierarchyError):
    """Raised when a parent cycle is detected."""


class MultipleParentingError(HierarchyError):
    """Raised when trying to parent more than once."""


class MultipleUnparentingError(HierarchyError):
    """Raised when trying to un-parent more than once."""


class HierarchicalMixin(object):
    """Mix-in class that defines a node object in the hierarchy."""

    __slots__ = ("__weakref__",)

    @abstractmethod
    def __get_hierarchy__(self):
        # type: () -> Hierarchy
        """Get hierarchy."""
        raise NotImplementedError()


class Hierarchy(Slotted):
    """Parent-child hierarchy node."""

    __slots__ = ("__obj_ref", "__parent_ref", "__last_parent_ref", "__children")

    def __init__(self, obj):
        # type: (HierarchicalMixin) -> None
        """Initialize with hierarchical object."""
        self.__obj_ref = ref(obj)
        self.__parent_ref = DEAD_WEAKREF
        self.__last_parent_ref = DEAD_WEAKREF
        self.__children = set()

    def prepare_children_updates(self, children_count):
        # type: (Counter[HierarchicalMixin, int]) -> ChildrenUpdates
        """Prepare children updates."""
        adoptions = set()
        releases = set()
        for child, count in children_count.items():
            child_hierarchy = child.__get_hierarchy__()
            if count == 1:
                child_parent = child_hierarchy.parent
                if child_parent is not None:
                    error = (
                        "{} is already parented to {}, cannot parent it to {}"
                    ).format(child, child_parent, self.obj)
                    raise AlreadyParentedError(error)
                for parent in self.iter_up():
                    if parent is child:
                        error = "parent cycle detected between {} and {}".format(
                            child, self.obj
                        )
                        raise ParentCycleError(error)
                adoptions.add(child)
            elif count == -1:
                if not self.has_child(child):
                    error = "{} is not a child of {}".format(child, self.obj)
                    raise NotParentedError(error)
                releases.add(child)
            elif count > 1:
                error = "{} cannot be parented to {} more than once".format(
                    child, self.obj
                )
                raise MultipleParentingError(error)
            elif count < -1:
                error = "{} cannot be unparented from {} more than once".format(
                    child, self.obj
                )
                raise MultipleUnparentingError(error)
        return ChildrenUpdates(
            adoptions=frozenset(adoptions), releases=frozenset(releases)
        )

    def update_children(self, children_updates):
        # type: (ChildrenUpdates) -> None
        """Perform children adoptions and/or releases."""
        for adoption in children_updates.adoptions:
            adoption_hierarchy = adoption.__get_hierarchy__()
            adoption_hierarchy.__parent_ref = ref(self.obj)
            adoption_hierarchy.__last_parent_ref = adoption_hierarchy.__parent_ref
            self.__children.add(adoption)
        for release in children_updates.releases:
            release_hierarchy = release.__get_hierarchy__()
            release_hierarchy.__parent_ref = DEAD_WEAKREF
            self.__children.remove(release_hierarchy.obj)

    def has_parent(self):
        # type: () -> bool
        """Whether has a parent."""
        return self.parent is not None

    def has_last_parent(self):
        # type: () -> bool
        """Whether had a parent."""
        return self.last_parent is not None

    def has_child(self, child):
        # type: (HierarchicalMixin) -> bool
        """Whether has a specific child."""
        return child in self.__children

    def iter_children(self):
        # type: () -> Iterator[HierarchicalMixin, ...]
        """Iterate over children."""
        for child in self.__children:
            yield child

    def iter_up(self, inclusive=True):
        # type: (bool) -> Iterator[HierarchicalMixin, ...]
        """Iterate up the tree."""
        if inclusive:
            yield self.obj
        parent = self.parent
        while parent is not None:
            yield parent
            parent_hierarchy = parent.__get_hierarchy__()
            parent = parent_hierarchy.parent

    def iter_down(self, inclusive=False, depth_first=False):
        # type: (bool, bool) -> Iterator[HierarchicalMixin, ...]
        """Iterate down the tree."""
        if inclusive:
            yield self.obj
        if depth_first:
            for child in self.iter_children():
                child_hierarchy = child.__get_hierarchy__()
                for grandchild in child_hierarchy.iter_down(
                    inclusive=True, depth_first=True
                ):
                    yield grandchild
        else:
            queue = deque(self.iter_children())
            while queue:
                child = queue.popleft()
                yield child
                child_hierarchy = child.__get_hierarchy__()
                queue.extend(child_hierarchy.iter_children())

    @property
    def obj(self):
        # type: () -> HierarchicalMixin
        """Hierarchical object."""
        obj = self.__obj_ref()
        if obj is None:
            error = "object is no longer alive"
            raise ReferenceError(error)
        return obj

    @property
    def parent(self):
        # type: () -> Optional[HierarchicalMixin]
        """Parent."""
        return self.__parent_ref()

    @property
    def last_parent(self):
        # type: () -> Optional[HierarchicalMixin]
        """Last parent."""
        return self.__last_parent_ref()

    @property
    def children(self):
        # type: () -> FrozenSet[HierarchicalMixin, ...]
        """Children."""
        return frozenset(self.__children)


class ChildrenUpdates(namedtuple("ChildrenUpdates", "adoptions releases")):
    """Describes a change in children."""

    def __invert__(self):
        # type: () -> ChildrenUpdates
        """Get inverted."""
        return ChildrenUpdates(adoptions=self.releases, releases=self.adoptions)


class HierarchyAccess(Slotted):
    """Provides read-only access to the hierarchy."""

    __slots__ = ("__hierarchy",)

    def __init__(self, hierarchy):
        # type: (Hierarchy) -> None
        """Initialize with hierarchy."""
        self.__hierarchy = hierarchy

    def has_parent(self):
        # type: () -> bool
        """Whether has a parent."""
        return self.__hierarchy.has_parent()

    def has_last_parent(self):
        # type: () -> bool
        """Whether had a parent."""
        return self.__hierarchy.has_last_parent()

    def has_child(self, child):
        # type: (HierarchicalMixin) -> bool
        """Whether has a specific child."""
        return self.__hierarchy.has_child(child)

    def iter_children(self):
        # type: () -> Iterator[HierarchicalMixin, ...]
        """Iterate over children."""
        for child in self.__hierarchy.iter_children():
            yield child

    def iter_up(self, inclusive=True):
        # type: (bool) -> Iterator[HierarchicalMixin, ...]
        """Iterate up the tree."""
        for obj in self.__hierarchy.iter_up(inclusive=inclusive):
            yield obj

    def iter_down(self, inclusive=False, depth_first=False):
        # type: (bool, bool) -> Iterator[HierarchicalMixin, ...]
        """Iterate down the tree."""
        for obj in self.__hierarchy.iter_down(
            inclusive=inclusive, depth_first=depth_first
        ):
            yield obj

    @property
    def parent(self):
        # type: () -> Optional[HierarchicalMixin]
        """Parent."""
        return self.__hierarchy.parent

    @property
    def last_parent(self):
        # type: () -> Optional[HierarchicalMixin]
        """Last parent."""
        return self.__hierarchy.last_parent

    @property
    def children(self):
        # type: () -> FrozenSet[HierarchicalMixin, ...]
        """Children."""
        return self.__hierarchy.children
