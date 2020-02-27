import inspect

from abc import ABCMeta, abstractmethod
from typing import Type, Dict, Tuple, Any, Optional
from datetime import datetime
from ast import literal_eval

from django.utils.dateparse import parse_datetime

from .utils import cast


class FieldMeta(ABCMeta):
    _instances: Dict[Tuple[type, Tuple[Any, ...], Tuple[Tuple[str, Any], ...]], 'Field'] = {}

    # Inspired by https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python#6798042
    def __call__(cls, *args, **kwargs):
        # Build a dict of all default values of constructor parameters for
        # this class and its ancestors
        defaults = {}
        for subcls in cls.mro():
            parameters = inspect.signature(subcls.__init__).parameters.items()
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
    def __init__(self, *args, optional=True, **kwargs):
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


class Metadata(dict):
    """
    MinimalValues = TupleField(float, sep=' ')
    MaximalValues = TupleField(float, sep=' ')
    PointNumberPerAxis = TupleField(int)
    PointSize = IntegerField()
    ColumnDescription = TupleField(str)
    dataformat__name = StringField()
    dataformat__columns = TupleField(str)
    viabilityproblem = Entity()
    """

    FIELDS: Dict[str, Field] = {
        'MinimalValues': TupleField(float, sep=' '),
        'MaximalValues': TupleField(float, sep=' '),
        'PointNumberPerAxis': TupleField(int),
        'PointSize': IntegerField(),
        'ColumnDescription': TupleField(str),
        'dataformat.name': StringField(),
        'dataformat.columns': TupleField(str),
        'viabilityproblem.title': StringField(),
        'viabilityproblem.description': StringField(),
        'results.title': StringField(),
        'results.author': StringField(),
        'results.contact': StringField(),
        'resultformat.title': StringField(),
        'resultformat.description': StringField(),
    }
