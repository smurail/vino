from typing import TextIO, NoReturn

from .exceptions import WrongFormatError


class TextParserMixin:
    @staticmethod
    def handle_unicode_decode_error(stream: TextIO, e: UnicodeDecodeError, prefix: str = "") -> NoReturn:
        name = getattr(stream, 'name', '<unknown>')
        msg = f'Input stream {name!r} cannot be opened as utf-8 text and might be binary'
        raise WrongFormatError(prefix + msg) from e
