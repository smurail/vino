from .base import FileFormatLoader
from ..kernels import BarGridKernel, KdTreeKernel
from ..kernels.hdf5common import HDF5Manager


class Hdf5Loader(FileFormatLoader):
    '''
    Loader for the Vino HDF5 file format.
    '''

    def __init__(self, strategies=[BarGridKernel, KdTreeKernel]):
        self.hdf5manager = HDF5Manager(strategies)

    def read(self, filename):
        return self.hdf5manager.readKernel(filename)
