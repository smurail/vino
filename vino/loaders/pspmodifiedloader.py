import re
import numpy as np

from vino.loaders import FileFormatLoader


class PspModifiedLoader(FileFormatLoader):
    '''
    Reader for the modified output format of the software of Patrick Saint-Pierre.
    By "modified", it means that the raw output file has been modified for give easy access to metadata at the begin of the file.
    '''

    @overrides
    def readFile(self, f):
        '''
        Returns an object of class BarGridKernel loaded from an output file from the software of Patrick Saint-Pierre.
        '''
        bgk = None
        origin = list(map(float, re.findall('-?\d+\.?\d*', f.readline())))
        dimension = len(origin)
        if dimension == 0 :
            raise FileFormatException("Dimensions must be > 0")
        opposite = list(map(float, re.findall('-?\d+\.?\d*', f.readline())))
        intervalNumber = list(map(int, re.findall('[0-9]+', f.readline())))
        if dimension !=len(opposite) or dimension!=len(intervalNumber):
            raise FileFormatException("Dimensions of metadata mismatch")
        pointSize = list(map(int, re.findall('[0-9]+', f.readline())))
        intervalNumber = [e//pointSize[0] for e in intervalNumber]
        # reading columns headers and deducing permutation of variables
        line = f.readline()
        columnNumbertoIgnore = len(re.findall('empty', line))
        permutVector = list(map(int, re.findall('[0-9]+', line)))
        permutation = np.zeros(dimension * dimension,int).reshape(dimension,dimension)
        for i in range(dimension):
            permutation[i][permutVector[i]-1]=1
        # Ok, creating the container object
        bgk = BarGridKernel(origin, opposite, intervalNumber,permutation)
        # ignoring lines until 'Initxx'
        stop=False
        while not stop:
            line = f.readline()
            if 'Initxx' in line:
                stop = True
        # reading bars
        stop = False
        while not stop:
            # using a while loop, because the for loop seems buggy with django InMemoryUploadedFile reading
            line = f.readline()
            if not line:
                stop = True
            else:
                coords = list(map(int, re.findall('[0-9]+', line)))
                coords = [e // pointSize[0] for e in coords]
                bgk.addBar(coords[columnNumbertoIgnore:-2], coords[-2], coords[-1])
                # TODO what is done with modelMetadata and nbDim
        return bgk
