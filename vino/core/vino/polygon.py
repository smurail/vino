from __future__ import annotations

import numpy as np
import numpy.typing as npt

from typing import cast, Tuple
from PIL import Image, ImageDraw

from ..metadata import Metadata
from .vino import Vino
from .regulargrid import RegularGrid, as_ppa_array
from .bargrid import BarGrid
from .typing import NDArrayFloat


class Polygon(Vino):
    """
    List of 2-dimensional points defining vertices of the polygon enclosing the
    set of viable points.
    """
    DATAFORMAT = 'polygon'

    @property
    def dim(self) -> int:
        return 2

    @property
    def bounds(self) -> NDArrayFloat:
        return cast(NDArrayFloat, np.array(
            (np.min(self, axis=0), np.max(self, axis=0))  # type: ignore
        ))

    def points_coordinates(self) -> NDArrayFloat:
        return np.asarray(self)

    def to_bargrid(self, ppa: int | npt.ArrayLike) -> BarGrid:
        return self.to_regulargrid(ppa=ppa).to_bargrid()

    def to_regulargrid(self, ppa: int | npt.ArrayLike) -> RegularGrid:
        ppa = as_ppa_array(ppa, self.dim)
        assert len(ppa) == 2

        image_size = cast(Tuple[int, int], tuple(ppa))

        unit = (self.bounds[1] - self.bounds[0]) / ppa
        points = np.floor((self - self.bounds[0]) / unit).astype(int)

        img = Image.new('L', image_size, 0)
        ImageDraw.Draw(img).polygon(points.ravel().tolist(), fill=1, outline=0, width=0)
        grid = np.array(img, dtype=bool).T

        metadata = Metadata(
            self.metadata,
            PointSize=1,
            PointNumberPerAxis=ppa - 1,
            MinimalValues=self.bounds[0] + unit/2,
            MaximalValues=self.bounds[1] - unit/2,
        )

        return RegularGrid(grid, metadata)
