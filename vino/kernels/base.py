from abc import ABCMeta, abstractmethod
from vino import METADATA
from .hdf5common import HDF5Manager


class KernelMeta(ABCMeta):
    def __new__(cls, name, bases, dict):
        cls = super().__new__(cls, name, bases, dict)

        format_code = cls.getFormatCode()
        if format_code is not None:
            cls.KERNELS[format_code] = cls

        return cls


class Kernel(metaclass=KernelMeta):
    KERNELS = {}

    def __init__(self, metadata={}):
        self.__metadata = metadata

    @property
    def metadata(self):
        return self.__metadata

    def getMetadata(self):
        return self.__metadata

    def getStateDimension(self):
        return int(self.metadata[METADATA.statedimension])

    @abstractmethod
    def getData(self):
        '''
        Return the object representing the data of the kernel
        '''

    def getDataAttributes(self):
        return {METADATA.resultformat_title: self.getFormatCode()}

    @staticmethod
    @abstractmethod
    def getFormatCode():
        '''
        Return a string that identifies of the format.
        This identifier is used to code the format used in the metadata of the hdf5 file.
        '''

    @abstractmethod
    def toBarGridKernel(self, origin, opposite, intervals):
        pass

    @classmethod
    @abstractmethod
    def initFromHDF5(cls, metadata, dataAttributes, hdf5data):
        '''
        Init a kernel from Vino HDF5 data.
        '''

    @classmethod
    def createFromHDF5(cls, path):
        return HDF5Manager(cls.KERNELS.values()).readKernel(path)

    @abstractmethod
    def isInSet(self, point):
        '''
        Return a boolean to indicate if a point is inside or outside from this kernel.
        '''
