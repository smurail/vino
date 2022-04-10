from __future__ import annotations

from .vino import Vino


class RegularGrid(Vino):
    DATAFORMAT = 'regulargrid'

    @property
    def dim(self) -> int:
        return self.ndim
