from collections import OrderedDict, defaultdict

from django.db import models
from django.conf import settings

from .fields import StatementsField, EquationsField, InequationsField


class Entity(models.Model):
    class Meta:
        abstract = True

    ACTIVE = 1
    DELETED = 2
    STATES = (
        (ACTIVE, 'Active'),
        (DELETED, 'Deleted'),
    )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
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
                fields=['vp', 'type', 'name'],
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


class ViabilityProblem(Entity, Metadata):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['dynamics', 'constraints', 'domain', 'controls', 'target'],
                name='viabilityproblem_unique'
            )
        ]

    DISCRETE = 1
    CONTINUOUS = 2

    dynamics = EquationsField((Symbol.STATE, Symbol.DYNAMICS))
    constraints = InequationsField((Symbol.STATE, Symbol.CONSTRAINT))
    domain = InequationsField()
    controls = InequationsField((Symbol.CONTROL, Symbol.DYNAMICS))
    target = StatementsField()

    STATEMENTS = [dynamics, constraints, controls]
    STATEMENTS_SET = set(STATEMENTS)

    def update_symbols(self):
        def dynamics_variable(s):
            s = s.strip()
            if s.endswith("'"):
                return s[:-1], self.CONTINUOUS
            if s.startswith('next_'):
                return s[5:], self.DISCRETE
            raise Exception("Invalid dynamics left side: %s" % s)

        statements_items = [
            (f, getattr(self, f.name)) for f in self.STATEMENTS
            if getattr(self, f.name)]

        dynamics_type = None
        symbols = {}
        symbols_order = defaultdict(int)

        # Extract variables and parameters
        for field, statements in statements_items:
            for left, op, right in statements:
                # Left side of relation: variable
                if field.name == 'dynamics':
                    left_name, new_dynamics_type = dynamics_variable(left)
                    if dynamics_type is None:
                        dynamics_type = new_dynamics_type
                    elif dynamics_type != new_dynamics_type:
                        raise Exception("Can't mix different dynamics types")
                else:
                    left_name = left

                # Variable and parameter types
                vtype, ptype = field.types

                # Add variable
                if left_name not in symbols:
                    symbols[left_name] = (symbols_order[vtype], vtype)
                    symbols_order[vtype] += 1
                else:
                    symbols[left_name] = (symbols[left_name][0], vtype)

                # Add parameters
                for name in right:
                    if name not in symbols:
                        symbols[name] = (symbols_order[ptype], ptype)
                        symbols_order[ptype] += 1

        # Update database
        self.symbol_set.all().delete()
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


class Software(EntityWithMetadata):
    version = models.CharField(max_length=30, default='', blank=True)
    parameters = models.CharField(max_length=200, default='', blank=True)


class DataFormat(Entity):
    parameters = models.CharField(max_length=200, default='', blank=True)


class Kernel(EntityWithMetadata):
    FORMATS = (
        ('bars', 'BarGrid format'),
        ('kdtree', 'KdTree format'),
    )

    params = models.ForeignKey(ParameterSet, models.CASCADE)
    format = models.ForeignKey(DataFormat, models.CASCADE)
    software = models.ForeignKey(Software, models.CASCADE)
    file = models.FileField(upload_to='kernels/%Y/%m/%d')
