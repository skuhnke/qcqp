'''
Created on Sep 16, 2019

@author: Sascha Kuhnke
'''


class InputFormatException(Exception):
    """Class for errors in the format of the input file."""
    
    def __init__(self, message):
        super().__init__(message)


class AlgorithmDataException(Exception):
    """Class for errors in the algorithm parameters."""
    
    def __init__(self, message):
        super().__init__(message)
        
        