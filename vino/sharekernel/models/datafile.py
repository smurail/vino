from __future__ import annotations

import shutil

from typing import Sequence
from pathlib import Path
from tempfile import NamedTemporaryFile

from django.utils.text import slugify
from django.core.files.storage import default_storage

import vino as vn

from vino.typing import AnyPath

from ..utils import hash_file


def make_datafile(path, files: Sequence[AnyPath]) -> tuple[vn.Vino, Path]:
    # Create a Vino object from files
    vno = vn.load(*files)

    # Save the Vino to a temporary file in CSV format
    temp = NamedTemporaryFile(mode='w', newline='', delete=False)
    vn.save_csv(temp, vno)
    temp.close()

    # Generate datafile name and path
    parts = (
        vno.metadata['viabilityproblem.title'],
        vno.metadata['results.title'],
        hash_file(temp.name, algorithm='sha256'),
    )
    name = '_'.join(slugify(p) for p in parts) + '.csv'
    path = Path(default_storage.path(Path(path) / name))

    # Move temporary file to this path
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(temp.name, path)

    return vno, path
