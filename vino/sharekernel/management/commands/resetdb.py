from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = 'Clear all data from sharekernel database'

    def confirm(self, msg, default=True):
        default_response = 'Y/n' if default else 'y/N'
        response = input(f"{msg} ({default_response})? ")
        r = response.lower()
        return r != 'n' if default else r == 'y'

    def handle(self, *args, **kwargs):
        msg = "You will lost ALL your data, are you sure"
        if self.confirm(msg, default=False):
            self.stdout.write("Deleting all sharekernel data...")
            for model in apps.get_app_config('sharekernel').get_models():
                model.objects.all().delete()
        else:
            self.stdout.write("Didn't do anything.")
