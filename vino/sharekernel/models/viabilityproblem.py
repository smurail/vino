from typing import Dict
from collections import defaultdict

from django.db import models
from django.db.models import Count, Q

from .fields import EquationsField, InequationsField
from .entity import EntityWithMetadata, EntityQuerySet
from .symbol import Symbol


class ViabilityProblemQuerySet(EntityQuerySet):
    def with_dimension_of(self, type, name):
        opts = {name: Count('symbols', filter=Q(symbols__type=type))}
        return self.annotate(**opts)

    def with_state_dimension(self):
        return self.with_dimension_of(Symbol.STATE, 'state_dimension')

    def with_control_dimension(self):
        return self.with_dimension_of(Symbol.CONTROL, 'control_dimension')

    def with_dimensions(self):
        return self.with_state_dimension().with_control_dimension()

    def of_dimension(self, value: int):
        return self.with_state_dimension().filter(state_dimension=value)


class ViabilityProblemManagerMixin:
    def with_dimension_of(self, type, name):
        return self.get_queryset().with_dimension_of(type, name)

    def with_state_dimension(self):
        return self.get_queryset().with_state_dimension()

    def with_control_dimension(self):
        return self.get_queryset().with_control_dimension()

    def with_dimensions(self):
        return self.get_queryset().with_dimensions()

    def of_dimension(self, value: int):
        return self.get_queryset().of_dimension(value)


class ViabilityProblem(EntityWithMetadata):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['dynamics', 'constraints', 'domain', 'controls', 'target'],
                name='viabilityproblem_unique'
            )
        ]

    PREFIX = 'viabilityproblem.'
    IDENTITY = ('dynamics', 'controls', 'constraints', 'domain', 'target')
    METADATA_TO_FIELD = {
        'dynamicsdescription': 'dynamics',
        'admissiblecontroldescription': 'controls',
        'stateconstraintdescription': 'constraints',
        'statedefinitiondomain': 'domain',
        'targetdescription': 'target',
    }

    _symbols_details: Dict[str, Symbol] = {}

    dynamics = EquationsField((Symbol.STATE, Symbol.DYNAMICS))
    controls = InequationsField((Symbol.CONTROL, Symbol.DYNAMICS))
    constraints = InequationsField((Symbol.STATE, Symbol.CONSTRAINT))
    domain = InequationsField()
    target = InequationsField((Symbol.STATE, Symbol.TARGET))

    objects = ViabilityProblemQuerySet.as_manager()

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

                # Add variables
                for name in left:
                    symbols[name] = (symbols_order[vtype], vtype)
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
        details = self._symbols_details or {s.name: s for s in self.symbols.all()}
        self.symbols.all().delete()
        Symbol.objects.bulk_create([
            Symbol(
                vp=self, type=typ, order=order, name=name,
                longname=details[name].longname if name in details else '',
                unit=details[name].unit if name in details else '')
            for name, (order, typ) in symbols.items()
        ])

    @staticmethod
    def post_save(sender, instance, changed_fields=None, **kwargs):
        fields = set(changed_fields.keys())
        if fields & instance.STATEMENTS_SET:
            instance.update_symbols()

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._symbols_details = None
        return instance

    @classmethod
    def from_metadata(cls, metadata, **kwargs):
        # Generate model instance from metadata
        instance = super().from_metadata(metadata, **kwargs)
        if instance._created:
            # Make sure to_python method is called for each field so we get
            # Statements objects for dynamics, constraints, controls, etc...
            instance.full_clean()
            # Build a variable dict from metadata
            var_fields = ('statevariables', 'controlvariables')
            var_definitions = sum(
                [(metadata.get(f'{cls.PREFIX}{v}') or []) for v in var_fields],
                []
            )
            variables = {
                v[0]: Symbol(name=v[0], longname=v[1], unit=v[2])
                for v in var_definitions
            }
            # Apply symbols informations from aforementioned dict
            instance._symbols_details = variables
            instance.update_symbols()
        return instance

    @property
    def dynamics_type(self):
        return self.dynamics.dynamics_type_name.capitalize()

    @property
    def state_variables(self):
        return self.symbols.filter(type=Symbol.STATE)

    @property
    def control_variables(self):
        return self.symbols.filter(type=Symbol.CONTROL)

    @property
    def dynamics_parameters(self):
        return self.symbols.filter(type=Symbol.DYNAMICS)

    @property
    def constraint_parameters(self):
        return self.symbols.filter(type=Symbol.CONSTRAINT)

    @property
    def kernels(self):
        from .kernel import Kernel
        return Kernel.objects.filter(params__vp=self)
