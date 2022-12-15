import estruttura
from tippo import Any, Callable, Iterable, Type, TypeVar

from .serializers import Serializer, TypedSerializer

__all__ = ["Relationship"]


T = TypeVar("T")


class Relationship(estruttura.Relationship[T]):
    __slots__ = ()

    def __init__(
        self,
        converter=None,  # type: Callable[[Any], T] | Type[T] | str | None
        validator=None,  # type: Callable[[Any], None] | str | None
        types=(),  # type: Iterable[Type[T] | str | None] | Type[T] | str | None
        subtypes=False,  # type: bool
        serializer=TypedSerializer(),  # type: Serializer[T] | None
        extra_paths=(),  # type: Iterable[str]
        builtin_paths=None,  # type: Iterable[str] | None
    ):
        super(Relationship, self).__init__(
            converter=converter,
            validator=validator,
            types=types,
            subtypes=subtypes,
            serializer=serializer,
            extra_paths=extra_paths,
            builtin_paths=builtin_paths,
        )
