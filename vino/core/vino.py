from __future__ import annotations

import numpy as np
import numpy.typing as npt

from .metadata import Metadata


class Vino(np.ndarray):
    metadata: Metadata

    def __new__(cls, data: npt.ArrayLike | None = None, metadata: Metadata | None = None) -> Vino:
        obj = np.asarray(data if data is not None else []).view(cls)
        obj.metadata = metadata or Metadata()
        return obj

    def __array_finalize__(self, obj: npt.NDArray) -> None:
        if obj is None or not hasattr(obj, 'metadata'):
            self.metadata = Metadata()
        else:
            self.metadata = getattr(obj, 'metadata')
