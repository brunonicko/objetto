# -*- coding: utf-8 -*-
"""Base model component."""

from weakref import ref
from slotted import Slotted

from ._model import Model


class Component(Slotted):
    """Adds functionality to a model."""

    __slots__ = ("__model_ref", "__internal")

    def __init__(self, model):
        # type: (Model) -> None
        """Initialize with model."""
        self.__model_ref = ref(model)

    @property
    def model(self):
        # type: () -> Model
        """Model."""
        model = self.__model_ref()
        if model is not None:
            return model
        raise ReferenceError("model is no longer alive")
