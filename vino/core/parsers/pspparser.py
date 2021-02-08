import numpy as np

from typing import TextIO

from .exceptions import InvalidFormatError
from .datafileparser import DataFileParser


class PSPParser(DataFileParser):
    @staticmethod
    def is_pspheader(line: str) -> bool:
        return line.strip() == 'Initxx'

    @classmethod
    def parse_data(cls, stream: TextIO, skiprows: int = 0) -> np.ndarray:
        if cls.is_pspheader(next(stream, '')):
            return cls.parse_csv_to_numpy(
                stream,
                dtype=np.int64,
            )
        raise InvalidFormatError("Couldn't find Patrick Saint-Pierre header")
