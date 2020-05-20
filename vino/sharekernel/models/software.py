from django.db import models

from .entity import EntityWithMetadata


class Software(EntityWithMetadata):
    PREFIX = 'software.'
    IDENTITY = ('title', 'version')

    version = models.CharField(max_length=30, default='', blank=True)
    parameters = models.CharField(max_length=200, default='', blank=True)
