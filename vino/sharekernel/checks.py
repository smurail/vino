from pathlib import Path

from django.core.checks import register, Tags, Error
from django.conf import settings

from .apps import SharekernelConfig


@register(Tags.compatibility)
def check_files_directory(app_configs=None, **kwargs):
    """Move legacy media directories to the new path if needed."""
    errors = []
    changes = {
        # Entity.image
        'data/images':  'images',
        # Kernel.datafile
        'data/kernels': 'kernels',
        # SourceFile.file
        'data/import':  'import',
    }

    def add_error(msg, **kwargs):
        errors.append(Error(msg, obj=SharekernelConfig.name, **kwargs))

    try:
        if not settings.MEDIA_ROOT:
            raise ValueError
        media_dir = Path(settings.MEDIA_ROOT)
        if not media_dir.exists():
            media_dir.mkdir(parents=True, exist_ok=True)
    except (AttributeError, TypeError, ValueError):
        add_error('MEDIA_ROOT setting must be defined.')
    except PermissionError as e:
        add_error(f"{media_dir} media directory can't be created.", hint=e)

    if not errors:
        for old_path, new_path in changes.items():
            old_path = Path(old_path)
            new_path = media_dir / new_path
            if not new_path.exists() and old_path.exists():
                try:
                    Path(old_path).rename(new_path)
                except (PermissionError, OSError):
                    # Django should take care of creating the directories and
                    # raise an error if it can't
                    pass

    return errors
