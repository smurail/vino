from abc import ABC


class FileFormatException(Exception):
    '''
    This exception is raised when an syntax error occurs while trying to read a file.
    '''
    pass


class FileFormatLoader(ABC):
    '''
    Abstract class for loaders that implements a specific format parser.
    '''

    def readFile(self, f):
        pass

    def read(self, filename):
        with open(filename, 'r') as f:
            return self.readFile(f)
