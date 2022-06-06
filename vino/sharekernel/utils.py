from __future__ import annotations

import os
import hashlib

from pathlib import Path
from typing import Union, Iterable

from django.core.files.storage import default_storage

from ..typing import AnyPath


StringPath = Union[str, os.PathLike]


def sorted_by_size(files: Iterable[StringPath]) -> list[StringPath]:
    return sorted(files, key=lambda f: Path(f).stat().st_size)


def media_relative_path(path: Path) -> str:
    return path.relative_to(default_storage.location).as_posix()


def hash_file(path: AnyPath, algorithm: str = 'sha1', chunk_size: int = 1024*1024) -> str:
    assert algorithm in hashlib.algorithms_guaranteed, f"Can't find {algorithm} algorithm"
    hasher = getattr(hashlib, algorithm)()
    with open(path, 'rb', buffering=0) as fp:
        while True:
            chunk = fp.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()
