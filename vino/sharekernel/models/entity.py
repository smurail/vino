from typing import Tuple

from django.db import models
from django.core.exceptions import FieldDoesNotExist
from django_currentuser.db.models import CurrentUserField  # type: ignore

from vino.core.data import parse_datafile, Metadata


class EntityQuerySet(models.QuerySet):
    def last_updated(self):
        return self.order_by('-date_updated')

    def last_created(self):
        return self.order_by('-date_created')


class EntityManager(models.Manager):
    def last_updated(self):
        return self.get_queryset().last_updated()

    def last_created():
        return self.get_queryset().last_created()


class Entity(models.Model):
    class Meta:
        abstract = True

    ACTIVE = 1
    DELETED = 2
    STATES = (
        (ACTIVE, 'Active'),
        (DELETED, 'Deleted'),
    )

    owner = CurrentUserField()
    state = models.IntegerField(choices=STATES, default=ACTIVE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    @classmethod
    def field_exists(cls, field):
        try:
            cls._meta.get_field(field)
            return True
        except FieldDoesNotExist:
            return False

    @classmethod
    def prepare_metadata(cls, metadata, **kwargs):
        def field_name(mk):
            k = mk[len(cls.PREFIX):] if '.' in mk else mk
            return cls.METADATA_TO_FIELD.get(k, k)

        metadata = {
            k: metadata.FIELDS[k].unparse(v) for k, v in metadata.items()
        }

        filtered_metadata = {
            k: v for k, v in dict(metadata, **kwargs).items()
            if '.' not in k or k.startswith(cls.PREFIX)
        }

        return {
            field_name(k): v for k, v in filtered_metadata.items()
            if v is not None and cls.field_exists(field_name(k))
        }

    @classmethod
    def from_metadata(cls, metadata, **kwargs):
        values = cls.prepare_metadata(metadata, **kwargs)
        kwargs = {k: values.get(k) for k in cls.IDENTITY if values.get(k)}
        obj, created = cls.objects.get_or_create(defaults=values, **kwargs)
        obj._created = created
        return obj

    @classmethod
    def from_files(cls, *files, owner=None):
        metadata = Metadata()
        for filepath in files:
            parse_datafile(filepath, metadata=metadata)
        return cls.from_metadata(metadata)


class EntityWithMetadata(Entity):
    class Meta:
        abstract = True

    PREFIX = 'entity.'
    IDENTITY: Tuple[str, ...] = ('title',)
    METADATA_TO_FIELD = {
        'contact': 'email',
        'website': 'url',
    }

    title = models.CharField(max_length=200)
    description = models.TextField(default='', blank=True)
    publication = models.TextField(default='', blank=True)
    author = models.CharField(max_length=200, default='', blank=True)
    email = models.CharField(max_length=200, default='', blank=True)
    url = models.URLField(default='', blank=True)
    image = models.ImageField(upload_to='images/%Y/%m/%d', blank=True)

    def __str__(self):
        return self.title
