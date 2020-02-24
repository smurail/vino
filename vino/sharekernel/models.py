from collections import OrderedDict, defaultdict
from itertools import chain

from django.db import models

from django_currentuser.db.models import CurrentUserField

from .fields import EquationsField, InequationsField


class Entity(models.Model):
    class Meta:
        abstract = True

    ACTIVE = 1
    DELETED = 2
    STATES = (
        (ACTIVE, 'Active'),
        (DELETED, 'Deleted'),
    )

    owner = CurrentUserField()
    state = models.IntegerField(choices=STATES, default=ACTIVE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


class Metadata(models.Model):
    class Meta:
        abstract = True

    title = models.CharField(max_length=200)
    description = models.TextField(default='', blank=True)
    publication = models.TextField(default='', blank=True)
    author = models.CharField(max_length=200, default='', blank=True)
    email = models.CharField(max_length=200, default='', blank=True)
    url = models.URLField(default='', blank=True)
    image = models.ImageField(upload_to='images/%Y/%m/%d', blank=True)

    def __str__(self):
        return self.title


class EntityWithMetadata(Entity, Metadata):
    class Meta:
        abstract = True


class Symbol(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['vp', 'name'],
                name='variable_unique'
            )
        ]

    STATE = 'SV'
    CONTROL = 'CV'
    DYNAMICS = 'DP'
    CONSTRAINT = 'SP'
    TARGET = 'TP'
    TYPES = OrderedDict([
        (STATE, 'State variable'),
        (CONTROL, 'Control variable'),
        (DYNAMICS, 'Dynamics parameter'),
        (CONSTRAINT, 'State constraint parameter'),
        (TARGET, 'Target parameter'),
    ])

    vp = models.ForeignKey('ViabilityProblem', models.CASCADE,
                           related_name="symbols",
                           verbose_name="Viability problem")
    type = models.CharField(max_length=2, choices=TYPES.items())
    order = models.IntegerField()
    name = models.CharField(max_length=30)
    longname = models.CharField(max_length=200, blank=True)
    unit = models.CharField(max_length=30, blank=True)

    def __str__(self):
        typ = self.TYPES[self.type]
        longname = (' (%s)' % self.longname if self.longname else '')
        return '%s: %s%s' % (typ, self.name, longname)


class ViabilityProblem(EntityWithMetadata):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['dynamics', 'constraints', 'domain', 'controls', 'target'],
                name='viabilityproblem_unique'
            )
        ]

    dynamics = EquationsField((Symbol.STATE, Symbol.DYNAMICS))
    controls = InequationsField((Symbol.CONTROL, Symbol.DYNAMICS))
    constraints = InequationsField((Symbol.STATE, Symbol.CONSTRAINT))
    domain = InequationsField()
    target = InequationsField((Symbol.STATE, Symbol.TARGET))

    STATEMENTS = [dynamics, constraints, controls, target]
    STATEMENTS_SET = set(STATEMENTS)

    def update_symbols(self):
        statements_items = [
            (f, getattr(self, f.name)) for f in self.STATEMENTS
            if getattr(self, f.name)]

        symbols = {}
        symbols_order = defaultdict(int)

        # Extract variables and parameters
        for field, statements in statements_items:
            for left, _, right in statements:
                # Variable and parameter types
                vtype, ptype = field.types

                # Add variable
                symbols[left] = (symbols_order[vtype], vtype)
                symbols_order[vtype] += 1

                # Add parameters
                for name in right:
                    if name not in symbols:
                        symbols[name] = (symbols_order[ptype], ptype)
                        symbols_order[ptype] += 1

        # Sort symbols by type
        symbols_by_type = defaultdict(list)
        sorted_symbols = sorted(symbols.items(), key=lambda x: x[1][0])
        for name, (order, typ) in sorted_symbols:
            symbols_by_type[typ].append(name)

        # Normalize symbols order
        symbols = {
            n: (o, t)
            for t in symbols_by_type
            for o, n in enumerate(symbols_by_type[t])
        }

        # Update database
        self.symbols.all().delete()
        Symbol.objects.bulk_create([
            Symbol(vp=self, type=typ, order=order, name=name)
            for name, (order, typ) in symbols.items()
        ])

    @staticmethod
    def post_save(sender, instance, changed_fields=None, **kwargs):
        fields = set(changed_fields.keys())
        if fields & instance.STATEMENTS_SET:
            instance.update_symbols()


class ParameterSet(Entity):
    vp = models.ForeignKey(ViabilityProblem, models.CASCADE,
                           verbose_name="Viability problem")
    dynamics = models.CharField(max_length=200, blank=True)
    constraints = models.CharField(max_length=200, blank=True)
    target = models.CharField(max_length=200, blank=True)

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


class Software(EntityWithMetadata):
    version = models.CharField(max_length=30, default='', blank=True)
    parameters = models.CharField(max_length=200, default='', blank=True)


class DataFormat(Entity):
    parameters = models.CharField(max_length=200, default='', blank=True)


class Kernel(EntityWithMetadata):
    params = models.ForeignKey(ParameterSet, models.CASCADE, verbose_name="Parameters")
    format = models.ForeignKey(DataFormat, models.CASCADE)
    software = models.ForeignKey(Software, models.CASCADE)
    datafile = models.FileField(upload_to='kernels/%Y/%m/%d', verbose_name="Data file")
