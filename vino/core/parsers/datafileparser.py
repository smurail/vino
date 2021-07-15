import numpy as np

from typing import Tuple, TextIO

from .parser import Parser
from .csvparser import CSVParserMixin
from .metadataparser import MetadataParserMixin
from ..metadata import Metadata


DataFile = Tuple[Metadata, np.ndarray]


class DataFileParser(MetadataParserMixin, CSVParserMixin, Parser[DataFile]):
    @classmethod
    def parse_data(cls, stream: TextIO) -> np.ndarray:
        return cls.parse_csv_to_numpy(stream)

    def parse(self, stream: TextIO) -> DataFile:
        # Parse optional metadata header
        metadata = self.parse_metadata(stream)

        # Parse data
        data = self.parse_data(stream)

        return metadata, data
