from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models


class Command(BaseCommand):
    help = "List all uploaded files referenced in database."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # List all file fields of all models of sharekernel app
        self.filefields = []
        filefield_type = (models.FileField, models.FilePathField)
        for model in apps.get_app_config("sharekernel").get_models():
            if not model._meta.proxy:
                for field in model._meta.get_fields():
                    if isinstance(field, filefield_type):
                        self.filefields.append(field)

    def handle(self, *args, **kwargs):
        query = None
        for field in self.filefields:
            qs = field.model.objects
            is_empty = {field.name: ''}
            subquery = qs.exclude(**is_empty).values_list(field.name, flat=True)
            query = subquery if query is None else query.union(subquery)
        for path in query:
            self.stdout.write(path)
