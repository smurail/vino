import datetime

from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def generate_media_path(path):
    interpolated_path = datetime.datetime.now().strftime(path)
    return Path(settings.MEDIA_ROOT) / interpolated_path


def store_files(path, *files):
    fs = FileSystemStorage(path)
    return [fs.path(fs.save(f.name, f)) for f in files]


def sorted_by_size(files):
    return sorted(files, key=lambda f: Path(f).stat().st_size)
