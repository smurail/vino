from __future__ import annotations

import numpy as np

from typing import BinaryIO

from vino import Vino
from vino.typing import AnyPath


def save_npz(file: BinaryIO | AnyPath, vino: Vino) -> None:
    np.savez(file, data=vino, metadata=vino.metadata)  # type: ignore


def load_npz(file: BinaryIO | AnyPath) -> Vino:
    try:
        npz = np.lib.npyio.NpzFile(file, allow_pickle=True)  # type: ignore
    except Exception as e:
        raise ValueError(f'Failed to load `.npz` file {file!r}') from e

    return Vino(npz['data'], npz['metadata'])
