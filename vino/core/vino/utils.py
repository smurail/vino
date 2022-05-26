from __future__ import annotations

from typing import cast

import numpy as np
import numpy.typing as npt
import numpy.lib.recfunctions as rfn

from .typing import NDArrayFloat


def asrecords(a: npt.NDArray, cols: list[str] | None = None) -> npt.NDArray:
    return cast(npt.NDArray, rfn.unstructured_to_structured(
        a,
        names=cols,
        copy=False,
        casting='no'
    ))


class RectanglesMixin:
    def rectangles(self) -> NDArrayFloat | None:
        raise NotImplementedError

    def rectangles_coordinates(self) -> tuple[NDArrayFloat, NDArrayFloat] | None:
        rectangles = self.rectangles()

        if rectangles is None:
            return None

        stops = np.full(len(rectangles), np.nan)
        x0, y0, x1, y1 = range(4)

        x = np.column_stack((rectangles[:, (x0, x1, x1, x0, x0)], stops)).ravel()  # type: ignore
        y = np.column_stack((rectangles[:, (y0, y0, y1, y1, y0)], stops)).ravel()  # type: ignore

        return (x, y)
