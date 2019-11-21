from collections import OrderedDict, defaultdict

from django.db import models
from django.conf import settings


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

    STATEMENTS = OrderedDict([
        ('dynamics', (Symbol.STATE, Symbol.DYNAMICS)),
        ('constraints', (Symbol.STATE, Symbol.CONSTRAINT)),
        ('controls', (Symbol.CONTROL, Symbol.DYNAMICS)),
    ])
    STATEMENTS_SET = set(STATEMENTS.keys())

    dynamics = models.CharField(max_length=200, blank=True)
    constraints = models.CharField(max_length=200, blank=True)
    domain = models.CharField(max_length=200, blank=True)
    controls = models.CharField(max_length=200, blank=True)
    target = models.CharField(max_length=200, blank=True)

    def update_symbols(self):
        import re
        from Equation import Expression

        def dynamics_variable(s):
            s = s.strip()
            if s.endswith("'"):
                return s[:-1], self.CONTINUOUS
            if s.startswith('next_'):
                return s[5:], self.DISCRETE
            raise Exception("Invalid dynamics left side: %s" % s)

        # Parse statements
        sep = ','
        relation = re.compile(r'(<=|>=|=)')
        all_statements = (
            (
                field,
                [relation.split(s) for s in getattr(self, field).split(sep)]
            )
            for field in self.STATEMENTS.keys()
        )
        dynamics_type = None
        symbols = {}
        symbols_order = defaultdict(int)

        # Extract variables and parameters
        for field, statements in all_statements:
            for left, op, right in statements:
                # Left side of relation: variable
                if field == 'dynamics':
                    left_name, new_dynamics_type = dynamics_variable(left)
                    if dynamics_type is None:
                        dynamics_type = new_dynamics_type
                    elif dynamics_type != new_dynamics_type:
                        raise Exception("Can't mix different dynamics types")
                else:
                    left_name = left

                # Right side of relation: parameters
                expr = Expression(right)

                # Add variable
                vtype = self.STATEMENTS[field][0]
                if left_name not in symbols:
                    symbols[left_name] = (symbols_order[vtype], vtype)
                    symbols_order[vtype] += 1
                else:
                    symbols[left_name] = (symbols[left_name][0], vtype)

                # Add parameters
                for name in expr:
                    ptype = self.STATEMENTS[field][1]
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
        fields = set((f.name for f in changed_fields.keys()))
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
