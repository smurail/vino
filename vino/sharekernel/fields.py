from functools import lru_cache

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from vino.core.statements import (Statements, Equations, Inequations,
                                  StatementsError)


class StatementsField(models.CharField):
    STATEMENTS_CLS = Statements

    def __init__(self, types=None, max_length=200, blank=True, **kwargs):
        if kwargs.get('null'):
            raise NotImplementedError("StatementsField can't be null.")
        super().__init__(max_length=max_length, blank=blank, **kwargs)
        self.types = types or (None, None)

    @staticmethod
    def get_prep_value(value):
        return str(value)

    # XXX See https://stackoverflow.com/questions/14756790/why-are-uncompiled-repeatedly-used-regexes-so-much-slower-in-python-3
    @classmethod
    @lru_cache(typed=True)
    def to_python(cls, value):
        assert value is not None

        if isinstance(value, Statements):
            return value

        try:
            return cls.STATEMENTS_CLS(value)
        except StatementsError as e:
            message, params = e.args
            raise ValidationError(_(message), params=params, code='invalid')

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)


class EquationsField(StatementsField):
    STATEMENTS_CLS = Equations


class InequationsField(StatementsField):
    STATEMENTS_CLS = Inequations
