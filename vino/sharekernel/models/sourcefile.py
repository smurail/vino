from pathlib import Path
from typing import IO, AnyStr

from django.db import models
from django.conf import settings

from .entity import Entity
from ..utils import store_files, sorted_by_size


class SourceFile(Entity):
    FILE_PATH = 'import/%Y/%m/%d'

    file = models.FilePathField(path=FILE_PATH, verbose_name="Source file")

    @classmethod
    def from_files(cls, *files: IO[AnyStr]):
        saved_files = store_files(cls.FILE_PATH, *files)
        return [
            cls.objects.get_or_create(file=f)[0]
            for f in sorted_by_size(saved_files)
        ]

    def __str__(self):
        return Path(self.file).relative_to(settings.MEDIA_ROOT).as_posix()
