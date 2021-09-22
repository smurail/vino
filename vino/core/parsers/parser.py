from typing import Generic, TypeVar, TextIO

from .exceptions import InvalidFormatError


T = TypeVar('T')


class Parser(Generic[T]):
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.at_eof = False

    def parse(self, stream: TextIO) -> T:
        raise NotImplementedError

    @staticmethod
    def handle_unicode_decode_error(stream: TextIO, e: UnicodeDecodeError, prefix: str = "") -> None:
        name = getattr(stream, 'name', '<unknown>')
        msg = f'Input stream {name!r} seems to be binary and cannot be opened as text'
        raise InvalidFormatError(prefix + msg) from e
