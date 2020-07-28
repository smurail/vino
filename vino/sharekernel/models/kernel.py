from __future__ import annotations

import numpy as np  # type: ignore

from pathlib import Path
from tempfile import mktemp
from typing import List, Optional, Iterable, Tuple, Dict
from sortedcontainers import SortedList  # type: ignore
from itertools import chain, product
from operator import itemgetter

from django.db import models
from django.db.models import QuerySet, Count, Q
from django.db.models.query import ModelIterable
from django.conf import settings
from django.utils.text import slugify
from django.utils.functional import cached_property

from vino.core.data import parse_datafile, iter_datafile, Metadata

from .entity import EntityWithMetadata, EntityManager
from .parameterset import ParameterSet
from .dataformat import DataFormat
from .software import Software
from .sourcefile import SourceFile
from .viabilityproblem import (ViabilityProblem, ViabilityProblemQuerySet,
                               ViabilityProblemManagerMixin)
from .symbol import Symbol

from ..utils import generate_media_path, store_one_file


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

    @property
    def axes(self) -> Iterable[int]:
        return range(self.dimension)

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

    def to_bargrid(self, ppa: int, debug: bool = False) -> Optional['BarGridKernel']:
        return None

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
    def ppa(self):
        if not hasattr(self, '_ppa'):
            point_size = self.metadata['PointSize']
            return np.array(self.metadata['PointNumberPerAxis']) / point_size
        return np.array([self._ppa] * self.dimension)

    @cached_property
    def grid_bounds(self):
        if hasattr(self, '_grid_bounds'):
            return self._grid_bounds
        grid_min = np.array(self.metadata.get('MinimalValues'))
        grid_max = np.array(self.metadata.get('MaximalValues'))
        return np.array([grid_min, grid_max])

    @property
    def origin(self):
        return self.grid_bounds[0]

    @property
    def opposite(self):
        return self.grid_bounds[1]

    @cached_property
    def unit(self):
        return (self.opposite - self.origin) / (self.ppa - 1)

    @property
    def bounds(self):
        half_unit = self.unit / 2
        return np.array([self.origin - half_unit, self.opposite + half_unit])

    @cached_property
    def baraxis(self):
        return (
            self._baraxis if hasattr(self, '_baraxis') else
            self.metadata.get('dataformat.baraxis', 0)
        )

    @property
    def pos_axes(self):
        return (a for a in self.axes if a != self.baraxis)

    @cached_property
    def pos_unit(self):
        return np.delete(self.unit, self.baraxis)

    @cached_property
    def axis_order(self):
        return list(chain(
            range(0, self.baraxis),
            range(self.baraxis+1, self.dimension),
            (self.baraxis, self.baraxis)
        ))

    @cached_property
    def bar_unit(self):
        return np.array([self.unit[a] for a in self.axis_order])

    @cached_property
    def bar_order(self) -> List[int]:
        return list(chain(
            range(0, self.baraxis),
            range(self.baraxis+2, self.dimension+1),
            (self.baraxis, self.baraxis+1)
        ))

    @cached_property
    def bars(self):
        return SortedList(
            [tuple(datum[a] for a in self.bar_order) for datum in self.data],
        )

    @property
    def rectangles(self):
        if self.dimension == 2:
            return list(self.get_bar_rect(i) for i in range(self.size))

    def data_for_axis(self, axis: int):
        assert 0 <= axis < self.dimension
        for i in range(self.size):
            yield self.get_bar_lower(i, axis)
            yield self.get_bar_upper(i, axis)

    def set_options(self,
                    ppa: int,
                    baraxis: int = 0,
                    bounds: Optional[Iterable[Iterable[float]]] = None,
                    origin: Optional[Iterable[float]] = None,
                    opposite: Optional[Iterable[float]] = None):

        assert ppa > 1
        assert 0 <= baraxis < self.dimension

        self._ppa = ppa
        self._baraxis = baraxis

        if bounds is not None:
            bounds = np.array(list(bounds))
            assert bounds.shape == (2, self.dimension)
            half_unit = (bounds[1] - bounds[0]) / (2 * ppa)
            origin, opposite = bounds[0] + half_unit, bounds[1] - half_unit
        else:
            assert origin is not None and opposite is not None
            origin = np.array(list(origin))
            opposite = np.array(list(opposite))
            assert origin.shape == opposite.shape == (self.dimension,)

        self._grid_bounds = np.array([origin, opposite])

    def get_bar_lower(self, i: int, axis: int) -> float:
        assert 0 <= i < len(self.bars)
        assert 0 <= axis < self.dimension
        return self.bars[i][
            -2 if axis == self.baraxis else
            axis if axis < self.baraxis else axis-1]

    def get_bar_upper(self, i: int, axis: int) -> float:
        assert 0 <= i < len(self.bars)
        assert 0 <= axis < self.dimension
        return self.bars[i][
            -1 if axis == self.baraxis else
            axis if axis < self.baraxis else axis-1]

    def get_bar_rect(self, i: int) -> Tuple[float, float, float, float]:
        assert self.dimension == 2

        # Get start point and end point
        start = np.array([self.get_bar_lower(i, 0), self.get_bar_lower(i, 1)])
        end = np.array([self.get_bar_upper(i, 0), self.get_bar_upper(i, 1)])

        # Compute half step of the grid for both dimensions
        half_unit = self.unit / 2

        # Compute coordinates for both opposite corners of each rect
        x0, y0 = start - half_unit
        x1, y1 = end + half_unit

        return (x0, x1, y0, y1)

    def add_bar(self, bar: List[float]):
        pos, lower, upper = bar[:-2], bar[-2], bar[-1]

        assert lower < upper

        unit = self.unit[self.baraxis]
        merge_bars = []

        bars_at_pos = self.bars.irange(
            (pos - self.pos_unit / 2).tolist(),
            (pos + self.pos_unit / 2).tolist()
        )
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

    def to_bargrid(self, ppa, debug=False):
        grid = BarGridKernel(
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

        grid.set_options(
            ppa=ppa,
            baraxis=self.baraxis,
            bounds=self.bounds,
        )

        grid_space = [
            np.linspace(grid.origin[a], grid.opposite[a], grid.ppa[a])
            for a in grid.pos_axes
        ]

        # Half step in the new grid
        pu_2 = grid.pos_unit / 2

        # Grid step for bar dimension in old grid and new grid
        old_bu = self.unit[self.baraxis]
        new_bu = grid.unit[grid.baraxis]

        # PPA, lower point and upper point for bar dimension
        b_ppa = grid.ppa[grid.baraxis]
        b_min = grid.bounds[0][grid.baraxis]
        b_max = grid.bounds[1][grid.baraxis]
        b_len = (b_max - b_min)

        # Iterate over grid
        for pos in product(*grid_space):
            # Look for bars at current position
            bars = list(self.bars.irange(tuple(pos - pu_2), tuple(pos + pu_2)))
            # Snap found bars to the grid and add them to the new BarGrid
            for bar in bars:
                bar_min = b_min + (np.floor(b_ppa * (bar[-2] - 0.5 * old_bu - b_min) / b_len) + 0.5) * new_bu
                bar_max = b_min + (np.floor(b_ppa * (bar[-1] + 0.5 * old_bu - b_min) / b_len) + 0.5) * new_bu

                if bar_min < bar_max:
                    grid.add_bar(list(pos) + [bar_min, bar_max])

        return grid


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

    def to_bargrid(self, ppa, debug=False):
        assert ppa > 1

        # Lower bounds of new bars for each dimension
        minima = np.array([
            min(self.get_cell_lower(i, a) for i in range(self.size))
            for a in self.axes
        ])
        # Upper bounds of new bars for each dimension
        maxima = np.array([
            max(self.get_cell_upper(i, a) for i in range(self.size))
            for a in self.axes
        ])
        # Bounds of the new bars points
        unit = (maxima - minima) / ppa
        origin = minima + unit / 2
        opposite = maxima - unit / 2
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
            origin=origin,
            opposite=opposite,
        )

        if debug:
            cells: Dict[Tuple[float, ...], int] = {}

        seen = set()

        ba, pu = bgk.baraxis, bgk.pos_unit

        # Iterate over cells
        for i in range(self.size):

            lower_point = np.fromiter((self.get_cell_lower(i, a) for a in self.axes), float)
            lower = origin + np.floor((lower_point - minima) / bgk.unit) * bgk.unit

            upper_point = np.fromiter((self.get_cell_upper(i, a) for a in self.axes), float)
            upper = origin + np.floor((upper_point - minima) / bgk.unit) * bgk.unit

            upper[ba] = np.minimum(upper[ba], opposite[ba])

            if lower[ba] >= upper[ba]:
                continue

            pos_lower = np.delete(lower, ba)
            pos_limit = np.delete(opposite, ba)
            pos_upper = np.minimum(np.delete(upper, ba), pos_limit) + pu
            pos_num = np.round((pos_upper - pos_lower) / pu).astype(int)

            if np.any(pos_lower > pos_upper):
                continue

            cell_spaces = [
                np.linspace(pos_lower[i], pos_upper[i], num=pos_num[i], endpoint=False)
                for i in range(len(pos_lower))
            ]

            for pos in product(*cell_spaces):
                bar = list(pos) + [lower[ba], upper[ba]]

                if debug:
                    c0, c1 = np.array(pos), pos + pu
                    c0 = np.insert(c0, ba, lower[ba])
                    c1 = np.insert(c1, ba, upper[ba])
                    new_cell = tuple(c0) + sum(((c0[a], c1[a]) for a in self.axes), ())
                    if new_cell not in cells:
                        cells[new_cell] = len(cells)

                bar_id = tuple(bar)
                if bar_id not in seen:
                    bgk.add_bar(bar)
                    seen.add(bar_id)

        if debug:
            sorted_cells = list(it[0] for it in sorted(cells.items(), key=itemgetter(bgk.baraxis)))
            for cell in sorted_cells:
                print(cell)
            print('Cell count:', len(cells))
            self.data = np.array(sorted_cells)

        print('Bar count:', len(bgk.bars))

        return bgk


_CUSTOM_KERNELS = {cls.FORMAT: cls for cls in Kernel.__subclasses__()}
