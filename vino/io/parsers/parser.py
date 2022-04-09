from typing import TypeVar, Union, Generic, TextIO
from numpy.typing import NDArray

from vino import Metadata, Numo


ParserOutput = Union[Metadata, NDArray, Numo]
T = TypeVar('T', bound=ParserOutput)


class ParserMixin:
    at_eof: bool

    def reset(self) -> None:
        self.at_eof = False


class Parser(ParserMixin, Generic[T]):
    def __init__(self) -> None:
        self.reset()

    def parse(self, stream: TextIO) -> T:
        raise NotImplementedError
