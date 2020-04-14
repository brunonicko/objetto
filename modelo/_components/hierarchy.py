# -*- coding: utf-8 -*-
"""Parent-Child hierarchy component."""

from weakref import ref
from collections import Counter, namedtuple, deque
from typing import Iterator, Optional, FrozenSet, Type, cast

from slotted import Slotted
from componente import CompositeMixin, Component

from .._base.exceptions import ModeloException, ModeloError

__all__ = [
    "Hierarchy",
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

DEAD_REF = ref(type("DeadRef", (object,), {"__slots__": ("__weakref__",)})())


class Hierarchy(Slotted, Component):
    """Parent-child hierarchy node."""

    __slots__ = ("__parent_ref", "__last_parent_ref", "__children")

    @staticmethod
    def get_type():
        # type: () -> Type[Hierarchy]
        """Get component key type."""
        return Hierarchy

    def __init__(self, obj):
        # type: (CompositeMixin) -> None
        """Initialize."""
        super(Hierarchy, self).__init__(obj)
        self.__parent_ref = DEAD_REF
        self.__last_parent_ref = DEAD_REF
        self.__children = set()

    @classmethod
    def get_component(cls, obj):
        # type: (CompositeMixin) -> Hierarchy
        """Get hierarchy component of a composite object."""
        return cast(Hierarchy, super(Hierarchy, cls).get_component(obj))

    def prepare_children_updates(self, children_count):
        # type: (Counter[CompositeMixin, int]) -> ChildrenUpdates
        """Prepare children updates."""
        adoptions = set()
        releases = set()
        for child, count in children_count.items():
            child_hierarchy = cast(Hierarchy, self.get_component(child))
            if count == 1:
                child_parent = child_hierarchy.parent
                if child_parent is not None:
                    raise AlreadyParentedError(
                        "{} is already parented to {}, cannot parent it to {}".format(
                            child, child_parent, self.obj
                        )
                    )
                for parent in self.iter_up():
                    if parent is child:
                        raise ParentCycleError(
                            "parent cycle detected between {} and {}".format(
                                child, self.obj
                            )
                        )
                adoptions.add(child)
            elif count == -1:
                if not self.has_child(child):
                    raise NotParentedError(
                        "{} is not a child of {}".format(child, self.obj)
                    )
                releases.add(child)
            elif count > 1:
                raise MultipleParentingError(
                    "{} cannot be parented to {} more than once".format(child, self.obj)
                )
            elif count < -1:
                raise MultipleUnparentingError(
                    "{} cannot be unparented from {} more than once".format(
                        child, self.obj
                    )
                )
        return ChildrenUpdates(
            adoptions=frozenset(adoptions), releases=frozenset(releases)
        )

    def update_children(self, children_updates):
        # type: (ChildrenUpdates) -> None
        """Perform children adoptions and/or releases."""
        for adoption in children_updates.adoptions:
            adoption_hierarchy = cast(Hierarchy, self.get_component(adoption))
            adoption_hierarchy.__parent_ref = ref(self.obj)
            adoption_hierarchy.__last_parent_ref = adoption_hierarchy.__parent_ref
            self.__children.add(adoption)
        for release in children_updates.releases:
            release_hierarchy = cast(Hierarchy, self.get_component(release))
            release_hierarchy.__parent_ref = DEAD_REF
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
        # type: (CompositeMixin) -> bool
        """Whether has a specific child."""
        return child in self.__children

    def iter_children(self):
        # type: () -> Iterator[CompositeMixin, ...]
        """Iterate over children."""
        for child in self.__children:
            yield child

    def iter_up(self, inclusive=True):
        # type: (bool) -> Iterator[CompositeMixin, ...]
        """Iterate up the tree."""
        if inclusive:
            yield self.obj
        parent = self.parent
        while parent is not None:
            yield parent
            parent_hierarchy = cast(Hierarchy, self.get_component(parent))
            parent = parent_hierarchy.parent

    def iter_down(self, inclusive=False, depth_first=False):
        # type: (bool, bool) -> Iterator[CompositeMixin, ...]
        """Iterate down the tree."""
        if inclusive:
            yield self.obj
        if depth_first:
            for child in self.iter_children():
                child_hierarchy = cast(Hierarchy, self.get_component(child))
                for grandchild in child_hierarchy.iter_down(
                    inclusive=True, depth_first=True
                ):
                    yield grandchild
        else:
            queue = deque(self.iter_children())
            while queue:
                child = queue.popleft()
                yield child
                child_hierarchy = cast(Hierarchy, self.get_component(child))
                queue.extend(child_hierarchy.iter_children())

    @property
    def parent(self):
        # type: () -> Optional[CompositeMixin]
        """Parent."""
        return self.__parent_ref()

    @property
    def last_parent(self):
        # type: () -> Optional[CompositeMixin]
        """Last parent."""
        return self.__last_parent_ref()

    @property
    def children(self):
        # type: () -> FrozenSet[CompositeMixin, ...]
        """Children."""
        return frozenset(self.__children)


class ChildrenUpdates(namedtuple("ChildrenUpdates", "adoptions releases")):
    """Describes a change in children."""

    def __invert__(self):
        # type: () -> ChildrenUpdates
        """Get inverted."""
        return ChildrenUpdates(adoptions=self.releases, releases=self.adoptions)


class HierarchyAccess(Slotted):
    """Provides read-only access to the hierarchy component."""

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
        # type: (CompositeMixin) -> bool
        """Whether has a specific child."""
        return self.__hierarchy.has_child(child)

    def iter_children(self):
        # type: () -> Iterator[CompositeMixin, ...]
        """Iterate over children."""
        for child in self.__hierarchy.iter_children():
            yield child

    def iter_up(self, inclusive=True):
        # type: (bool) -> Iterator[CompositeMixin, ...]
        """Iterate up the tree."""
        for obj in self.__hierarchy.iter_up(inclusive=inclusive):
            yield obj

    def iter_down(self, inclusive=False, depth_first=False):
        # type: (bool, bool) -> Iterator[CompositeMixin, ...]
        """Iterate down the tree."""
        for obj in self.__hierarchy.iter_down(
            inclusive=inclusive, depth_first=depth_first
        ):
            yield obj

    @property
    def parent(self):
        # type: () -> Optional[CompositeMixin]
        """Parent."""
        return self.__hierarchy.parent

    @property
    def last_parent(self):
        # type: () -> Optional[CompositeMixin]
        """Last parent."""
        return self.__hierarchy.last_parent

    @property
    def children(self):
        # type: () -> FrozenSet[CompositeMixin, ...]
        """Children."""
        return self.__hierarchy.children


class HierarchyException(ModeloException):
    """Hierarchy exception."""


class HierarchyError(ModeloError, HierarchyException):
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
