from __future__ import annotations

import numpy as np
import numpy.typing as npt

from typing import cast, TYPE_CHECKING, Sequence
from scipy import ndimage  # type: ignore

from ..metadata import Metadata
from .vino import Vino
from .typing import NDArrayInt, NDArrayFloat, NDArrayBool

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
    """
    A :attr:`dim`-dimensional array where non-zero elements define the set
    of the regular grid cells containing the viable points.

    Regular grid refers here to the tessellation of :attr:`dim`-dimensional
    euclidean space by congruent rectangular cuboids.
    """
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

        assert len(self.ppa) == len(self.origin)
        assert len(self.ppa) == len(self.opposite)

        # If `data` array is a flattened array, we need to give it back its
        # original shape -- for example when loading from a CSV file.
        # See also `save_csv` implementation in `vino.io` module.
        if type(self) is RegularGrid and self.dim == 2 and self.shape[-1] == 1:
            self.shape = self.ppa

        assert len(self.ppa) == self.dim

    @property
    def count(self) -> int:
        return self.size

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

    def grid_coordinates(self, axes: Sequence[int] | None = None) -> NDArrayFloat:
        if axes is None:
            origin, opposite, ppa = self.origin, self.opposite, self.ppa
        else:
            axes = list(axes)
            origin = self.origin[axes]
            opposite = self.opposite[axes]
            ppa = self.ppa[axes]

        slices = tuple(
            slice(start, stop, complex(imag=steps))
            for start, stop, steps in zip(origin, opposite, ppa)
        )
        dim = self.dim if axes is None else len(axes)

        return np.mgrid[slices].reshape(dim, -1).T

    def points_coordinates(self) -> NDArrayFloat:
        coordinates = self.grid_coordinates()
        points = coordinates[self.ravel()]

        return cast(NDArrayFloat, points)

    def section(self, plane: Sequence[int], at: Sequence[int]) -> NDArrayBool:
        assert len(plane) == 2
        assert len(at) == self.dim - 2

        sections = np.moveaxis(self, plane, range(-len(plane), 0))

        return cast(NDArrayBool, sections[tuple(at)])

    def section_coordinates(self, plane: Sequence[int], at: Sequence[int]) -> NDArrayFloat:
        grid_coordinates = self.grid_coordinates(plane)
        points = grid_coordinates[self.section(plane, at).ravel()]

        return cast(NDArrayFloat, points)

    def with_distance(self, domain: str | None = None) -> RegularGrid:
        assert domain is None
        assert np.issubdtype(self.dtype, np.bool_)

        # Add border of False around data
        padded = np.pad(self, 1, mode='constant', constant_values=False)  # type: ignore

        # Compute euclidian distance to closest border
        result = ndimage.distance_transform_edt(padded)

        # Extract distances without 0 border
        distances = result[tuple(slice(1, -1) for _ in range(result.ndim))]

        return RegularGrid(distances, self.metadata)

    def distances(self, domain: str | None = None) -> NDArrayFloat:
        assert np.issubdtype(self.dtype, np.bool_)

        nonzero_distances = self.with_distance(domain)[self]

        return cast(NDArrayFloat, np.asarray(nonzero_distances.ravel()))

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
