import estruttura
from basicco import basic_data
from tippo import Any, Callable, Iterable, Type, TypeVar

from .serializers import Serializer, TypedSerializer

__all__ = ["Relationship"]


T = TypeVar("T")


class Relationship(estruttura.Relationship[T]):
    __slots__ = ("_parent", "_history")

    def __init__(
        self,
        converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
        validator=None,  # type: Callable[[Any], None] | str | None
        types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
        subtypes=False,  # type: bool
        serializer=TypedSerializer(),  # type: Serializer[T] | None
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
        parent=True,  # type: bool
        history=None,  # type: bool | None
    ):
        if history is None:
            if not parent:
                error = "history can't be True if parent is False"
                raise ValueError(error)
            history = True

        self._parent = bool(parent)
        self._history = bool(history)

        super(Relationship, self).__init__(
            converter=converter,
            validator=validator,
            types=types,
            subtypes=subtypes,
            serializer=serializer,
            extra_paths=extra_paths,
            builtin_paths=builtin_paths,
        )

    def to_items(self, usecase=None):
        # type: (basic_data.ItemUsecase | None) -> list[tuple[str, Any]]
        """
        Convert to items.

        :param usecase: Usecase.
        :return: Items.
        """
        return super(Relationship, self).to_items() + [
            ("parent", self.parent),
            ("history", self.history),
        ]

    @property
    def parent(self):
        return self._parent

    @property
    def history(self):
        return self._history
