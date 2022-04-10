from __future__ import annotations

from typing import cast

from .vino import Vino


class KdTree(Vino):
    DATAFORMAT = 'kdtree'

    @property
    def dim(self) -> int:
        assert self.size == 0 or len(self.shape) == 2

        # NOTE: column_count = self.shape[1]
        #       column_count = dim + dim * 2 + 1 = dim * 3 + 1
        #       dim = (column_count - 1) / 3

        return (cast(int, self.shape[1]) - 1) // 3
