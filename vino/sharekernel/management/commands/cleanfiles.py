from pathlib import Path

from django.core.files.storage import default_storage
from django.template.defaultfilters import pluralize

from vino.sharekernel.models import SourceFile

from .listfiles import Command as BaseCommand


class Command(BaseCommand):
    ROOT = Path(default_storage.location)

    help = (
        "Clean up orphan sourcefile entries from database, and media "
        "files that are not referenced anymore. Eventually clean up empty "
        "directories that may remain. Uploaded files and empty directories "
        f"are searched in {ROOT} directory."
    )

    @classmethod
    def iterfiles(cls):
        """Iterate over all media files in ``ROOT`` directory."""
        for filepath in cls.ROOT.glob("**/*"):
            if filepath.is_file():
                yield filepath.relative_to(cls.ROOT)

    def is_orphan(self, path):
        """Return True if ``path`` is not found anywhere in database."""
        query = None
        for field in self.filefields:
            qs = field.model.objects
            has_path = {f"{field.name}__endswith": path}
            subquery = qs.filter(**has_path).values_list('pk', flat=True)
            query = subquery if query is None else query.union(subquery)
        return not query.exists()

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Really apply changes to database and filesystem."
        )

    def set_options(self, **options):
        self.verbosity = options['verbosity']
        self.force = options['force']

    def handle(self, *args, **kwargs):
        self.set_options(**kwargs)

        # Handle orphan sourcefiles
        sf_count = SourceFile.objects.count()
        sf_orphan = SourceFile.objects.orphans()
        sf_cleaned = sf_orphan_count = sf_orphan.count()
        if self.force:
            sf_cleaned, _ = sf_orphan.delete()

        # Handle orphan media files
        up_count = up_orphan_count = up_cleaned = 0
        verb = "Remove" if self.force else "Would remove"
        for filepath in self.iterfiles():
            up_count += 1
            if self.is_orphan(filepath):
                up_orphan_count += 1
                self.stdout.write(f"{verb} {filepath}...")
                if self.force:
                    up_cleaned += 1
                    self.ROOT.joinpath(filepath).unlink()
        if not self.force:
            up_cleaned = up_orphan_count

        # Handle potential empty directories
        empty_dirs = 0
        # Iterate over directories ensuring deepest ones are listed first
        for dirpath in reversed(sorted(self.ROOT.glob("**"))):
            if not any(dirpath.iterdir()):
                if self.force:
                    dirpath.rmdir()
                empty_dirs += 1

        cleanup_needed = False
        verb = "Cleaned up" if self.force else "Found"

        if sf_orphan_count > 0:
            cleanup_needed = True
            noun = f"orphan{pluralize(sf_orphan_count)}"
            msg = f"{verb} {sf_cleaned}/{sf_count} {noun} in sourcefiles."
            color = (
                self.style.WARNING if not self.force else
                self.style.SUCCESS if sf_orphan_count == sf_cleaned else
                self.style.ERROR
            )
            self.stdout.write(color(msg))
        else:
            self.stdout.write(self.style.SUCCESS("No orphans found in sourcefiles!"))

        if up_orphan_count > 0:
            cleanup_needed = True
            msg = f"{verb} {up_cleaned}/{up_count} orphan media files."
            color = (
                self.style.WARNING if not self.force else
                self.style.SUCCESS if up_orphan_count == up_cleaned else
                self.style.ERROR
            )
            self.stdout.write(color(msg))
        else:
            self.stdout.write(self.style.SUCCESS("No orphans found in media files!"))

        if empty_dirs > 0:
            cleanup_needed = True
            noun = f"director{pluralize(empty_dirs, 'y,ies')}"
            msg = f"{verb} {empty_dirs} empty {noun}."
            color = self.style.SUCCESS if self.force else self.style.WARNING
            self.stdout.write(color(msg))

        if cleanup_needed and not self.force:
            msg = "Didn't cleaned up anything, please use -f option to do so."
            self.stdout.write(self.style.NOTICE(msg))
