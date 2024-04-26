'''
Created on Nov 14, 2019

@author: Sascha Kuhnke
'''
import os
import sys
import pathlib


def add_cpu_time_to_results():
    """Appends CPU time to results file."""
    
    instance_name = sys.argv[1]
    dir_output = sys.argv[2]
    
    # Change to the main working directory
    path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
    os.chdir(os.path.join(path_working_directory, "..", "..")) 
    
    path_output = os.path.join(dir_output)
    path_time_file = os.path.join(path_output, instance_name + ".time")
    path_results_file = os.path.join(path_output, instance_name, "results.csv")
    
    # Read System, User, and CPU Time from the file.
    time_file = open(path_time_file, 'r')
    data_time_file = time_file.readlines()
    sys_time = float(data_time_file.pop()[4:-1])
    user_time = float(data_time_file.pop()[4:-1])
    
    # Determine actual CPU Time
    cpu_time = round(user_time + sys_time)
    time_file.close()
    
    if os.path.isfile(path_results_file):
        # Read data from results file
        results_file = open(path_results_file, 'r')
        results = results_file.readlines()
        results_file.close()        
    
        # Add CPU Time
        results_last_instance = results[-1]
        results_last_instance = results_last_instance[0:-1]
        results_last_instance += "," + str(cpu_time) + "\n"
        results[-1] = results_last_instance

        # Update results file 
        results_file = open(path_results_file, 'w')
        results_file.writelines(results)
        results_file.close()


if __name__ == '__main__':
    
    add_cpu_time_to_results()
    
    
