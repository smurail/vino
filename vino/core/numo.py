from __future__ import annotations

import numpy as np
import numpy.typing as npt

from .metadata import Metadata


class Numo(np.ndarray):
    """
    N-dimensional array with a :attr:`metadata` property.

    Numo stands for Numerical Object. This class is derived from Numpy_
    ndarray_. Used to represent completely or partially loaded vino core
    objects in their bare form.

    .. _Numpy: https://numpy.org
    .. _ndarray: https://numpy.org/doc/stable/reference/arrays.ndarray.html
    """
    metadata: Metadata

    def __new__(cls, data: npt.ArrayLike | None = None, metadata: Metadata | None = None) -> Numo:
        obj = np.asarray(data if data is not None else []).view(cls)
        obj.metadata = metadata or Metadata()
        return obj

    def __array_finalize__(self, obj: npt.NDArray) -> None:
        if obj is None or not hasattr(obj, 'metadata'):
            self.metadata = Metadata()
        else:
            self.metadata = getattr(obj, 'metadata')
