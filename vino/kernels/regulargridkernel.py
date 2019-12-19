import numpy as np
from .base import Kernel


class RegularGridKernel(Kernel):
    def __init__(self, originCoords, dimensionsSteps, dimensionsExtents=None, data=None, metadata = {}):
        super(RegularGridKernel, self).__init__(metadata)
        self.originCoords = originCoords
        self.dimensionsSteps = dimensionsSteps
        self.dimensionsExtents = dimensionsExtents
        if data != None:
            self.setGrid(data)
        elif (dimensionsExtents != None):
            self.grid = np.zeros(dimensionsExtents, dtype='bool')

    @staticmethod
    def getFormatCode():
        return "grid"

    @classmethod
    def initFromHDF5(cls, metadata, dataAttributes, data):
        '''
        Create an object of class BarGridKernel from attributes and data loaded from an HDF5 file. This method is intended to be used by the method hdf5common.readKernel
        '''
        return cls(dataAttributes['origin'], dataAttributes['steps'], data=data, metadata=metadata)

    def getData(self):
        return self.grid

    def setGrid(self, grid):
        self.dimensionsExtents = grid.shape
        self.grid = grid

    def set(self, coords, value):
        self.grid.put([coords], value)

    def get(self, coords):
        return self.grid[coords]

    def isInSet(self, point):
        # TODO
        raise NotImplementedError
