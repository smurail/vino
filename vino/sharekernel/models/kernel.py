from __future__ import annotations

from typing import Optional, IO, AnyStr

from django.db import models
from django.db.models import QuerySet, Count, Q
from django.db.models.query import ModelIterable
from django.utils.functional import cached_property
from django.contrib.auth.models import User

import vino as vn

from ..utils import media_relative_path
from .entity import EntityWithMetadata, EntityManager
from .parameterset import ParameterSet
from .dataformat import DataFormat
from .software import Software
from .sourcefile import SourceFile
from .viabilityproblem import (ViabilityProblem, ViabilityProblemQuerySet,
                               ViabilityProblemManagerMixin)
from .symbol import Symbol
from .datafile import make_datafile


class KernelIterable(ModelIterable):
    def __iter__(self):
        for kernel in super().__iter__():
            yield kernel.promote()


class KernelQuerySet(ViabilityProblemQuerySet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._iterable_class = KernelIterable

    def with_dimension_of(self, type, name):
        opts = {
            name: Count(
                'params__vp__symbols',
                filter=Q(params__vp__symbols__type=type)
            )
        }
        return self.annotate(**opts)


class KernelManager(ViabilityProblemManagerMixin, EntityManager):
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
    DATA_UNIT = '-'
    DATAFILE_PATH = 'kernels/%Y/%m/%d'

    FORMAT: Optional[str] = None

    objects = KernelManager()

    params = models.ForeignKey(ParameterSet, models.CASCADE,
                               related_name="kernels",
                               verbose_name="Parameters")
    format = models.ForeignKey(DataFormat, models.CASCADE, verbose_name="Data format")
    software = models.ForeignKey(Software, models.CASCADE)
    datafile = models.FileField(upload_to=DATAFILE_PATH, verbose_name="Data file")
    sourcefiles = models.ManyToManyField(SourceFile, verbose_name="Source files")
    size = models.IntegerField(default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure Kernel subclasses instances always have the right format
        if self.FORMAT and (not self.format_id or str(self.format) != self.FORMAT):
            self.format = DataFormat.objects.get(title=self.FORMAT)
            assert str(self.format) == self.FORMAT

    def promote(self) -> Kernel:
        # https://schinckel.net/2013/07/28/django-single-table-inheritance-on-the-cheap./
        format_name = str(self.format)
        if format_name in _CUSTOM_KERNELS:
            subclass = _CUSTOM_KERNELS[format_name]
            self.__class__ = subclass
        return self

    @property
    def vp(self) -> ViabilityProblem:
        return self.params.vp

    @cached_property
    def variables(self) -> QuerySet[Symbol]:
        return self.vp.state_variables

    @property
    def dimension(self) -> int:
        return len(self.variables)

    @cached_property
    def data(self) -> vn.Vino:
        return vn.load(self.datafile.path)

    @property
    def metadata(self) -> vn.Metadata:
        return self.data.metadata

    @property
    def size_with_unit(self) -> Optional[str]:
        if self.size:
            return f'{self.size} {self.DATA_UNIT}{"s" if self.size > 1 else ""}'
        return None

    def update_datafile(self) -> None:
        files = [sf.file for sf in self.sourcefiles.order_by('pk').all()]
        _, path = make_datafile(self.DATAFILE_PATH, files)
        self.datafile = media_relative_path(path)

    @classmethod
    def from_files(cls, *files: IO[AnyStr], owner: User | None = None) -> Kernel:
        sourcefiles = SourceFile.from_files(*files)
        files = [sf.file for sf in sourcefiles]
        data, path = make_datafile(cls.DATAFILE_PATH, files)
        metadata = data.metadata

        # Generate models instances from metadata
        vp = ViabilityProblem.from_metadata(metadata, owner=owner)
        fields = {
            'params': ParameterSet.from_metadata(metadata, vp=vp, owner=owner),
            'software': Software.from_metadata(metadata, owner=owner),
            'format': DataFormat.from_metadata(metadata, owner=owner),
            'datafile': media_relative_path(path),
            'size': data.count,
            'owner': owner,
        }
        kernel = Kernel.from_metadata(metadata, **fields)

        # Bind to source files
        kernel.sourcefiles.add(*sourcefiles)

        # FIXME Should check if declared format in metadata match detected one
        # FIXME Should check if column count is valid
        # FIXME Perform other checks?

        return kernel


class RegularGridKernel(Kernel):
    class Meta:
        proxy = True

    FORMAT = 'regulargrid'
    DATA_UNIT = 'point'

    objects = KernelManager.create('RegularGrid', FORMAT)()


class BarGridKernel(Kernel):
    class Meta:
        proxy = True

    FORMAT = 'bars'
    DATA_UNIT = 'bar'

    objects = KernelManager.create('BarGrid', FORMAT)()


class KdTreeKernel(Kernel):
    class Meta:
        proxy = True

    FORMAT = 'kdtree'
    DATA_UNIT = 'cell'

    objects = KernelManager.create('KdTree', FORMAT)()


class PolygonKernel(Kernel):
    class Meta:
        proxy = True

    FORMAT = 'polygon'
    DATA_UNIT = 'point'

    objects = KernelManager.create('Polygon', FORMAT)()


_CUSTOM_KERNELS = {cls.FORMAT: cls for cls in Kernel.__subclasses__()}
