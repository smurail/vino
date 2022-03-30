from __future__ import annotations

import re
import pandas as pd
import numpy as np

from pandas.errors import ParserError as PandasParseError
from typing import TextIO

from .parser import Parser
from .textparser import TextParserMixin
from .exceptions import ParseError

from ...core.utils import to_int


C_ERROR_PATTERN = re.compile('C error: (.*)')
C_ERROR_LINENO_PATTERN = re.compile(r' (?:in line|at row) (\d+)')


class CSVParserMixin(TextParserMixin):
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
            # Try to extract error message from pandas exception
            msg, args = e.args[0], ()
            match = C_ERROR_PATTERN.search(msg)
            if match:
                # Look for a line number in the pandas error message
                msg = match.group(1)
                match = C_ERROR_LINENO_PATTERN.search(msg)
                if match:
                    # If a line number is found, pass it to our ParseError
                    name = getattr(stream, 'name', '<unknown>')
                    lineno = to_int(match.group(1))
                    args = ((name, lineno, None, None),)
            raise ParseError(f"CSV parse error: {msg}", *args) from e

        except UnicodeDecodeError as e:
            cls.handle_unicode_decode_error(stream, e, "CSV parse error: ")

        except ValueError as e:
            raise ParseError(f"CSV parse error: {e.args[0]}") from e

        return df.to_numpy()


class CSVParser(CSVParserMixin, Parser[np.ndarray]):
    def parse(self, stream: TextIO) -> np.ndarray:
        return self.parse_csv_to_numpy(stream)
