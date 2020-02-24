from abc import ABCMeta, abstractmethod
from typing import Type, Dict, Tuple, Any, Optional

from .utils import cast


class FieldMeta(ABCMeta):
    _instances: Dict[Tuple[type, Tuple[Any, ...], Tuple[Tuple[str, Any], ...]], 'Field'] = {}

    # Inspired by https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python#6798042
    def __call__(cls, *args, **kwargs):
        key = (cls, args, tuple(kwargs.items()))
        if key not in cls._instances:
            cls._instances[key] = super().__call__(*args, **kwargs)
        return cls._instances[key]


class Field(metaclass=FieldMeta):
    @abstractmethod
    def parse(self, inp: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def unparse(self, value: Any) -> str:
        raise NotImplementedError


class TupleField(Field):
    def __init__(self, typ, sep=','):
        self.type = typ
        self.separator = sep

    def parse(self, inp):
        typ, sep = self.type, self.separator
        tokens = inp.strip().split(sep)
        return [cast(item.strip(), typ) for item in tokens if item.strip()]

    def unparse(self, value):
        return self.separator.join((str(x) for x in value))


class BuiltinTypeField(Field):
    TYPE: Optional[Type] = None

    @classmethod
    def parse(cls, inp):
        return cast(inp, cls.TYPE)

    @classmethod
    def unparse(cls, value):
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
