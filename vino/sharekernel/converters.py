from __future__ import annotations
from typing import Sequence


class IntTupleConverter:
    LIMIT = 100

    regex = '[-,0-9]+'

    def to_python(self, value: str) -> tuple[int]:
        return tuple(int(x) for x in value.split(',', self.LIMIT))

    def to_url(self, value: Sequence[int]) -> str:
        return ','.join(value)
