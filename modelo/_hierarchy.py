# -*- coding: utf-8 -*-
"""Parent-Child hierarchy component."""

from weakref import ref
from collections import Counter, namedtuple, deque
from typing import Iterator, Optional, FrozenSet

from ._model import Model
from ._component import Component
from ._constants import DEAD_REF
from ._exceptions import (
    AlreadyParentedError,
    NotParentedError,
    ParentCycleError,
    MultipleParentingError,
    MultipleUnparentingError,
)


class ChildrenUpdates(namedtuple("ChildrenUpdates", "adoptions releases")):
    """Describes a change in children."""

    def __invert__(self):
        # type: () -> ChildrenUpdates
        """Get inverted."""
        return ChildrenUpdates(adoptions=self.releases, releases=self.adoptions)


class Hierarchy(Component):
    """Parent-child hierarchy node."""

    __slots__ = ("__parent_ref", "__last_parent_ref", "__children")

    def __init__(self, model):
        # type: (Model) -> None
        """Initialize."""
        super(Hierarchy, self).__init__(model)
        self.__parent_ref = DEAD_REF
        self.__last_parent_ref = DEAD_REF
        self.__children = set()

    def prepare_children_updates(self, children_count):
        # type: (Counter[Model, int]) -> ChildrenUpdates
        """Prepare children updates."""
        adoptions = set()
        releases = set()
        for child, count in children_count.items():
            child_hierarchy = child.__hierarchy__
            if count == 1:
                child_parent = child_hierarchy.parent
                if child_parent is not None:
                    raise AlreadyParentedError(
                        "{} is already parented to {}, cannot parent it to {}".format(
                            child, child_parent, self.model
                        )
                    )
                for parent in self.iter_up():
                    if parent is child:
                        raise ParentCycleError(
                            "parent cycle detected between {} and {}".format(
                                child, self.model
                            )
                        )
                adoptions.add(child)
            elif count == -1:
                if not self.has_child(child):
                    raise NotParentedError(
                        "{} is not a child of {}".format(child, self.model)
                    )
                releases.add(child)
            elif count > 1:
                raise MultipleParentingError(
                    "{} cannot be parented to {} more than once".format(
                        child, self.model
                    )
                )
            elif count < -1:
                raise MultipleUnparentingError(
                    "{} cannot be unparented from {} more than once".format(
                        child, self.model
                    )
                )
        return ChildrenUpdates(
            adoptions=frozenset(adoptions), releases=frozenset(releases)
        )

    def update_children(self, children_updates):
        # type: (ChildrenUpdates) -> None
        """Perform children adoptions and/or releases."""
        for adoption in children_updates.adoptions:
            adoption_hierarchy = adoption.__hierarchy__
            adoption_hierarchy.__parent_ref = ref(self.model)
            adoption_hierarchy.__last_parent_ref = adoption_hierarchy.__parent_ref
            self.__children.add(adoption)
        for release in children_updates.releases:
            release_hierarchy = release.__hierarchy__
            release_hierarchy.__parent_ref = DEAD_REF
            self.__children.remove(release_hierarchy.model)

    def has_parent(self):
        # type: () -> bool
        """Whether has a parent."""
        return self.parent is not None

    def has_last_parent(self):
        # type: () -> bool
        """Whether had a parent."""
        return self.last_parent is not None

    def has_child(self, child):
        # type: (Model) -> bool
        """Whether has a specific child."""
        return child in self.__children

    def iter_children(self):
        # type: () -> Iterator[Model, ...]
        """Iterate over children."""
        for child in self.__children:
            yield child

    def iter_up(self, inclusive=True):
        # type: (bool) -> Iterator[Model, ...]
        """Iterate up the tree."""
        if inclusive:
            yield self.model
        parent = self.parent
        while parent is not None:
            yield parent
            parent_hierarchy = parent.__hierarchy__
            parent = parent_hierarchy.parent

    def iter_down(self, inclusive=False, depth_first=False):
        # type: (bool, bool) -> Iterator[Model, ...]
        """Iterate down the tree."""
        if inclusive:
            yield self.model
        if depth_first:
            for child in self.iter_children():
                child_hierarchy = child.__hierarchy__
                for grandchild in child_hierarchy.iter_down(
                    inclusive=True, depth_first=True
                ):
                    yield grandchild
        else:
            queue = deque(self.iter_children())
            while queue:
                child = queue.popleft()
                yield child
                child_hierarchy = child.__hierarchy__
                queue.extend(child_hierarchy.iter_children())

    @property
    def parent(self):
        # type: () -> Optional[Model]
        """Parent."""
        return self.__parent_ref()

    @property
    def last_parent(self):
        # type: () -> Optional[Model]
        """Last parent."""
        return self.__last_parent_ref()

    @property
    def children(self):
        # type: () -> FrozenSet[Model, ...]
        """Children."""
        return frozenset(self.__children)
