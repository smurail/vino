from __future__ import annotations

import numpy as np
import numpy.typing as npt
import numpy.lib.recfunctions as rfn

from typing import cast

from ..metadata import Metadata
from ..utils import to_int
from .regulargrid import RegularGrid, as_ppa_array, grid_positions
from .typing import NDArrayInt, NDArrayFloat
from .utils import RectanglesMixin, asrecords


def _bars_merge(bar_a: NDArrayInt, bar_b: NDArrayInt) -> tuple[int, int] | None:
    a0, a1 = bar_a[-2], bar_a[-1]+1
    b0, b1 = bar_b[-2], bar_b[-1]+1
    if a0 <= b0 <= a1 or a0 <= b1 <= a1 or b0 <= a0 <= b0 or b0 <= a1 <= b1:
        return (min(a0, b0), max(a1, b1)-1)
    return None


class BarGrid(RectanglesMixin, RegularGrid):
    """
    List of non-overlapping *bars* containing the set of viable points.

    Bars are :attr:`dim`-dimensional hyperrectangles defined by a start point
    and an end coordinate -- along the :attr:`baraxis`-axis of the state space.

    Property :attr:`baraxis` is the zero-based index of the bar axis. For
    example if :attr:`baraxis` is ``1`` (ie. *y*-axis), a bar defined by the
    array `[3, 0, 12]` starts at point :math:`\\coord{3, 0}` and ends at point
    :math:`\\coord{3, 12}`.
    """
    DATAFORMAT = 'bars'
    DTYPE = np.uint32

    axes: list[int]

    def __init__(self, data: npt.ArrayLike, metadata: Metadata) -> None:
        super().__init__(data, metadata)

        point_size = self.metadata.get('PointSize', 1)
        if point_size > 1:
            self[:] = self // point_size

        # Data array
        columns = [c for c in self.metadata['ColumnDescription'] if c != 'empty']
        self.axes = list(to_int(c)-1 for c in columns)
        assert self.axes[-2] == self.axes[-1]

        # New column names
        self.columns = [
            self.axis_name(c) + ('max' if i == len(self.axes)-1 else '')
            for i, c in enumerate(self.axes)
        ]

    @property
    def dim(self) -> int:
        assert self.size == 0 or len(self.shape) == 2
        return (cast(int, self.shape[1]) - 1) if self.size > 0 else 0

    @property
    def baraxis(self) -> int:
        return self.axes[-1]

    def indices_min(self) -> tuple[int, ...]:
        return tuple(self.axes.index(a) for a in range(self.dim))

    def indices_max(self) -> tuple[int, ...]:
        return tuple(a+1 if a == self.dim-1 else a for a in self.indices_min())

    def indices_pos(self) -> tuple[int, ...]:
        return tuple(self.axes.index(a) for a in range(self.dim) if a != self.baraxis)

    def points_min(self) -> NDArrayInt:
        return cast(NDArrayInt, self[:, self.indices_min()])

    def points_max(self) -> NDArrayInt:
        return cast(NDArrayInt, self[:, self.indices_max()])

    def points(self) -> npt.NDArray:
        return np.asarray(np.concatenate((  # type: ignore
            self.points_min(),
            self.points_max(),
        ), axis=0))

    def points_coordinates(self) -> NDArrayFloat:
        return cast(NDArrayFloat, self.origin + self.points() * self.unit)

    def rectangles(self) -> NDArrayFloat | None:
        if self.dim != 2:
            return None

        half_unit: NDArrayFloat = self.unit / 2
        real_bars = self.origin[self.axes] + self * self.unit[self.axes]

        # [[x0, y0], ...]
        rectangles_min = real_bars[:, self.indices_min()] - half_unit
        # [[x1, y1], ...]
        rectangles_max = real_bars[:, self.indices_max()] + half_unit

        # [[x0, y0, x1, y1], ...]
        return np.hstack((rectangles_min, rectangles_max))

    def permute(self, baraxis: int) -> BarGrid:
        return self.to_regulargrid().to_bargrid(baraxis=baraxis)

    def hull(self, regu: RegularGrid | None = None) -> NDArrayFloat:
        grid = regu if regu is not None else self.to_regulargrid()
        other_axes = [a for a in range(self.dim) if a != self.baraxis]
        other_hull = [grid.to_bargrid(baraxis=a) for a in other_axes]

        hull = [self]

        for bg in other_hull:
            hull.extend((
                bg[:, bg.indices_min()][:, self.axes],
                bg[:, bg.indices_max()][:, self.axes]
            ))

        return BarGrid(
            np.unique(np.concatenate(hull), axis=0),  # type: ignore
            self.metadata
        )

    def to_regulargrid(self, ppa: int | npt.ArrayLike = -1) -> RegularGrid:
        if ppa != -1:
            self = self.to_bargrid(ppa=ppa)

        bar_indices = list(self.indices_min())
        grid = np.full(self.ppa, False)

        for bar in self:
            # Build index
            bar_min, bar_max = bar[-2], bar[-1]+1
            index = bar[bar_indices].tolist()
            index[self.baraxis] = slice(bar_min, bar_max)
            # Fill grid
            grid[tuple(index)] = True

        new_metadata = Metadata(
            self.metadata,
            PointSize=1,
            PointNumberPerAxis=self.ppa - 1,
            MinimalValues=self.origin,
            MaximalValues=self.opposite,
        )

        return RegularGrid(grid, new_metadata)

    def to_bargrid(self, ppa: int | npt.ArrayLike = -1, baraxis: int = -1, autocrop: bool = True) -> BarGrid:
        assert baraxis == -1

        # New grid bounds
        if autocrop:
            # Crop bounds to actual values
            min_point = self[:, self.indices_min()].min(axis=0)
            max_point = self[:, self.indices_max()].max(axis=0)
            new_bounds = np.array((
                self.origin + (min_point - 0.5) * self.unit,
                self.origin + (max_point + 0.5) * self.unit
            ))
        else:
            # Keep bounds
            new_bounds = self.bounds

        # New bargrid metrics
        new_ppa = as_ppa_array(ppa, self.dim)
        new_unit = (new_bounds[1] - new_bounds[0]) / new_ppa
        new_origin = new_bounds[0] + new_unit / 2
        new_opposite = new_bounds[1] - new_unit / 2

        pos_axes = self.axes[:-2]

        # Build 2D array of every positions of the new grid
        new_positions = grid_positions(new_ppa[pos_axes])
        # Build 2D array of these positions expressed in old grid coordinates
        old_positions = (
            (new_origin[pos_axes] + new_positions * new_unit[pos_axes] - self.origin[pos_axes]) / self.unit[pos_axes]
        ).round().astype(self.dtype)

        # Compute new bars
        new_bars = self._resample(
            self, self.axes, self.columns,
            self.origin, self.unit, old_positions,
            new_origin, new_unit, new_positions
        )

        coldesc = [f'x{a+1}' for a in self.axes]
        coldesc[-2] += 'min'
        coldesc[-1] += 'max'

        new_metadata = Metadata(
            self.metadata,
            PointSize=1,
            PointNumberPerAxis=new_ppa - 1,
            MinimalValues=new_origin,
            MaximalValues=new_opposite,
            ColumnDescription=coldesc,
        )

        return BarGrid(new_bars, new_metadata)

    @staticmethod
    def _resample(  # type: ignore
        data: BarGrid,
        axes: list[int],
        cols: list[str],
        old_origin, old_unit, old_positions,
        new_origin, new_unit, new_positions
    ) -> NDArrayInt:

        assert np.issubdtype(data.dtype, np.integer)

        # Sort all bars in lexical order (first by column 0, then 1, 2, etc.)
        old_bars_rec = asrecords(data, cols)
        old_bars_rec.sort()
        old_bars = rfn.structured_to_unstructured(old_bars_rec, copy=False)

        # Convert all bars from old grid coordinates to new grid coordinates
        new_bars = (
            (old_origin[axes] + old_bars * old_unit[axes] - new_origin[axes]) / new_unit[axes]
        ).round().astype(old_bars.dtype)

        # Build structured array views of old bars and old grid positions
        # to be able to do a fast search in old bars with `searchsorted` method
        pos_cols = cols[:-2]
        pos_axes = range(len(pos_cols))
        old_bars_positions = asrecords(old_bars[:, pos_axes], pos_cols)
        old_positions_rec = asrecords(old_positions, pos_cols)

        # New bars list
        bars = []

        # Iterate over indices of the new grid expressed in old grid coordinates
        for old_pos_rec in old_positions_rec:
            idx = old_bars_positions.searchsorted(old_pos_rec)
            new_batch: list[NDArrayInt] = []

            # Iterate over bars at current position
            while idx < len(old_bars) and np.all(old_bars_positions[idx] == old_pos_rec):
                new_bar = new_bars[idx]
                idx += 1

                merge = None

                # Already have bars to add at current position?
                if new_batch:
                    # Skip duplicates
                    if np.all(new_bar == new_batch[-1]):
                        continue

                    # Try to merge the new bar with the last one
                    merge = _bars_merge(new_batch[-1], new_bar)
                    if merge is not None:
                        new_batch[-1][-2:] = merge

                # Otherwise, add the new bar
                if merge is None:
                    new_batch.append(new_bar)

            # Finalize by adding current batch to new bars list
            bars.extend(new_batch)

        if not bars:
            return np.empty((0, data.shape[1]), dtype=old_bars.dtype)

        return np.array(bars, dtype=old_bars.dtype)
