import shutil

from typing import Iterable
from pathlib import Path
from tempfile import mktemp

from .files import AnyPath
from .metadata import Metadata
from .data import parse_datafile
from .utils import slugify


class DataFileError(Exception):
    pass


class DataFileParseError(DataFileError):
    pass


class DataFile:
    """
    A datafile object represents a concrete Viable Numerical Object

    Parameters
    ----------
    sources : AnyPath
        Paths of source data files to be parsed to build the datafile

    Attributes
    ----------
    TEMPFILE_DIR : str
        Directory where to write temporary file
    DATAFILE_DIR : str
        Directory where to store datafile
    metadata : Metadata
        Dict storing metadata
    tempfile : Path
        Path to temporary file generated while parsing
    path : Path
        Path to datafile
    size : int
        Size of datafile in bytes
    """
    TEMPFILE_PREFIX = 'vino-'
    TEMPFILE_DIR = '/tmp/vino/'
    DATAFILE_DIR = ''
    FILENAME_FIELDS = ('viabilityproblem.title', 'results.title')

    def __init__(self, sources: Iterable[AnyPath]):
        self.metadata = Metadata()
        self.tempfile = self.generate_tempfile_path()
        self.path = Path()
        self.size = 0

        if sources:
            self.parse(sources)

    @property
    def relative_path(self) -> str:
        """Datafile path relative to self.DATAFILE_DIR"""
        return self.path.relative_to(self.DATAFILE_DIR).as_posix()

    def feed(self, source: AnyPath) -> int:
        """Parse `source` file and append result to temporary file

        Parameters
        ----------
        source : AnyPath
            Path of source data file to be parsed

        Raises
        ------
        DataFileParseError
            Any exception raised while parsing

        Returns
        -------
        feed : int
            Size of processed data in bytes
        """
        size = parse_datafile(source, target=self.tempfile, metadata=self.metadata)
        self.size += size
        return size

    def parse(self, sources: Iterable[AnyPath]):
        """Parse `sources` and store result in a new file

        Parameters
        ----------
        sources : AnyPath
            Paths of source data files to be parsed
        """
        try:
            # Parse each source file
            for f in sources:
                self.feed(f)
            # Store datafile and remove temporary file
            filename = self.generate_filename()
            self.path = self.store(filename)
        except Exception as e:
            raise DataFileParseError("Parse error") from e
        finally:
            if self.tempfile.is_file():
                self.tempfile.unlink()

    def store(self, filename: str) -> Path:
        """Store temporary file in `self.DATAFILE_DIR` and return its path"""
        path = Path(self.DATAFILE_DIR).joinpath(filename).as_posix()
        return Path(shutil.copy(self.tempfile, path))

    def generate_tempfile_path(self) -> Path:
        """Return a newly generated path for temporary file"""
        return Path(mktemp(dir=self.TEMPFILE_DIR, prefix=self.TEMPFILE_PREFIX))

    def generate_filename(self) -> str:
        """Return the datafile name from metadata"""
        if not self.metadata:
            raise DataFileError(
                "Datafile must be parsed before generating its filename")
        parts = (slugify(self.metadata.get(f)) for f in self.FILENAME_FIELDS)
        return '_'.join(parts) + '.csv'
