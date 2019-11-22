import re

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class StatementsField(models.CharField):
    _relation = re.compile(r'(<=|>=|=)')

    def __init__(self, max_length=200, blank=True, **kwargs):
        if kwargs.get('null'):
            raise NotImplementedError("StatementsField can't be null.")
        kwargs['null'] = False
        super().__init__(max_length=max_length, blank=blank, **kwargs)

    @staticmethod
    def get_prep_value(value):
        return ','.join((''.join(statement) for statement in value))

    @classmethod
    def to_python(cls, value):
        assert value is not None

        if isinstance(value, list):
            return value

        statements = [s for s in (s.strip() for s in value.split(',')) if s]
        splitted_statements = map(cls._relation.split, statements)
        valid_statements = [s for s in splitted_statements if len(s) == 3]

        if len(statements) != len(valid_statements):
            raise ValidationError(
                _("Each statement must contain =, <= or >=."), code='invalid')

        return valid_statements
