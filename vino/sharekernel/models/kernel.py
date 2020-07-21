from __future__ import annotations

import numpy as np  # type: ignore

from pathlib import Path
from tempfile import mktemp
from typing import List, Optional, Iterable, Tuple, Dict
from sortedcontainers import SortedList  # type: ignore
from itertools import chain
from operator import itemgetter

from django.db import models
from django.db.models import QuerySet
from django.db.models.query import ModelIterable
from django.conf import settings
from django.utils.text import slugify
from django.utils.functional import cached_property

from vino.core.data import parse_datafile, iter_datafile, Metadata

from .entity import EntityWithMetadata, EntityQuerySet, EntityManager
from .parameterset import ParameterSet
from .dataformat import DataFormat
from .software import Software
from .sourcefile import SourceFile
from .viabilityproblem import ViabilityProblem
from .symbol import Symbol

from ..utils import generate_media_path, store_one_file


class KernelIterable(ModelIterable):
    def __iter__(self):
        for kernel in super().__iter__():
            yield kernel.promote()


class KernelQuerySet(EntityQuerySet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._iterable_class = KernelIterable


class KernelManager(EntityManager):
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

    FORMAT: Optional[str] = None

    objects = KernelManager()

    params = models.ForeignKey(ParameterSet, models.CASCADE,
                               related_name="kernels",
                               verbose_name="Parameters")
    format = models.ForeignKey(DataFormat, models.CASCADE, verbose_name="Data format")
    software = models.ForeignKey(Software, models.CASCADE)
    datafile = models.FileField(upload_to='kernels/%Y/%m/%d', verbose_name="Data file")
    sourcefiles = models.ManyToManyField(SourceFile, verbose_name="Source files")
    size = models.IntegerField(default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure Kernel subclasses instances always have the right format
        if self.FORMAT and (not self.format_id or self.format.title != self.FORMAT):
            self.format = DataFormat.objects.get(title=self.FORMAT)
            assert self.format.title == self.FORMAT

    def promote(self) -> Kernel:
        # https://schinckel.net/2013/07/28/django-single-table-inheritance-on-the-cheap./
        format_name = self.format.title
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

    @property
    def rectangles(self) -> Optional[List[float]]:
        return None

    @cached_property
    def data(self):
        return np.array(
            [tuple(datum.data) for datum in iter_datafile(self.datafile.path)]
            if self.datafile else []
        )

    @cached_property
    def metadata(self) -> Metadata:
        metadata = Metadata()
        if self.datafile:
            parse_datafile(self.datafile.path, metadata=metadata)
        return metadata

    @property
    def size_with_unit(self) -> Optional[str]:
        if self.size:
            return f'{self.size} {self.DATA_UNIT}{"s" if self.size > 1 else ""}'
        return None

    @property
    def columns(self) -> Optional[List[str]]:
        return self.metadata.get('dataformat.columns')

    def data_for_axis(self, axis: int) -> Iterable[float]:
        assert 0 <= axis < self.dimension
        return self.data[:, axis].tolist()

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
    class Meta:
        proxy = True

    FORMAT = 'bars'
    DATA_UNIT = 'bar'

    objects = KernelManager.create('BarGrid', FORMAT)()

    @cached_property
    def baraxis(self):
        return (
            self._baraxis if hasattr(self, '_baraxis') else
            self.metadata.get('dataformat.baraxis', 0)
        )

    @cached_property
    def ppa(self):
        if not hasattr(self, '_ppa'):
            point_size = self.metadata['PointSize']
            return np.array(self.metadata['PointNumberPerAxis']) / point_size
        return np.array([self._ppa] * self.dimension)

    @cached_property
    def bounds(self):
        if hasattr(self, '_bounds'):
            return self._bounds
        defv = [.0 for _ in range(self.dimension)]
        minv = self.metadata.get('MinimalValues', defv)
        maxv = self.metadata.get('MaximalValues', defv)
        return tuple(
            (np.array((minv[i], maxv[i])) for i in range(self.dimension))
        )

    @cached_property
    def axis_order(self) -> List[int]:
        return list(chain(
            range(0, self.baraxis),
            range(self.baraxis+2, self.dimension+1),
            (self.baraxis, self.baraxis+1)
        ))

    @cached_property
    def bars(self):
        return SortedList(
            [tuple(datum[a] for a in self.axis_order) for datum in self.data],
        )

    @property
    def rectangles(self):
        if self.dimension == 2:
            return list(self.get_bar_rect(i) for i in range(self.size))

    def data_for_axis(self, axis: int):
        assert 0 <= axis < self.dimension
        half_unit = self.get_axis_unit(axis) / 2
        for i in range(self.size):
            yield self.get_bar_lower(i, axis) + half_unit
            yield self.get_bar_upper(i, axis) - half_unit

    def set_options(self, ppa: Optional[int] = None, baraxis: int = 0, bounds=None):
        assert ppa is None or ppa > 1
        assert 0 <= baraxis < self.dimension
        self._ppa = ppa
        self._baraxis = baraxis
        self._bounds = bounds

    def get_axis_length(self, axis: int) -> int:
        assert 0 <= axis < self.dimension
        lower, upper = self.bounds[axis]
        return upper - lower

    def get_axis_unit(self, axis: int, ppa: int = None):
        assert 0 <= axis < self.dimension
        return self.get_axis_length(axis) / self.ppa[axis]

    def get_bar_lower(self, i: int, axis: int) -> float:
        assert 0 <= i < len(self.bars)
        assert 0 <= axis < self.dimension
        return self.bars[i][
            -2 if axis == self.baraxis else
            axis if axis < self.baraxis else axis-1]

    def get_bar_upper(self, i: int, axis: int) -> float:
        assert 0 <= i < len(self.bars)
        assert 0 <= axis < self.dimension
        offset = 0 if axis == self.baraxis else self.get_axis_unit(axis)
        return offset + self.bars[i][
            -1 if axis == self.baraxis else
            axis if axis < self.baraxis else axis-1]

    def get_bar_rect(self, i: int) -> Tuple[float, float, float, float]:
        assert self.dimension == 2
        x0, y0 = self.get_bar_lower(i, 0), self.get_bar_lower(i, 1)
        x1, y1 = self.get_bar_upper(i, 0), self.get_bar_upper(i, 1)
        return (x0, x1, y0, y1)

    def add_bar(self, bar: List[float]):
        pos, lower, upper = bar[:-2], bar[-2], bar[-1]

        assert lower < upper

        axes = range(self.dimension)
        unit = self.get_axis_unit(self.baraxis)
        pos_unit = np.fromiter((self.get_axis_unit(a) for a in axes if a != self.baraxis), float)
        merge_bars = []

        bars_at_pos = self.bars.irange((pos - pos_unit / 2).tolist(), (pos + pos_unit / 2).tolist())
        for cur_bar in bars_at_pos:
            cur_lower, cur_upper = cur_bar[-2], cur_bar[-1]

            if round(upper/unit) >= round(cur_lower/unit) and round(lower/unit) <= round(cur_upper/unit):
                # our new bar intersects this bar, merge them
                merge_bars.append(cur_bar)
                lower = min(lower, cur_lower)
                upper = max(upper, cur_upper)

        for bar in merge_bars:
            self.bars.remove(bar)

        # Insert the new bar
        new_bar = pos + [lower, upper]
        self.bars.add(new_bar)
        self.size = len(self.bars)


class KdTreeKernel(Kernel):
    class Meta:
        proxy = True

    FORMAT = 'kdtree'
    DATA_UNIT = 'cell'

    objects = KernelManager.create('KdTree', FORMAT)()

    @property
    def rectangles(self):
        if self.dimension == 2:
            return [list(cell[2:6]) for cell in self.data]

    def get_cell_lower(self, i: int, axis: int) -> float:
        assert 0 <= i < self.size
        assert 0 <= axis < self.dimension
        return self.data[i][self.dimension + axis*2]

    def get_cell_upper(self, i: int, axis: int) -> float:
        assert 0 <= i < self.size
        assert 0 <= axis < self.dimension
        return self.data[i][self.dimension + axis*2 + 1]

    def to_bargrid(self, ppa: int, debug: bool = False) -> BarGridKernel:
        assert ppa > 1

        # Alias for state space dimension
        dim = self.dimension
        axes = range(dim)
        # Lower bounds for each axis
        minima = np.array([
            min(self.get_cell_lower(i, a) for i in range(self.size))
            for a in axes
        ])
        # Upper bounds for each axis
        maxima = np.array([
            max(self.get_cell_upper(i, a) for i in range(self.size))
            for a in axes
        ])
        # Size
        length = maxima - minima
        # Brand new BarGridKernel
        bgk = BarGridKernel(
            owner=self.owner,
            title=self.title,
            description=self.description,
            publication=self.publication,
            author=self.author,
            email=self.email,
            url=self.url,
            image=self.image,
            params=self.params
        )
        bgk.set_options(
            ppa=ppa,
            baraxis=0,
            bounds=tuple(np.array((minima[a], maxima[a])) for a in axes),
        )
        # Grid unit vector
        unit = length / bgk.ppa

        if debug:
            cells: Dict[Tuple[float, ...], int] = {}

        seen = set()

        for i in range(self.size):

            lower_point = np.fromiter((self.get_cell_lower(i, a) for a in axes), float)
            lower = minima + np.floor((lower_point - minima) / unit) * unit

            upper_point = np.fromiter((self.get_cell_upper(i, a) for a in axes), float)
            upper = minima + np.ceil((upper_point - minima) / unit) * unit

            assert lower[bgk.baraxis] < upper[bgk.baraxis]

            if debug:
                new_cell = tuple(lower) + sum(((lower[a], upper[a]) for a in axes), ())
                if new_cell not in cells:
                    cells[new_cell] = len(cells)

            pos = np.delete(lower, bgk.baraxis)
            pos_start = np.copy(pos)
            pos_limit = np.delete(upper, bgk.baraxis)
            pos_unit = np.delete(unit, bgk.baraxis)

            while np.all(np.round(pos/pos_unit) < np.round(pos_limit/pos_unit)):
                bar = pos.tolist() + [lower[bgk.baraxis], upper[bgk.baraxis]]

                bar_id = tuple(bar)
                if bar_id not in seen:
                    bgk.add_bar(bar)
                    seen.add(bar_id)

                for k in range(len(pos)):
                    if round(pos[k]/pos_unit[k]) < round(pos_limit[k]/pos_unit[k]):
                        pos[k] += pos_unit[k]
                        break
                    else:
                        pos[k] = pos_start[k]

        if debug:
            sorted_cells = list(it[0] for it in sorted(cells.items(), key=itemgetter(1)))
            for cell in sorted_cells:
                print(cell)
            print('Cell count:', len(cells))
            self.data = np.array(sorted_cells)

        print('Bar count:', len(bgk.bars))

        return bgk


_CUSTOM_KERNELS = {cls.FORMAT: cls for cls in Kernel.__subclasses__()}
