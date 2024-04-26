'''
Created on Jun 17, 2020

@author: Sascha Kuhnke
'''
import time


def get_start_time():
    """Returns the current performance counter."""
    
    return round(time.perf_counter(), 2)

    
def get_time_passed(time_start):
    """Calculates the passed time from time_start."""
    
    return round(time.perf_counter() - time_start, 2)