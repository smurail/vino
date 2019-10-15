import logging

from .base import Loader, FileFormatException, FileFormatLoader
from .psploader import PspLoader
from .pspmodifiedloader import PspModifiedLoader
from .viabilitreeloader import ViabilitreeLoader
from .hdf5loader import Hdf5Loader

__all__ = [
    'Loader', 'FileFormatException', 'FileFormatLoader', 'PspLoader',
    'PspModifiedLoader', 'ViabilitreeLoader', 'Hdf5Loader', 'Loader',
]


class Loader(object):
    def __init__(self):
        self.loaders = []

    def loadersdoc(self):
        for loader in self.loaders:
            print("{0}: {1}".format(type(loader).__name__, str(loader.__doc__)))

    def load(self, filename):
        '''
        Load a file by trying all file loaders, and return an object of type Kernel, precisely on of its subtypes.
        Returns None if no suitable loader have succeed to load the file.
        '''

        for loader in self.loaders:
            try:
                return loader.read(filename)
            except Exception as e:
                logging.getLogger(__name__).info("Loading of %s fails with the %s loader: %s",filename, loader, e)

        return None
