import re
import numpy as np

from vino.loaders import FileFormatLoader


class PspModifiedLoader(FileFormatLoader):
    '''
    Reader for the modified output format of the software of Patrick
    Saint-Pierre.  By "modified", it means that the raw output file has been
    modified for give easy access to metadata at the begin of the file.
    '''

    @overrides
    def readFile(self, f):
        '''
        Returns an object of class BarGridKernel loaded from an output file
        from the software of Patrick Saint-Pierre.
        '''

        bgk = None

        origin = list(map(float, re.findall('-?\d+\.?\d*', f.readline())))
        dimension = len(origin)

        if dimension == 0:
            raise FileFormatException("Couldn't find more than 0 dimension")

        opposite = list(map(float, re.findall('-?\d+\.?\d*', f.readline())))
        intervalNumber = list(map(int, re.findall('\d+', f.readline())))

        if dimension != len(opposite) or dimension != len(intervalNumber):
            raise FileFormatException("Dimensions of metadata mismatch")

        # Read point size
        line = f.readline()
        pointSize = next(map(int, re.findall('\d+', line)), None)
        intervalNumber = [e // pointSize for e in intervalNumber]

        # Read columns headers
        line = f.readline()
        ignoreColumns = len(re.findall('empty', line))

        # Make permutation matrix
        permutVector = list(map(int, re.findall('[0-9]+', line)))
        permutation = np.zeros((dimension, dimension), int)
        for i in range(dimension):
            permutation[i][permutVector[i]-1] = 1

        # Create container object
        bgk = BarGridKernel(origin, opposite, intervalNumber, permutation)

        # Ignore lines until 'Initxx'
        while True:
            line = f.readline()
            if 'Initxx' in line:
                break

        # Read bars
        for line in f:
            coords = list(map(int, re.findall('\d+', line)))
            coords = [e // pointSize for e in coords]
            bgk.addBar(coords[ignoreColumns:-2], coords[-2], coords[-1])
            # TODO what is done with modelMetadata and nbDim

        return bgk
