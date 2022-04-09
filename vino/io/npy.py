from __future__ import annotations

import contextlib
import numpy as np

from typing import BinaryIO, cast
from vino.typing import AnyPath
from numpy.typing import NDArray
from os import PathLike


def load_npy(file: BinaryIO | AnyPath) -> NDArray:
    with contextlib.ExitStack() as stack:
        if isinstance(file, (str, bytes, PathLike)):
            file = stack.enter_context(open(file, 'rb'))
        arr = cast(NDArray, np.lib.format.read_array(file))  # type: ignore
    return arr
