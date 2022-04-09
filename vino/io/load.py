from __future__ import annotations

import contextlib
import numpy as np

from typing import TextIO
from numpy.typing import NDArray
from os import PathLike

from vino import Metadata, Numo, Vino
from vino.typing import AnyPath

from .parsers.helpers import sourcefile_parse


def load(*files: TextIO | AnyPath) -> Vino:
    with contextlib.ExitStack() as stack:
        md_chunks: list[Metadata] = []
        dt_chunks: list[Numo | NDArray] = []

        for file in files:
            # Open `file` if it's a path
            # XXX Keep this isinstance to make static type checker happy
            if isinstance(file, (str, bytes, PathLike)):
                file = stack.enter_context(open(file))

            # Parse text stream
            r = sourcefile_parse(file)

            if isinstance(r, Numo):
                md_chunks.append(r.metadata)
                dt_chunks.append(r)
            elif isinstance(r, Metadata):
                md_chunks.append(r)
            else:
                dt_chunks.append(r)

        # Merge all numerical data into one numpy array
        try:
            data = np.concatenate(dt_chunks)  # type: ignore
        except ValueError as e:
            if not dt_chunks:
                raise ValueError("No data found in input files") from e
            raise ValueError("Can't concatenate data chunks") from e

        # Merge all metadata into one Metadata object
        try:
            metadata = md_chunks[0]
        except IndexError as e:
            raise ValueError("No metadata found in input files") from e

        for md in md_chunks[1:]:
            metadata.update(**md)

    return Vino(data, metadata)
