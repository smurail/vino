import re
import os

from overrides import overrides

from vino import METADATA
from .base import FileFormatLoader
from ..kernels import KdTreeKernel


class ViabilitreeLoader(FileFormatLoader):
    '''
    Loader for the output format of the software viabilitree.
    The loader assumes that a second file with the path and the same name but
    with the file extension '.txt' provides metadata in the form 'key:value'
    for each line.
    The metadata 'viabilityproblem.statedimension' is mandatory for loading the file.
    '''

    @overrides
    def read(self, filename):
        metadata = {}
#        myre = re.compile('^#(.*):(.*)$')
        myre = re.compile('^#([^:]*):(.*)$')
#        myre = re.compile('^([^:]*):(.*)$')
        with open(os.path.splitext(filename)[0]+'.txt') as f:
            for line in f:
                if line.startswith('#'):
                    match = myre.match(line)
                    if match:
                        k, v = match.groups()
                        metadata[k.strip().lower()] = v.strip()
        metadata[METADATA.statedimension] = int(metadata[METADATA.statedimension])
        k = KdTreeKernel.readViabilitree(filename, metadata)

        return k
