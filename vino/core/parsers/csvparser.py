from __future__ import annotations

import re
import pandas as pd
import numpy as np

from pandas.errors import ParserError as PandasParseError  # type: ignore
from typing import TextIO

from .parser import Parser
from .exceptions import ParseError


C_ERROR_PATTERN = re.compile('C error: (.*)')


class CSVParserMixin:
    @classmethod
    def parse_csv_to_numpy(
            cls,
            stream: TextIO,
            skiprows: int = 0,
            usecols: list[int] | None = None,
            header: bool = True,
            dtype: str | type | None = None) -> np.ndarray:

        try:
            df = pd.read_csv(
                stream,
                skiprows=skiprows,
                usecols=usecols,
                dtype=dtype,
                na_filter=False,
                delim_whitespace=True,
                low_memory=True,
                header=0 if header else None,
            )

        except PandasParseError as e:
            msg = e.args[0]
            match = C_ERROR_PATTERN.search(msg)
            if match:
                msg = match.group(1)
            raise ParseError(f"CSV parse error: {msg}") from e

        except ValueError as e:
            raise ParseError(f"CSV parse error: {e.args[0]}") from e

        return df.to_numpy()


class CSVParser(CSVParserMixin, Parser[np.ndarray]):
    def parse(self, stream: TextIO) -> np.ndarray:
        return self.parse_csv_to_numpy(stream)
