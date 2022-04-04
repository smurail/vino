from typing import TextIO, NoReturn

from .exceptions import InvalidFormatError


class TextParserMixin:
    @staticmethod
    def handle_unicode_decode_error(stream: TextIO, e: UnicodeDecodeError, prefix: str = "") -> NoReturn:
        name = getattr(stream, 'name', '<unknown>')
        msg = f'Input stream {name!r} seems to be binary and cannot be opened as text'
        raise InvalidFormatError(prefix + msg) from e
