from pathlib import Path
from typing import IO, AnyStr

from django.db import models
from django.core.files.storage import default_storage

from .entity import Entity, EntityQuerySet
from ..utils import sorted_by_size, media_save


class SourceFileQuerySet(EntityQuerySet):
    def orphans(self):
        return self.exclude(
            pk__in=SourceFile.kernel_set.through.objects.values('sourcefile'))


class SourceFile(Entity):
    ROOT = default_storage.location
    FILE_PATH = 'import/%Y/%m/%d'

    objects = SourceFileQuerySet.as_manager()

    file = models.FilePathField(path=ROOT, verbose_name="Source file")

    @classmethod
    def from_files(cls, *files: IO[AnyStr]):
        saved_files = [media_save(cls.FILE_PATH, f) for f in files]
        return [
            cls.objects.get_or_create(file=Path(f).relative_to(cls.ROOT))[0]
            for f in sorted_by_size(saved_files)
        ]

    def __str__(self):
        return self.file
