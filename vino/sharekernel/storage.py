from datetime import datetime

from django.core.files.storage import FileSystemStorage


class CustomFileSystemStorage(FileSystemStorage):
    def path(self, name):
        path = super().path(name)
        return datetime.now().strftime(path)
