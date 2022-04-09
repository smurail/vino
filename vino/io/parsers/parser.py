from typing import TypeVar, Union, Generic, TextIO
from numpy.typing import NDArray

from vino import Metadata, Numo


T = TypeVar('T', bound=Union[Metadata, NDArray, Numo])


class Parser(Generic[T]):
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.at_eof = False

    def parse(self, stream: TextIO) -> T:
        raise NotImplementedError
