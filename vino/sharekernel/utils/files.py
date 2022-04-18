from __future__ import annotations

import os
import datetime

from pathlib import Path
from typing import IO, AnyStr, Iterable, Union

from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage, default_storage


StringPath = Union[str, os.PathLike]


def interpolate_path(path: StringPath) -> Path:
    interpolated_path = datetime.datetime.now().strftime(os.fspath(path))
    return Path(settings.MEDIA_ROOT) / interpolated_path


def as_django_file(f: IO[AnyStr]) -> File:
    return f if isinstance(f, File) else File(f)


def store_files(path: StringPath, *files: IO[AnyStr], storage: Storage = default_storage) -> list[Path]:
    # NOTE f.name is in fact the path of f file object
    return [
        store_one_file(Path(path) / Path(f.name).name, f, storage)
        for f in files
    ]


def store_one_file(filepath: StringPath, content: IO[AnyStr], storage: Storage = default_storage) -> Path:
    path = interpolate_path(filepath).as_posix()
    name = storage.save(path, as_django_file(content))
    return Path(storage.path(name))


def sorted_by_size(files: Iterable[StringPath]) -> list[StringPath]:
    return sorted(files, key=lambda f: Path(f).stat().st_size)
