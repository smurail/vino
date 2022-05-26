from __future__ import annotations

import numpy as np
import numpy.typing as npt

from typing import cast, TYPE_CHECKING

from ..metadata import Metadata
from .vino import Vino
from .typing import NDArrayInt, NDArrayFloat

if TYPE_CHECKING:
    from .bargrid import BarGrid


def grid_positions(axes: npt.ArrayLike) -> NDArrayInt:
    a: NDArrayInt = np.asarray(axes)
    return np.indices(a).T.reshape(-1, len(a)).astype(a.dtype)  # type: ignore


def as_ppa_array(ppa: int | npt.ArrayLike, dim: int) -> NDArrayInt:
    ppa_array = np.array([ppa] * dim) if isinstance(ppa, int) else np.asarray(ppa)

    assert dim == len(ppa_array), "Dimension mismatch"
    assert np.all(ppa_array > 1), "PPA must be greater than one"

    return ppa_array


class RegularGrid(Vino):
    DATAFORMAT = 'regulargrid'

    ppa: NDArrayInt
    origin: NDArrayFloat
    opposite: NDArrayFloat

    def __init__(self, data: npt.ArrayLike, metadata: Metadata) -> None:
        # Grid
        point_size = self.metadata.get('PointSize', 1)
        # XXX Misleading name! PointNumberPerAxis = intervals = PPA - 1
        raw_ppa = np.array(self.metadata['PointNumberPerAxis'])

        assert point_size == 1 or point_size % 2 == 0
        assert np.all(raw_ppa % point_size == 0)

        self.ppa = (raw_ppa // point_size) + 1
        self.origin = np.array(self.metadata['MinimalValues'])
        self.opposite = np.array(self.metadata['MaximalValues'])

        assert len(self.ppa) == len(self.origin) == len(self.opposite)

    @property
    def dim(self) -> int:
        return self.ndim

    @property
    def bounds(self) -> NDArrayFloat:
        half_unit: NDArrayFloat = self.unit / 2
        return np.array((self.origin - half_unit, self.opposite + half_unit))

    @property
    def unit(self) -> NDArrayFloat:
        return cast(NDArrayFloat, (self.opposite - self.origin)) / (self.ppa - 1)

    def points_coordinates(self) -> NDArrayFloat:
        slices = tuple(
            slice(start, stop, complex(imag=steps))
            for start, stop, steps in zip(self.origin, self.opposite, self.ppa)
        )
        coordinates = np.mgrid[slices].reshape(self.dim, -1).T
        points = coordinates[self.ravel()]

        return cast(NDArrayFloat, points)

    def to_bargrid(self, ppa: int | npt.ArrayLike = -1, baraxis: int = -1) -> BarGrid:
        from .bargrid import BarGrid

        assert ppa == -1

        baraxis = 0 if baraxis < 0 else baraxis

        # New columns positions for bargrid conversion
        new_axes = [a for a in range(self.dim) if a != baraxis] + [baraxis, baraxis]
        new_pos_axes = new_axes[:-2]

        # Put bar-axis in last position to facilitate bargrid conversion
        permuted_grid = np.moveaxis(self, baraxis, self.dim-1) if baraxis != self.dim-1 else self

        bars: list[tuple[int, ...]] = []

        for pos in grid_positions(self.ppa[new_pos_axes]):
            pos_tuple = tuple(pos)
            row = permuted_grid[pos_tuple]

            # About 1.5 faster to preallocate bars_loc with np.empty than to
            # build it with np.concatenate
            bar_at_end = row[-1]
            bars_loc_len = len(row) + (1 if bar_at_end else 0)
            bars_loc = np.empty(bars_loc_len, dtype=bool)
            bars_loc[0] = row[0]
            np.not_equal(row[:-1], row[1:], out=bars_loc[1:len(row)])
            if bar_at_end:
                bars_loc[-1] = len(row)

            bars_pos = np.nonzero(bars_loc)[0]
            bars_len = np.diff(bars_pos.reshape(-1, 2), axis=1).ravel()  # type: ignore
            bars.extend(
                (pos_tuple + (b0, b0+bs-1))
                for b0, bs in zip(bars_pos[::2], bars_len)
            )

        columns = [f'x{a+1}' for a in new_axes]
        columns[-2] += 'min'
        columns[-1] += 'max'

        new_metadata = Metadata(
            self.metadata,
            PointSize=1,
            PointNumberPerAxis=self.ppa - 1,
            MinimalValues=self.origin,
            MaximalValues=self.opposite,
            ColumnDescription=columns,
        )

        return BarGrid(np.array(bars, dtype=BarGrid.DTYPE), new_metadata)
