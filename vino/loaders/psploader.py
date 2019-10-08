import re
import numpy as np

from vino.loaders import FileFormatLoader
from vino import METADATA


class PspLoader(FileFormatLoader):
    '''
    Reader for the raw output format of the software of Patrick Saint-Pierre.
    '''
    @overrides
    def readFile(self, f):
        metadata={}
        bgk = None
        f.readline()
        nbDim = re.match('\s*([0-9]*)\s.*',f.readline()).group(1)
        metadata[METADATA.dynamicsdescription] = f.readline()
        metadata[METADATA.stateconstraintdescription] = f.readline()
        metadata[METADATA.targetdescription] = f.readline()
        for i in range(4): f.readline()
        dimensionsSteps = list(map(int, re.findall('[0-9]+', f.readline())))
        for i in range(2): f.readline()
        origin = list(map(int, re.findall('[0-9]+', f.readline())))
        maxPoint = list(map(int, re.findall('[0-9]+', f.readline())))
        for i in range(5): f.readline()
        # ND Why? Why not opposite = maxPoint
        opposite = origin
        bgk = BarGridKernel(origin, opposite, dimensionsSteps, metadata=metadata)
        # reading until some lines with 'Initxx'
        stop=False
        initxx=False
        # ND Why restrict min/max point to integer position
        bgk.kernelMinPoint = [e//1 for e in origin]
        bgk.kernelMaxPoint = [e//1 for e in maxPoint]
        while not stop:
            line = f.readline()
            if 'Initxx' in line:
                initxx = True
            elif initxx and 'Initxx' not in line:
                stop = True
        # reading bars
        for line in f:
            coords = list(map(int, re.findall('[0-9]+', line)))
            # ND Why convert point to integer position
            coords = [e//1 for e in coords]
            bgk.addBar(coords[2:-2], coords[-2], coords[-1])
            # TODO what is done with modelMetadata and nbDim
        return bgk
