from collections import OrderedDict, defaultdict
from itertools import chain
from pathlib import Path
from tempfile import mktemp
from typing import Tuple, Dict

from django.db import models
from django.db.models import Count, Q
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.utils.text import slugify

from django_currentuser.db.models import CurrentUserField

from vino.core.data import parse_datafile, iter_datafile, Metadata

from .fields import EquationsField, InequationsField
from .utils import (generate_media_path, store_files, store_one_file,
                    sorted_by_size)


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

    @classmethod
    def field_exists(cls, field):
        try:
            cls._meta.get_field(field)
            return True
        except FieldDoesNotExist:
            return False

    @classmethod
    def prepare_metadata(cls, metadata, **kwargs):
        def field_name(mk):
            k = mk[len(cls.PREFIX):] if '.' in mk else mk
            return cls.METADATA_TO_FIELD.get(k, k)

        metadata = {
            k: metadata.FIELDS[k].unparse(v) for k, v in metadata.items()
        }

        filtered_metadata = {
            k: v for k, v in dict(metadata, **kwargs).items()
            if '.' not in k or k.startswith(cls.PREFIX)
        }

        return {
            field_name(k): v for k, v in filtered_metadata.items()
            if v is not None and cls.field_exists(field_name(k))
        }

    @classmethod
    def from_metadata(cls, metadata, **kwargs):
        values = cls.prepare_metadata(metadata, **kwargs)
        kwargs = {k: values.get(k) for k in cls.IDENTITY if values.get(k)}
        obj, created = cls.objects.get_or_create(defaults=values, **kwargs)
        obj._created = created
        return obj

    @classmethod
    def from_files(cls, *files, owner=None):
        metadata = Metadata()
        for filepath in files:
            parse_datafile(filepath, metadata=metadata)
        return cls.from_metadata(metadata)


class EntityWithMetadata(Entity):
    class Meta:
        abstract = True

    PREFIX = 'entity.'
    IDENTITY: Tuple[str, ...] = ('title',)
    METADATA_TO_FIELD = {
        'contact': 'email',
        'website': 'url',
    }

    title = models.CharField(max_length=200)
    description = models.TextField(default='', blank=True)
    publication = models.TextField(default='', blank=True)
    author = models.CharField(max_length=200, default='', blank=True)
    email = models.CharField(max_length=200, default='', blank=True)
    url = models.URLField(default='', blank=True)
    image = models.ImageField(upload_to='images/%Y/%m/%d', blank=True)

    def __str__(self):
        return self.title


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

    @property
    def fullname(self):
        return self.name + (f' ({self.longname})' if self.longname else '')

    def __str__(self):
        return f'{self.TYPES[self.type]}: {self.fullname}'


class ViabilityProblemQuerySet(models.QuerySet):
    def with_dimension_of(self, type, name):
        opts = {name: Count('symbols', filter=Q(symbols__type=type))}
        return self.annotate(**opts)

    def with_state_dimension(self):
        return self.with_dimension_of(Symbol.STATE, 'state_dimension')

    def with_control_dimension(self):
        return self.with_dimension_of(Symbol.CONTROL, 'control_dimension')

    def with_dimensions(self):
        return self.with_state_dimension().with_control_dimension()


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
        details = self._symbols_details
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
        instance._symbols_details = {s.name: s for s in instance.symbols.all()}
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


class ParameterSet(Entity):
    PREFIX = 'parameters.'
    IDENTITY = ('vp', 'dynamics', 'constraints', 'target')
    METADATA_TO_FIELD = {
        'dynamicsparametervalues': 'dynamics',
        'stateconstraintparametervalues': 'constraints',
        'targetparametervalues': 'target',
    }

    vp = models.ForeignKey(ViabilityProblem, models.CASCADE, verbose_name="Viability problem")
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
    PREFIX = 'software.'
    IDENTITY = ('title', 'version')

    version = models.CharField(max_length=30, default='', blank=True)
    parameters = models.CharField(max_length=200, default='', blank=True)


class DataFormat(EntityWithMetadata):
    PREFIX = 'resultformat.'
    IDENTITY = ('title',)
    METADATA_TO_FIELD = {
        'parameterlist': 'parameters'
    }

    parameters = models.CharField(max_length=200, default='', blank=True)


class SourceFile(Entity):
    file = models.FilePathField(path='import/%Y/%m/%d', verbose_name="Source file")

    @classmethod
    def from_files(cls, *files):
        path = generate_media_path(cls._meta.get_field('file').path)
        saved_files = store_files(path, *files)
        return [
            cls.objects.get_or_create(file=f)[0]
            for f in sorted_by_size(saved_files)
        ]

    def __str__(self):
        return Path(self.file).relative_to(settings.MEDIA_ROOT).as_posix()


class Kernel(EntityWithMetadata):
    PREFIX = 'results.'
    IDENTITY = ('title', 'params', 'format', 'software', 'datafile')

    params = models.ForeignKey(ParameterSet, models.CASCADE, verbose_name="Parameters")
    format = models.ForeignKey(DataFormat, models.CASCADE, verbose_name="Data format")
    software = models.ForeignKey(Software, models.CASCADE)
    datafile = models.FileField(upload_to='kernels/%Y/%m/%d', verbose_name="Data file")
    sourcefiles = models.ManyToManyField(SourceFile, verbose_name="Source files")
    size = models.IntegerField(default=0)

    @property
    def vp(self):
        return self.params.vp

    @property
    def data(self):
        for datum in iter_datafile(self.datafile.path):
            yield list(datum.data)

    @property
    def columns(self):
        metadata = Metadata()
        parse_datafile(self.datafile.path, metadata=metadata)
        return metadata.get('dataformat.columns')

    @classmethod
    def from_files(cls, *files, owner=None):
        # Parse data and metadata from files
        sourcefiles = SourceFile.from_files(*files)
        tmpfile = Path(mktemp(dir=settings.MEDIA_ROOT, prefix='vino-'))
        metadata = Metadata()
        size = 0

        try:
            for sf in sourcefiles:
                size += parse_datafile(sf.file, target=tmpfile, metadata=metadata)
        except Exception:
            tmpfile.unlink()
            raise

        # Generate datafile name from metadata
        fields = ('viabilityproblem.title', 'results.title')
        parts = (slugify(metadata.get(x)) for x in fields)
        filename = '_'.join(parts) + '.csv'
        datafile = generate_media_path(cls.datafile.field.upload_to) / filename

        # Store datafile and remove temporary file
        datafile = store_one_file(datafile, tmpfile.open())
        tmpfile.unlink()

        # Generate models instances from metadata
        vp = ViabilityProblem.from_metadata(metadata, owner=owner)
        fields = {
            'params': ParameterSet.from_metadata(metadata, vp=vp, owner=owner),
            'software': Software.from_metadata(metadata, owner=owner),
            'format': DataFormat.from_metadata(metadata, owner=owner),
            'datafile': datafile.relative_to(settings.MEDIA_ROOT).as_posix(),
            'size': size,
            'owner': owner,
        }
        kernel = Kernel.from_metadata(metadata, **fields)

        # Bind to source files
        kernel.sourcefiles.add(*sourcefiles)

        # Check if declared format match detected one
        detected = metadata.get('dataformat.name')
        declared = metadata.get('resultformat.title')
        msg = f'Declared format ({declared}) differs from detected one ({detected})'
        assert detected == declared, msg

        # Check if column count is valid
        column_count = len(metadata.get('dataformat.columns', []))
        dimensions = metadata.get('viabilityproblem.statedimension', 0)
        msg = f'Column count ({column_count}) must be greater or equal than state dimensions ({dimensions})'
        assert column_count >= dimensions, msg

        return kernel
