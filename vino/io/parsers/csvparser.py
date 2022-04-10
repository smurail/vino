from __future__ import annotations

import re
import pandas as pd
import numpy.typing as npt

from pandas.core.arrays import ExtensionArray
from pandas.errors import ParserError as PandasParseError
from typing import TextIO, Sequence, cast

from ...core.utils import to_int

from .parser import Parser
from .textparser import TextParserMixin
from .exceptions import ParseError


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
            dtype: str | type | None = None) -> npt.NDArray:

        try:
            # XXX usecols is NOT an ExtensionArray but pandas-stubs does not
            #     correctly declare usecols parameter type, so hack it!
            # XXX float_precision='round_trip' should resolve accuracy issues,
            #     see https://stackoverflow.com/a/36909497
            df = pd.read_csv(
                stream,
                skiprows=skiprows,
                usecols=cast(ExtensionArray, usecols),
                dtype=dtype,
                na_filter=False,
                delim_whitespace=True,
                low_memory=True,
                header=0 if header else None,
                float_precision='round_trip',
            )
            # XXX pandas-stubs does not correctly declare return type for
            #     to_numpy method
            return cast(npt.NDArray, df.to_numpy())

        except PandasParseError as e:
            # Try to extract error message from pandas exception
            msg = e.args[0]
            args: Sequence = ()
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


class CSVParser(CSVParserMixin, Parser[npt.NDArray]):
    def parse(self, stream: TextIO) -> npt.NDArray:
        return self.parse_csv_to_numpy(stream)
