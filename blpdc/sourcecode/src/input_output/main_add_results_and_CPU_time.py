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
    
    algorithm = "qcp-solver"
    qcp_solver = "gurobi"
    
    # Change to the main working directory
    path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
    os.chdir(os.path.join(path_working_directory, "..", "..")) 
    
    path_output = os.path.join(dir_output)
    path_log_file = os.path.join(path_output, instance_name, instance_name + ".log")
    path_time_file = os.path.join(path_output, instance_name + ".time")
    path_results_file = os.path.join(path_output, instance_name, "results.csv")
    
    # Read objective value and dual bound
    log_file = open(path_log_file, 'r')
    data_log_file = log_file.readlines()
    string1 = ""
    string2 = ""
    num_line = 0
    while string1 != "Best" or string2 != "objective":
        line_curr = data_log_file[num_line].split()
        if len(line_curr) > 1:
            string1 = line_curr[0]
            string2 = line_curr[1]
        num_line += 1
    log_file.close()
        
    objective_value = float(line_curr[2][:-1])
    dual_bound = float(line_curr[5][:-1])
    
    # Read System, User, and CPU Time from the file.
    time_file = open(path_time_file, 'r')
    data_time_file = time_file.readlines()
    sys_time = float(data_time_file.pop()[4:-1])
    user_time = float(data_time_file.pop()[4:-1])
    
    # Determine actual CPU Time
    cpu_time = round(user_time + sys_time)
    time_file.close()

    # Create results file 
    results_file = open(path_results_file, 'w')
    results_file.write("Instance" + "," + "Algorithm" + "," + "QCP solver" + "," + "Solved" + "," + "Dual bound" + "," + 
                               "Objective" + "," + "Time" + "," + "CPU time" + "\n")
    results_file.write(instance_name + "," + algorithm + "," + qcp_solver + "," + "-" + "," + str(dual_bound) + "," + 
                            str(objective_value) + "," + "-" + "," + str(cpu_time) + "\n")

    results_file.close()


if __name__ == '__main__':
    
    add_cpu_time_to_results()
    
    
