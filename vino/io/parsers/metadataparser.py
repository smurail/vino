from __future__ import annotations

import re

from typing import TextIO

from ...core.metadata import Metadata

from .parser import Parser
from .textparser import TextParserMixin
from .exceptions import WrongFormatError


class MetadataParserMixin(TextParserMixin):
    METADATA_LINE = re.compile(r'^#\s*([^:]+?)\s*:\s*(.*?)\s*?$')

    def __init__(self) -> None:
        super().__init__()

        self.lineno = 0
        self.offset = 0

    @staticmethod
    def is_blank(line: str) -> bool:
        return not line.strip()

    @staticmethod
    def is_comment(line: str) -> bool:
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

        try:
            for line in stream:
                line_size = len(line)
                self.lineno += 1
                byte_count += line_size

                if self.is_blank(line) or self.is_comment(line):
                    continue

                key, value = self.parse_metadatum(line)

                # XXX Don't change this line! Let static type checking
                #     understand that `key` can't be None after this block
                if key is None:
                    # We probably reached the end of metadata
                    interrupted = True
                    break

                if metadata.is_defined_field(key):
                    metadata[key] = value

        except UnicodeDecodeError as e:
            self.handle_unicode_decode_error(stream, e, "Metadata parse error: ")

        if interrupted:
            # Rewind the file pointer to the beginning of the previous line
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
            name = getattr(stream, 'name', '<unknown>')
            raise WrongFormatError(
                "Couldn't recognize metadata",
                (name, self.lineno, self.offset, line)
            )
        return metadata
