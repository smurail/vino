from ast import literal_eval
from typing import Type, Optional
from django.utils.dateparse import parse_datetime

from ...utils import cast
from .field import Field


class TupleField(Field):
    def __init__(self, typ, sep=',', **kwargs):
        self.type = typ
        self.separator = sep
        super().__init__(**kwargs)

    def do_parse(self, inp):
        typ, sep = self.type, self.separator
        tokens = inp.strip().split(sep)
        return [cast(item.strip(), typ) for item in tokens if item.strip()]

    def do_unparse(self, value):
        return self.separator.join((str(x) for x in value))


class LiteralField(Field):
    def do_parse(self, inp):
        return literal_eval(inp)

    def do_unparse(self, value):
        return repr(value)


class DateTimeField(Field):
    def do_parse(self, inp):
        return parse_datetime(inp)

    def do_unparse(self, value):
        return value.isoformat()


class BuiltinTypeField(Field):
    TYPE: Optional[Type] = None

    @classmethod
    def do_parse(cls, inp):
        return cast(inp, cls.TYPE)

    @classmethod
    def do_unparse(cls, value):
        return str(value)


class IntegerField(BuiltinTypeField):
    TYPE = int


class StringField(BuiltinTypeField):
    TYPE = str
