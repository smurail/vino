from __future__ import annotations

from typing import TextIO

from .parser import ParserOutput
from .exceptions import WrongFormatError
from .metadataparser import MetadataParser
from .pspparser import PSPParser
from .richcsvparser import RichCSVParser


def sourcefile_parse(stream: TextIO) -> ParserOutput:
    assert stream.seekable()

    # XXX Don't factorize following code blocks to let mypy correctly
    #     understand return types

    # 1. Is it a metadata file?
    try:
        return MetadataParser().parse(stream)
    except WrongFormatError:
        stream.seek(0)

    # 2. Is it a PSP file?
    try:
        return PSPParser().parse(stream)
    except WrongFormatError:
        stream.seek(0)

    # 3. Otherwise, we expect a RichCSV file
    return RichCSVParser().parse(stream)
