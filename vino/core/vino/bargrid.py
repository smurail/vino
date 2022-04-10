from __future__ import annotations

from typing import cast

from .regulargrid import RegularGrid


class BarGrid(RegularGrid):
    DATAFORMAT = 'bars'

    @property
    def dim(self) -> int:
        assert self.size == 0 or len(self.shape) == 2
        return (cast(int, self.shape[1]) - 1) if self.size > 0 else 0
