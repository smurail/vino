from __future__ import annotations

from typing import Mapping, Any, Iterator, Iterable

from .fields import (
    Field, TupleField, IntegerField, StringField, DateTimeField, LiteralField
)


class BaseMetadata(Mapping[str, Any]):
    _fields: dict[str, Field] = {}
    _values: dict[str, Any]

    def __init__(self, *chunks: Iterable, **fields: Any):
        self._values = {}

        for md in chunks:
            items = md.items() if isinstance(md, Mapping) else md
            for k, v in items:
                self._values[k] = v
        for k, v in fields.items():
            self._values[k] = v

    @classmethod
    def is_defined(cls, name: str) -> bool:
        return name in cls._fields

    @classmethod
    def parse(cls, name: str, value: str) -> Any:
        return cls._fields[name].parse(value)

    def __getitem__(self, name: str) -> Any:
        return self._values[name]

    def __iter__(self) -> Iterator[str]:
        return self._values.__iter__()

    def __len__(self) -> int:
        return len(self._values)

    def get_unparsed(self, name: str) -> str:
        return self._fields[name].unparse(self[name])

    def __repr__(self):
        return f'{type(self).__name__}({dict.__repr__(self._values)})'


class Metadata(BaseMetadata):
    _fields = {
        'MinimalValues': TupleField(float, sep=' '),
        'MaximalValues': TupleField(float, sep=' '),
        'PointNumberPerAxis': TupleField(int),
        'PointSize': IntegerField(),
        'ColumnDescription': TupleField(str),
        'dataformat.name': StringField(),
        'dataformat.columns': TupleField(str),
        'dataformat.baraxis': IntegerField(),
        'parameters.dynamicsparametervalues': TupleField(float),
        'parameters.stateconstraintparametervalues': TupleField(float),
        'parameters.targetparametervalues': TupleField(float),
        'resultformat.description': StringField(),
        'resultformat.parameterlist': TupleField(str),
        'resultformat.title': StringField(),
        'results.author': StringField(),
        'results.contact': StringField(),
        'results.formatparametervalues': TupleField(str),
        'results.softwareparametervalues': TupleField(str),
        'results.submissiondate': DateTimeField(),
        'results.title': StringField(),
        'software.author': StringField(),
        'software.contact': StringField(),
        'software.description': StringField(),
        'software.parameters': TupleField(str),
        'software.title': StringField(),
        'software.version': StringField(),
        'software.publication': StringField(),
        'software.website': StringField(),
        'viabilityproblem.admissiblecontroldescription': StringField(),
        'viabilityproblem.controlvariables': LiteralField(),
        'viabilityproblem.description': StringField(),
        'viabilityproblem.dynamicsdescription': StringField(),
        'viabilityproblem.dynamicsparameters': LiteralField(),
        'viabilityproblem.stateconstraintdescription': StringField(),
        'viabilityproblem.stateconstraintparameters': LiteralField(),
        'viabilityproblem.statedefinitiondomain': StringField(),
        'viabilityproblem.statedimension': IntegerField(),
        'viabilityproblem.statevariables': LiteralField(),
        'viabilityproblem.targetdescription': StringField(),
        'viabilityproblem.targetparameters': LiteralField(),
        'viabilityproblem.title': StringField(),
    }
