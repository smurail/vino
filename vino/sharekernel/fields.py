import re

from Equation import Expression as _Expression

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Expression(_Expression):
    def __init__(self, expression, argorder=[], *args, **kwargs):
        self.value = expression
        super().__init__(expression, argorder, *args, **kwargs)

    def __str__(self):
        return self.value


class Statements:
    def __init__(self, statements, time_type=None):
        self.statements = statements
        self.time_type = time_type

    def __len__(self):
        return len(self.statements)

    def __iter__(self):
        return iter(self.statements)

    def __setitem__(self, index, value):
        self.statements[index] = value

    def __getitem__(self, index):
        return self.statements[index]

    def __eq__(self, other):
        return (isinstance(other, Statements) and
            (self.statements, self.time_type) == (other.statements, other.time_type))

    def __repr__(self):
        return 'Statements(%r)' % self.statements


class StatementsField(models.CharField):
    RELATIONS = ('=', '<=', '>=')

    def __init__(self, types=None, max_length=200, blank=True, **kwargs):
        if kwargs.get('null'):
            raise NotImplementedError("StatementsField can't be null.")
        super().__init__(max_length=max_length, blank=blank, **kwargs)
        self.types = types or (None, None)
        # Compile regex used to split relations (ie. "x=y", "a>=b"...)
        self._relation = re.compile(
            r'\s*(%s)\s*' % '|'.join(self.RELATIONS))

    def split(self, statement):
        return tuple(filter(None, map(str.strip, self._relation.split(statement))))

    @staticmethod
    def get_prep_value(value):
        return ','.join((''.join(map(str, statement)) for statement in value))

    def to_python(self, value):
        assert value is not None

        if isinstance(value, Statements):
            return value

        statements = [s for s in (s.strip() for s in value.split(',')) if s]
        splitted_statements = (self.split(stmt) for stmt in statements)
        valid_statements = [s for s in splitted_statements if len(s) == 3]

        if len(statements) != len(valid_statements):
            raise ValidationError(
                _("Each statement must contain one of: %(relations)s."),
                params={'relations': ', '.join(self.RELATIONS)},
                code='invalid')

        try:
            for i, (left, op, right) in enumerate(valid_statements):
                valid_statements[i] = (left, op, Expression(right))
        except: # noqa
            raise ValidationError(
                _("Invalid syntax: %(value)s"),
                params={'value': right},
                code='invalid')

        return valid_statements


class EquationsField(StatementsField):
    RELATIONS = ('=')


class InequationsField(StatementsField):
    RELATIONS = ('<=', '>=')
