# -*- coding: utf-8 -*-
"""Frozen data structures."""

try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc

try:
    from inspect import Parameter, signature
except ImportError:
    Parameter = None
    signature = None
    try:
        from inspect import getfullargspec as getargspec
    except ImportError:
        from inspect import getargspec

from attr import attributes as attributes
from attr import attr as field
from abc import ABCMeta, abstractmethod
from slotted import SlottedHashable, SlottedSequence, SlottedMapping, SlottedSet
from pyrsistent import pvector, pmap, pset
from six import with_metaclass

__all__ = [
    "FrozenStructure",
    "FrozenList",
    "FrozenDict",
    "FrozenSet",
    "FrozenObject",
    "field",
    "transform",
    "discard",
    "match_any",
]

_pvector = pvector([])
_pmap = pmap({})
_pset = pset(set())

_PVector = type(_pvector)
_PMap = type(_pmap)
_PSet = type(_pset)


class FrozenStructure(with_metaclass(ABCMeta, object)):
    @abstractmethod
    def __init__(self, initial):
        raise NotImplementedError()

    @abstractmethod
    def __evolver__(self):
        raise NotImplementedError()


class FrozenList(SlottedHashable, SlottedSequence):

    __slots__ = ("__store",)

    def __init__(self, initial=_pvector):
        # type: (collections_abc.Iterable) -> None
        if isinstance(initial, _PVector):
            self.__store = initial
        elif isinstance(initial, FrozenList):
            self.__store = initial.__store
        else:
            self.__store = pvector(initial)

    def __repr__(self):
        return "{}({})".format(type(self).__name__, list(self.__store))

    __str__ = __repr__

    def __hash__(self):
        return hash(self.__store)

    def __getitem__(self, item):
        return self.__store[item]

    def __len__(self):
        return len(self.__store)

    def __evolver__(self):
        return self.__store.evolver()


getattr(FrozenStructure, "register")(FrozenList)


class FrozenDict(SlottedHashable, SlottedMapping):
    __slots__ = ("__store",)

    def __init__(self, initial=_pmap):
        # type: (collections_abc.Mapping) -> None
        if isinstance(initial, _PMap):
            self.__store = initial
        elif isinstance(initial, FrozenList):
            self.__store = initial.__store
        else:
            self.__store = pmap(initial)

    def __repr__(self):
        return "{}({})".format(type(self).__name__, dict(self.__store))

    __str__ = __repr__

    def __hash__(self):
        return hash(self.__store)

    def __getitem__(self, key):
        return self.__store[key]

    def __len__(self):
        return len(self.__store)

    def __iter__(self):
        for key in self.__store:
            yield key

    def __evolver__(self):
        return self.__store.evolver()


getattr(FrozenStructure, "register")(FrozenDict)


class FrozenSet(SlottedHashable, SlottedSet):
    __slots__ = ("__store",)

    def __init__(self, initial=_pset):
        # type: (collections_abc.Set) -> None
        if isinstance(initial, _PSet):
            self.__store = initial
        elif isinstance(initial, FrozenList):
            self.__store = initial.__store
        else:
            self.__store = pset(initial)

    def __repr__(self):
        return "{}({})".format(type(self).__name__, list(self.__store))

    __str__ = __repr__

    def __hash__(self):
        return hash(self.__store)

    def __contains__(self, value):
        return value in self.__store

    def __len__(self):
        return len(self.__store)

    def __iter__(self):
        for value in self.__store:
            yield value

    def __evolver__(self):
        return self.__store.evolver()


getattr(FrozenStructure, "register")(FrozenSet)


class FrozenObjectMeta(type):
    @staticmethod
    def __new__(mcs, name, bases, dct):
        if "__init__" in dct:
            if all(not isinstance(b, FrozenObjectMeta) for b in bases):
                dct = dict(dct)
                dct.pop("__init__")
            else:
                error = "cannot implement '__init__' on frozen class '{}'".format(name)
                raise TypeError(error)
        return attributes(frozen=True)(
            super(FrozenObjectMeta, mcs).__new__(mcs, name, bases, dct)
        )


class FrozenObject(with_metaclass(FrozenObjectMeta, object)):
    def __init__(self, **field_values):
        raise RuntimeError("cannot implement '__init__' on ")

    def __evolver__(self):
        return pmap(self.__dict__).evolver()


getattr(FrozenStructure, "register")(FrozenObject)


def transform(structure, transformations):
    r = structure
    for path, command in _chunks(transformations, 2):
        r = _do_to_path(r, path, command)
    return r


def discard(evolver, key):
    """Discard the element and returns a structure without the discarded elements."""
    try:
        del evolver[key]
    except KeyError:
        pass


def match_any(_):
    """Matcher that matches any value."""
    return True


def _chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]


def _do_to_path(structure, path, command):
    if not path:
        return command(structure) if callable(command) else command

    kvs = _get_keys_and_values(structure, path[0])
    return _update_structure(structure, kvs, path[1:], command)


def _items(structure):
    try:
        return structure.items()
    except AttributeError:
        return list(enumerate(structure))


def _get(structure, key, default):
    try:
        if hasattr(structure, "__getitem__"):
            return structure[key]
        return getattr(structure, key)
    except (IndexError, KeyError):
        return default


def _get_keys_and_values(structure, key_spec):
    if callable(key_spec):
        # Support predicates as callable objects in the path
        arity = _get_arity(key_spec)

        # Unary predicates are called with the "key" of the path - eg a key in a
        # mapping, an index in a sequence.
        if arity == 1:
            return [(k, v) for k, v in _items(structure) if key_spec(k)]

        # Binary predicates are called with the key and the corresponding value
        elif arity == 2:
            return [(k, v) for k, v in _items(structure) if key_spec(k, v)]

        else:
            raise ValueError("callable in transform path must take 1 or 2 arguments")

    # Non-callables are used as-is as a key.
    return [(key_spec, _get(structure, key_spec, pmap()))]


if signature is not None:

    def _get_arity(f):
        return sum(
            1
            for p in signature(f).parameters.values()
            if p.default is Parameter.empty
            and p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
        )


else:

    def _get_arity(f):
        arg_spec = getargspec(f)
        return len(arg_spec.args) - len(arg_spec.defaults or ())


def _update_structure(structure, kvs, path, command):
    is_store = not isinstance(structure, FrozenStructure)
    if is_store:
        is_object = False
        e = structure.evolver()
    else:
        is_object = isinstance(structure, FrozenObject)
        e = structure.__evolver__()
    if not path and command is discard:
        for k, v in reversed(kvs):
            discard(e, k)
    else:
        for k, v in kvs:
            result = _do_to_path(v, path, command)
            if result is not v:
                e[k] = result
    if is_store:
        return e.persistent()
    else:
        if is_object:
            if e.is_dirty():
                return type(structure)(**e.persistent())
            else:
                return structure
        else:
            return type(structure)(e.persistent())
