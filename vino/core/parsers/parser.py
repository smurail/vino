from typing import Generic, TypeVar, TextIO


T = TypeVar('T')


class Parser(Generic[T]):
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.at_eof = False

    def parse(self, stream: TextIO) -> T:
        raise NotImplementedError
