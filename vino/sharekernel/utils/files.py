import datetime

from pathlib import Path
from os import PathLike
from typing import IO, AnyStr, Iterable

from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage, default_storage

from vino.typing import AnyPath


def interpolate_path(path: AnyPath):
    interpolated_path = datetime.datetime.now().strftime(os.fspath(path))
    return Path(settings.MEDIA_ROOT) / interpolated_path


def as_django_file(f: IO[AnyStr]):
    return f if isinstance(f, File) else File(f)


def store_files(path: AnyPath, *files: IO[AnyStr], storage: Storage = default_storage) -> Path:
    # NOTE f.name is in fact the path of f file object
    return [
        store_one_file(Path(path) / Path(f.name).name, f, storage)
        for f in files
    ]


def store_one_file(filepath: AnyPath, content: IO[AnyStr], storage: Storage = default_storage) -> Path:
    path = interpolate_path(filepath).as_posix()
    return Path(storage.save(path, as_django_file(content)))


def sorted_by_size(files: Iterable[AnyPath]):
    return sorted(files, key=lambda f: Path(f).stat().st_size)
