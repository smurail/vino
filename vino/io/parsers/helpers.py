import numpy as np

from typing import TextIO, Union

from .exceptions import InvalidFormatError
from .metadataparser import MetadataParser
from .pspparser import PSPParser
from .viabilitreeparser import ViabilitreeParser
from .richcsvparser import RichCSVParser

from ...core.metadata import Metadata
from ...core.vino import Vino


def sourcefile_parse(stream: TextIO) -> Union[Metadata, np.ndarray, Vino]:
    assert stream.seekable()

    # XXX Don't factorize following code blocks to let mypy correctly
    #     understand return types

    # 1. Is it a metadata file?
    try:
        return MetadataParser().parse(stream)
    except InvalidFormatError:
        stream.seek(0)

    # 2. Is it a PSP file?
    try:
        return PSPParser().parse(stream)
    except InvalidFormatError:
        stream.seek(0)

    # 3. Is it a Viabilitree file?
    try:
        return ViabilitreeParser().parse(stream)
    except InvalidFormatError:
        stream.seek(0)

    # 4. Otherwise, we expect vino datafile
    return RichCSVParser().parse(stream)
