from __future__ import annotations

import inspect

from abc import ABCMeta, abstractmethod
from typing import Dict, Tuple, Any


class FieldMeta(ABCMeta):
    _instances: Dict[Tuple[type, Tuple[Any, ...], Tuple[Tuple[str, Any], ...]], Field] = {}

    # Inspired by https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python#6798042
    def __call__(cls, *args: Any, **kwargs: Any) -> Field:
        # Build a dict of all default values of constructor parameters for
        # this class and its ancestors
        defaults: Dict[str, Any] = {}
        for subcls in cls.mro():
            parameters = inspect.signature(subcls.__init__).parameters.items()  # type: ignore[misc]
            defaults.update(**{
                k: v.default for k, v in parameters
                if v.default is not inspect.Parameter.empty
            })
        # Add default parameters to current parameters
        defaults.update(**kwargs)
        kwargs = defaults
        # We can now build the complete signature of this field
        key = (cls, args, tuple(kwargs.items()))
        if key not in cls._instances:
            cls._instances[key] = super().__call__(*args, **kwargs)
        return cls._instances[key]


class Field(metaclass=FieldMeta):
    def __init__(self, *args: Any, optional: bool = True, **kwargs: Any):
        self.optional = optional

    def parse(self, inp: str) -> Any:
        if self.optional and inp.lower() == 'none':
            return None
        return self.do_parse(inp)

    def unparse(self, value: Any) -> str:
        if self.optional and value is None:
            return 'none'
        return self.do_unparse(value)

    @abstractmethod
    def do_parse(self, inp: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def do_unparse(self, value: Any) -> str:
        raise NotImplementedError
