from django.db import models

from .entity import EntityWithMetadata


class DataFormat(EntityWithMetadata):
    PREFIX = 'resultformat.'
    IDENTITY = ('title',)
    METADATA_TO_FIELD = {
        'parameterlist': 'parameters'
    }

    parameters = models.CharField(max_length=200, default='', blank=True)
