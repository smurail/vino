from typing import Dict, Any

from .fields import (
    Field, TupleField, IntegerField, StringField, DateTimeField, LiteralField
)


class BaseMetadata(Dict[str, Any]):
    FIELDS: Dict[str, Field] = {}

    @classmethod
    def has_field(cls, field: str) -> bool:
        return field in cls.FIELDS

    @classmethod
    def parse_field(cls, field: str, value: str) -> Any:
        return cls.FIELDS[field].parse(value)

    @classmethod
    def unparse_field(cls, field: str, value: Any) -> str:
        return cls.FIELDS[field].unparse(value)


class Metadata(BaseMetadata):
    FIELDS = {
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
