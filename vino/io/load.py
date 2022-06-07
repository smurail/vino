from __future__ import annotations

import contextlib
import numpy as np

from typing import TextIO, BinaryIO, cast
from io import RawIOBase, BufferedIOBase, TextIOWrapper
from numpy.typing import NDArray
from os import PathLike

from vino import Metadata, Numo, Vino
from vino.typing import AnyPath

from .npz import load_npz
from .npy import load_npy
from .parsers.helpers import sourcefile_parse


ENCODING = "utf-8"


def load(*files: TextIO | BinaryIO | AnyPath) -> Vino:
    # We are going to build a list of metadata chunks and another of data ones
    md_chunks: list[Metadata] = []
    dt_chunks: list[Numo | NDArray] = []

    # Parse each file to get a data or metadata chunk
    with contextlib.ExitStack() as stack:
        for file in files:
            # Try first to open file as NPZ
            try:
                vino = load_npz(file)  # type: ignore
                if len(files) > 1:
                    raise ValueError("Please provide only one NPZ file")
                return vino
            except ValueError:
                pass

            # Try to open file as NPY
            try:
                # If file is a text stream an exception will be raised
                dt_chunks.append(load_npy(file))  # type: ignore
                continue
            except (ValueError, TypeError):
                pass

            # If file is a binary stream try to decode it as text
            if isinstance(file, (RawIOBase, BufferedIOBase)):  # type: ignore
                # See https://github.com/python/typeshed/issues/6077
                file = TextIOWrapper(cast(BinaryIO, file), encoding=ENCODING)
            # If file is a path, open it as text
            elif isinstance(file, (str, bytes, PathLike)):
                file = stack.enter_context(open(file, encoding=ENCODING))

            # Assume file is a text stream
            file = cast(TextIO, file)

            # Parse text stream
            r = sourcefile_parse(file)

            if isinstance(r, Numo):
                if r.metadata:
                    md_chunks.append(r.metadata)
                dt_chunks.append(r)
            elif isinstance(r, Metadata):
                md_chunks.append(r)
            else:
                dt_chunks.append(r)

    # Merge all numerical data chunks into one numpy array
    try:
        data = np.concatenate(dt_chunks)  # type: ignore
    except ValueError as e:
        if not dt_chunks:
            raise ValueError("No data found in input files") from e
        raise ValueError("Can't concatenate data chunks") from e

    # Merge all metadata chunks into one Metadata object
    try:
        metadata = md_chunks[0]
    except IndexError as e:
        raise ValueError("No metadata found in input files") from e

    for md in md_chunks[1:]:
        metadata.update(**md)

    return Vino(data, metadata)
