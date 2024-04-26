'''
Created on Oct 02, 2019

@author: Sascha Kuhnke
'''
import os
import sys
import pathlib


def add_averages_to_results():
    """Appends averages to algorithm results file."""
    
    dir_output = sys.argv[1]
    
    # Change to the main working directory
    path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
    os.chdir(os.path.join(path_working_directory, "..", "..")) 

    path_algorithm_results_file = os.path.join(dir_output + ".ods")
    
    if os.path.isfile(path_algorithm_results_file):
        # Read data from results file
        results_file = open(path_algorithm_results_file, 'r')
        results = results_file.readlines()
        n_results = len(results)
        n_columns = results[0].count(',')
        results_file.close()    
    
        # Append averages to results file
        results_file = open(path_algorithm_results_file, 'w')
        
        averages = "Avg"
        column = "A"
        for _ in range(n_columns):
            column = chr(ord(column) + 1)
            average_curr = "AVERAGE(" + column + "2:" + column + str(n_results) + ")"
            averages += ',"=IF(ISNUMBER(' + average_curr + '), ROUND(' + average_curr + ', 0), ' + '"-"' + ')"' 
        averages += "\n"
        
        results.append(averages)
    
        results_file.writelines(results)
        results_file.close()  


if __name__ == '__main__':
    
    add_averages_to_results()
      
    
