from __future__ import annotations

import numpy as np
import numpy.typing as npt

from typing import cast
from itertools import chain

from ..metadata import Metadata
from .vino import Vino
from .regulargrid import RegularGrid, as_ppa_array
from .bargrid import BarGrid
from .utils import RectanglesMixin, asrecords
from .typing import NDArrayFloat


class KdTree(RectanglesMixin, Vino):
    DATAFORMAT = 'kdtree'

    axes: list[int]

    def __init__(self, data: npt.ArrayLike, metadata: Metadata) -> None:
        # Give names to columns
        self.columns = [f'c{index+1}' for index in range(self.shape[1])]

        # Sort cells in lexical order (ie. in columns order)
        cells_rec = asrecords(self, cols=self.columns)
        cols_min = [self.columns[i] for i in self.indices_min()]
        index = np.argsort(cells_rec, order=cols_min)
        self[:] = self[index]

        space_axes = range(self.dim)
        self.axes = list(chain(
            # N first columns are coordinates of current point
            space_axes,
            # N*2 next columns are (min, max) pairs for each dimension
            chain.from_iterable((x, x) for x in space_axes),
            # Last column is control, what axis should it be?
            [self.dim]
        ))

    @property
    def dim(self) -> int:
        assert self.size == 0 or len(self.shape) == 2

        # NOTE: column_count = self.shape[1]
        #       column_count = dim + dim * 2 + 1 = dim * 3 + 1
        #       dim = (column_count - 1) / 3

        return (cast(int, self.shape[1]) - 1) // 3

    def indices_point(self) -> tuple[int, ...]:
        return tuple(range(self.dim))

    def indices_min(self) -> tuple[int, ...]:
        return tuple(range(self.dim, self.dim*3, 2))

    def indices_max(self) -> tuple[int, ...]:
        return tuple(range(self.dim+1, self.dim*3+1, 2))

    def points_coordinates(self) -> NDArrayFloat:
        return np.asarray(self[:, self.indices_point()])

    def cells_min(self) -> NDArrayFloat:
        return cast(NDArrayFloat, self[:, self.indices_min()])

    def cells_max(self) -> NDArrayFloat:
        return cast(NDArrayFloat, self[:, self.indices_max()])

    def cells(self) -> NDArrayFloat:
        return cast(NDArrayFloat, np.hstack((self.cells_min(), self.cells_max())))

    def rectangles(self) -> NDArrayFloat | None:
        if self.dim != 2:
            return None
        return self.cells()

    @property
    def bounds(self) -> NDArrayFloat:
        return cast(NDArrayFloat, np.array((
            np.min(self.cells_min(), axis=0),  # type: ignore
            np.max(self.cells_max(), axis=0),  # type: ignore
        )))

    def to_regulargrid(self, ppa: int | npt.ArrayLike) -> RegularGrid:
        ppa = as_ppa_array(ppa, self.dim)

        bounds = self.bounds
        unit = (bounds[1] - bounds[0]) / ppa

        cells_min = self.cells_min()
        cells_max = self.cells_max()

        cells_min_int = np.floor((cells_min - bounds[0] + unit/2) / unit).astype(int)
        cells_max_int = np.round((cells_max - bounds[0] - unit/2) / unit).astype(int) + 1  # type: ignore

        assert np.all(cells_min_int <= cells_max_int), "Bogus KdTree rasterization"

        grid = np.full(ppa, False)
        for cmin, cmax in zip(cells_min_int, cells_max_int):
            # Fill grid between cmin *included* and cmax *excluded*
            grid[tuple(slice(cmin[a], cmax[a]) for a in range(self.dim))] = True

        metadata = Metadata(
            self.metadata,
            PointSize=1,
            PointNumberPerAxis=ppa - 1,
            MinimalValues=bounds[0] + unit/2,
            MaximalValues=bounds[1] - unit/2,
        )

        return RegularGrid(grid, metadata)

    def to_bargrid(self, ppa: int | npt.ArrayLike) -> BarGrid:
        return self.to_regulargrid(ppa=ppa).to_bargrid()
