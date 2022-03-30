import numpy as np

from typing import Tuple, TextIO

from .parser import Parser
from .csvparser import CSVParserMixin
from .metadataparser import MetadataParserMixin

from ...core.vino import Vino


class RichCSVParser(MetadataParserMixin, CSVParserMixin, Parser[Vino]):
    @classmethod
    def parse_data(cls, stream: TextIO) -> np.ndarray:
        return cls.parse_csv_to_numpy(stream)

    def parse(self, stream: TextIO) -> Vino:
        # Parse optional metadata header
        metadata = self.parse_metadata(stream)

        # Parse data
        data = self.parse_data(stream)

        return Vino(data, metadata)
