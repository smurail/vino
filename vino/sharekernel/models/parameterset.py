from itertools import chain
from collections import OrderedDict

from django.db import models
from django.db.models import Count, Q

from .entity import Entity
from .viabilityproblem import ViabilityProblem, ViabilityProblemQuerySet
from .symbol import Symbol


class ParameterSetQuerySet(ViabilityProblemQuerySet):
    def with_dimension_of(self, type, name):
        opts = {name: Count('vp__symbols', filter=Q(vp__symbols__type=type))}
        return self.annotate(**opts)


class ParameterSet(Entity):
    PREFIX = 'parameters.'
    IDENTITY = ('vp', 'dynamics', 'constraints', 'target')
    METADATA_TO_FIELD = {
        'dynamicsparametervalues': 'dynamics',
        'stateconstraintparametervalues': 'constraints',
        'targetparametervalues': 'target',
    }

    vp = models.ForeignKey(ViabilityProblem, models.CASCADE,
                           related_name="parametersets",
                           verbose_name="Viability problem")
    dynamics = models.CharField(max_length=200, blank=True)
    constraints = models.CharField(max_length=200, blank=True)
    target = models.CharField(max_length=200, blank=True)

    objects = ParameterSetQuerySet.as_manager()

    def to_dict(self):
        types = [Symbol.DYNAMICS, Symbol.CONSTRAINT, Symbol.TARGET]
        # List all names from symbols within `types`
        symbols = self.vp.symbols.filter(type__in=types).order_by('type').all()
        sorted_symbols = sorted(symbols, key=lambda s: types.index(s.type))
        names = (symbol.name for symbol in sorted_symbols)
        # List all values from those types
        values_set = (self.dynamics, self.constraints, self.target)
        values = chain.from_iterable((x.split(',') for x in values_set))
        return OrderedDict(zip(names, values))

    def __str__(self):
        fields = ('='.join(item) for item in self.to_dict().items())
        return f'{self.vp}: {", ".join(fields)}'
