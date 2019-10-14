from abc import ABCMeta, abstractmethod
from vino import METADATA

class Kernel(metaclass=ABCMeta):

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

    @abstractmethod
    def isInSet(self, point):
        '''
        Return a boolean to indicate if a point is inside or outside from this kernel.
        '''
