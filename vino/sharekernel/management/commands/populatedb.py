from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.contrib.auth.models import User

from ...models import Kernel


class Command(BaseCommand):
    SAMPLES_PATH = 'samples'

    help = 'Populate sharekernel database with samples data'

    def add_arguments(self, parser):
        parser.add_argument(
            'user', type=str, help='owner name of created objects')

    def handle(self, user, *args, **kwargs):
        samples = [
            'lake/2D_light.txt',
            'lake/2D.txt',
            'lake/lake_Isa_R1.dat',
            'bilingual-viabilitree/bilingual21dil0control0.1ustep0.01WC.dat',
            'bilingual-viabilitree/Bilingual21TS05dil3.dat',
            'rangeland/3D_rangeland.txt',
        ]
        images = {
            'Lake eutrophication': 'lake/photo.JPG',
            'Rangeland management': 'rangeland/photo(3).JPG',
            'Language competition': 'bilingual-viabilitree/bilingual.png',
        }

        try:
            owner = User.objects.get(username=user)
        except User.DoesNotExist:
            raise CommandError(f"User {user} does not exist.")

        for datafile in map(Path, samples):
            # Deduce metadata filename from date filename
            df = Path(self.SAMPLES_PATH) / datafile
            mf = (
                df.with_suffix('.txt') if df.suffix == '.dat' else
                df.parent / Path(f'{df.stem}_metadata.txt')
            )
            # Console feedback
            self.stdout.write(f"Process {str(df)!r} sample...")
            # Check files
            if not df.is_file():
                raise CommandError(f"Data file {df} not found.")
            if not mf.is_file():
                raise CommandError(f"Metadata file {mf} not found.")
            # Create Kernel object from metadata and data files
            k = Kernel.from_files(mf.open('rb'), df.open('rb'), owner=owner)
            # Setup ViabilityProblem image if needed
            vp = k.params.vp
            if not vp.image:
                srcpath = Path(self.SAMPLES_PATH) / Path(images.get(vp.title))
                self.stdout.write(f"Setup image {str(srcpath)!r} for {vp}...")
                with open(srcpath, 'rb') as fp:
                    vp.image.save(srcpath.name, File(fp))
