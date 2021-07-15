from __future__ import annotations

import numpy as np

from typing import TextIO

from .exceptions import InvalidFormatError
from .datafileparser import DataFileParser, DataFile


class PSPParser(DataFileParser):
    PSP_HEADER = 'Initxx'
    DTYPE = np.uint32

    @classmethod
    def is_pspheader(cls, line: str) -> bool:
        return line.strip() == cls.PSP_HEADER

    @classmethod
    def parse_data(
            cls,
            stream: TextIO,
            columns: list[int] | None = None) -> np.ndarray:

        next_line = next(stream, '')
        if cls.is_pspheader(next_line):
            return cls.parse_csv_to_numpy(
                stream,
                dtype=cls.DTYPE,
                usecols=columns
            )

        raise InvalidFormatError("Couldn't find PSP header")

    def parse(self, stream: TextIO) -> DataFile:
        # Parse metadata
        metadata = self.parse_metadata(stream)

        # Read ColumnDescription metadatum
        coldesc = metadata.get('ColumnDescription')
        if not coldesc:
            raise InvalidFormatError("ColumnDescription metadata not found")

        # Generate integer indices list of columns to be kept
        columns = [i for i, c in enumerate(coldesc) if c != 'empty']

        # Parse PSP data keeping only specified columns
        data = self.parse_data(stream, columns=columns)

        return metadata, data
