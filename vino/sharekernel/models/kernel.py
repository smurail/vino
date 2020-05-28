from pathlib import Path
from tempfile import mktemp

from django.db import models
from django.db.models.query import ModelIterable
from django.conf import settings
from django.utils.text import slugify
from django.utils.functional import cached_property

from vino.core.data import parse_datafile, iter_datafile, Metadata

from .entity import EntityWithMetadata
from .parameterset import ParameterSet
from .dataformat import DataFormat
from .software import Software
from .sourcefile import SourceFile
from .viabilityproblem import ViabilityProblem

from ..utils import generate_media_path, store_one_file


class KernelIterable(ModelIterable):
    def __iter__(self):
        for kernel in super().__iter__():
            yield kernel.promote()


class KernelQuerySet(models.QuerySet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._iterable_class = KernelIterable


class KernelManager(models.Manager):
    FORMAT = None

    def get_queryset(self):
        # Use custom queryset
        qs = KernelQuerySet(self.model, using=self._db)
        # Optimization: fetch related objects in the same sql query
        qs = qs.select_related(
            'params', 'format', 'software', 'params__vp'
        )
        # Filter by format if needed
        if self.FORMAT is not None:
            qs = qs.filter(format__title=self.FORMAT)
        return qs

    @classmethod
    def create(cls, name, format_name):
        return type(
            f'{name}KernelManager',
            (KernelManager,),
            {'FORMAT': format_name}
        )


class Kernel(EntityWithMetadata):
    PREFIX = 'results.'
    IDENTITY = ('title', 'params', 'format', 'software', 'datafile')

    objects = KernelManager()

    params = models.ForeignKey(ParameterSet, models.CASCADE, verbose_name="Parameters")
    format = models.ForeignKey(DataFormat, models.CASCADE, verbose_name="Data format")
    software = models.ForeignKey(Software, models.CASCADE)
    datafile = models.FileField(upload_to='kernels/%Y/%m/%d', verbose_name="Data file")
    sourcefiles = models.ManyToManyField(SourceFile, verbose_name="Source files")
    size = models.IntegerField(default=0)

    def promote(self):
        # https://schinckel.net/2013/07/28/django-single-table-inheritance-on-the-cheap./
        format_name = self.format.title
        if format_name in _CUSTOM_KERNELS:
            subclass = _CUSTOM_KERNELS[format_name]
            self.__class__ = subclass
        return self

    @property
    def vp(self):
        return self.params.vp

    @cached_property
    def data(self):
        return [
            tuple(datum.data) for datum in iter_datafile(self.datafile.path)
        ]

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


class BarGridKernel(Kernel):
    FORMAT = 'bars'

    objects = KernelManager.create('BarGrid', 'bars')()

    class Meta:
        proxy = True


class KdTreeKernel(Kernel):
    FORMAT = 'kdtree'

    objects = KernelManager.create('KdTree', 'kdtree')()

    class Meta:
        proxy = True


_CUSTOM_KERNELS = {cls.FORMAT: cls for cls in Kernel.__subclasses__()}
