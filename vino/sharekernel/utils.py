import datetime

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage


def generate_media_path(path):
    interpolated_path = datetime.datetime.now().strftime(path)
    return Path(settings.MEDIA_ROOT) / interpolated_path


def as_django_file(f):
    return f if isinstance(f, File) else File(f)


def store_files(path, *files):
    fs = FileSystemStorage(path)
    return [
        Path(fs.path(fs.save(fs.generate_filename(Path(f.name).name), f)))
        for f in map(as_django_file, files)
    ]


def store_one_file(filepath, content):
    filepath = Path(filepath)
    content = content if isinstance(content, File) else File(content)
    fs = FileSystemStorage(filepath.parent)
    return Path(fs.path(fs.save(fs.generate_filename(filepath.name), content)))


def sorted_by_size(files):
    return sorted(files, key=lambda f: Path(f).stat().st_size)
