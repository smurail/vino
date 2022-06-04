from django.core.management.base import BaseCommand

from vino.sharekernel.models import Kernel


class Command(BaseCommand):
    help = (
        "Make datafile from sourcefiles for each Kernel in sharekernel "
        "database, overwriting existing one."
    )

    def handle(self, *args, **kwargs):
        for kernel in Kernel.objects.all():
            self.stdout.write(f"Make datafile for {kernel!r}...")
            kernel.update_datafile()
            kernel.save()
        self.stdout.write("All done!")
