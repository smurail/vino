from pathlib import Path

from django.db import models
from django.conf import settings

from .entity import Entity
from ..utils import store_files, sorted_by_size


class SourceFile(Entity):
    file = models.FilePathField(path='import/%Y/%m/%d', verbose_name="Source file")

    @classmethod
    def from_files(cls, *files):
        saved_files = store_files(cls._meta.get_field('file').path, *files)
        return [
            cls.objects.get_or_create(file=f)[0]
            for f in sorted_by_size(saved_files)
        ]

    def __str__(self):
        return Path(self.file).relative_to(settings.MEDIA_ROOT).as_posix()
