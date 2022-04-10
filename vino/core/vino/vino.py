from __future__ import annotations

import numpy.typing as npt

from typing import Any, cast

from ..numo import Numo
from ..metadata import Metadata
from .typing import NDArrayFloat


_dataformats: dict[str, type] = {}


class Vino(Numo):
    """
    Base class for ViNO core objects.
    """
    DATAFORMAT_METADATUM = 'resultformat.title'
    DATAFORMAT: str

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
            subclass = _dataformats[dataformat]

            return cast(Vino, super().__new__(subclass, data, metadata))
        return cast(Vino, super().__new__(cls, data, metadata))

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        assert cls.DATAFORMAT not in _dataformats
        _dataformats[cls.DATAFORMAT] = cls

    @property
    def dim(self) -> int:
        raise NotImplementedError

    @property
    def bounds(self) -> NDArrayFloat:
        raise NotImplementedError
