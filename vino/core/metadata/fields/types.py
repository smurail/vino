from ast import literal_eval
from typing import TypeVar, Type, Optional, Any, Tuple
from django.utils.dateparse import parse_datetime
from datetime import datetime

from .field import Field


T = TypeVar('T', bound=int)


def cast(to_type: Type[T], value: Any) -> T:
    try:
        if isinstance(value, to_type):
            return value
        return to_type(value)
    except (ValueError, TypeError):
        return to_type()


class TupleField(Field):
    def __init__(self, typ: Type, sep: str = ',', **kwargs: Any):
        self.type = typ
        self.separator = sep
        super().__init__(**kwargs)

    def do_parse(self, inp: str) -> Tuple:
        typ, sep = self.type, self.separator
        tokens = inp.strip().split(sep)
        return tuple(cast(typ, item.strip()) for item in tokens if item.strip())

    def do_unparse(self, value: Any) -> str:
        return self.separator.join((str(x) for x in value))


class LiteralField(Field):
    def do_parse(self, inp: str) -> Any:
        return literal_eval(inp)

    def do_unparse(self, value: Any) -> str:
        return repr(value)


class DateTimeField(Field):
    def do_parse(self, inp: str) -> Optional[datetime]:
        return parse_datetime(inp)

    def do_unparse(self, value: Optional[datetime]) -> str:
        return '' if value is None else value.isoformat()


class BuiltinTypeField(Field):
    TYPE: Type

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls is BuiltinTypeField:
            raise TypeError(f"Can't instantiate abstract class {cls.__name__} directly")
        return super().__new__(cls)

    @classmethod
    def do_parse(cls, inp: str) -> Any:
        return cast(cls.TYPE, inp)

    @classmethod
    def do_unparse(cls, value: Any) -> str:
        return str(value)


class IntegerField(BuiltinTypeField):
    TYPE = int


class StringField(BuiltinTypeField):
    TYPE = str
