import numpy as np

from typing import TextIO

from .csvparser import CSVParser


class ViabilitreeParser(CSVParser):
    def parse(self, stream: TextIO) -> np.ndarray:
        return self.parse_csv_to_numpy(stream, dtype=np.float64)
