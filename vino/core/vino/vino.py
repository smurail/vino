from __future__ import annotations

import numpy.typing as npt

from typing import Any, cast, NamedTuple

from ..numo import Numo
from ..metadata import Metadata
from .typing import NDArrayFloat


_dataformats: dict[str, type[Vino]] = {}


class Vino(Numo):
    """
    Base class for ViNO core objects.
    """
    DATAFORMAT_METADATUM = 'resultformat.title'
    VARIABLES_METADATUM = 'viabilityproblem.statevariables'
    DATAFORMAT: str

    columns: list[str]

    class Variable(NamedTuple):
        order: int
        axis: str
        name: str
        desc: str | None = None
        unit: str | None = None

        def __str__(self):
            return self.name

    def __new__(cls, data: npt.ArrayLike, metadata: Metadata) -> Vino:
        if cls is Vino:
            # Get dataformat name
            if metadata and cls.DATAFORMAT_METADATUM not in metadata:
                raise ValueError(
                    f"Metadatum {cls.DATAFORMAT_METADATUM!r} MUST be defined")
            dataformat = metadata[cls.DATAFORMAT_METADATUM]

            # Get vino subclass for this dataformat
            if dataformat not in _dataformats:
                raise ValueError(
                    f"Unknown dataformat {dataformat!r} (available formats: "
                    f"{', '.join((repr(k) for k in _dataformats.keys()))})")
            cls = _dataformats[dataformat]

        metadata = Metadata(metadata)
        metadata[cls.DATAFORMAT_METADATUM] = cls.DATAFORMAT

        return cast(Vino, super().__new__(cls, data, metadata))

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        assert cls.DATAFORMAT not in _dataformats
        _dataformats[cls.DATAFORMAT] = cls

    def axis_name(self, order: int) -> str:
        assert order >= 0
        return 'xyz'[order] if self.dim <= 3 else f'x{order+1}'

    @property
    def variables(self) -> list[Variable]:
        state_variables = self.metadata.get(
            self.VARIABLES_METADATUM,
            [self.axis_name(a) for a in range(self.dim)]
        )
        return [
            self.Variable(
                order=i,
                axis=self.axis_name(i),
                name=v if isinstance(v, str) else v[0],
                desc=None if isinstance(v, str) else v[1] or None,
                unit=None if isinstance(v, str) else v[2] or None,
            )
            for i, v in enumerate(state_variables)
        ]

    @property
    def dim(self) -> int:
        raise NotImplementedError

    @property
    def bounds(self) -> NDArrayFloat:
        raise NotImplementedError
