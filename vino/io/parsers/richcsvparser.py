import numpy as np

from typing import TextIO

from ...core.numo import Numo

from .parser import Parser
from .csvparser import CSVParserMixin
from .metadataparser import MetadataParserMixin


class RichCSVParser(MetadataParserMixin, CSVParserMixin, Parser[Numo]):
    @classmethod
    def parse_data(cls, stream: TextIO) -> np.ndarray:
        return cls.parse_csv_to_numpy(stream)

    def parse(self, stream: TextIO) -> Numo:
        # Parse optional metadata header
        metadata = self.parse_metadata(stream)

        # Parse data
        data = self.parse_data(stream)

        return Numo(data, metadata)
