from __future__ import annotations

import re

from typing import TextIO

from .parser import Parser
from .exceptions import InvalidFormatError
from ..metadata import Metadata


class MetadataParserMixin:
    METADATA_LINE = re.compile(r'^#\s*([^:]+?)\s*:\s*(.*?)\s*?$')

    def __init__(self) -> None:
        super().__init__()

        self.lineno = 0
        self.offset = 0

    @classmethod
    def is_blank(cls, line: str) -> bool:
        return not line.strip()

    @classmethod
    def is_comment(cls, line: str) -> bool:
        return line[:2] == '//'

    @classmethod
    def parse_metadatum(cls, line: str) -> tuple[str, str] | tuple[None, None]:
        match = cls.METADATA_LINE.match(line)
        return (match.group(1), match.group(2)) if match else (None, None)

    def parse_metadata(self, stream: TextIO) -> Metadata:
        assert stream.seekable()

        metadata = Metadata()
        line_size = 0
        byte_count = 0
        interrupted = False

        for line in stream:
            line_size = len(line)
            self.lineno += 1
            byte_count += line_size

            if self.is_blank(line) or self.is_comment(line):
                continue

            key, value = self.parse_metadatum(line)

            if key is None or value is None:
                interrupted = True
                break

            if metadata.is_defined_field(key):
                metadata[key] = value

        if interrupted:
            stream.seek(0)
            stream.read(byte_count - line_size)
        else:
            self.at_eof = True

        return metadata


class MetadataParser(MetadataParserMixin, Parser[Metadata]):
    def parse(self, stream: TextIO) -> Metadata:
        metadata = self.parse_metadata(stream)
        if not self.at_eof:
            line = next(stream)
            raise InvalidFormatError(
                "Couldn't recognize metadata",
                (stream.name, self.lineno, self.offset, line)
            )
        return metadata
