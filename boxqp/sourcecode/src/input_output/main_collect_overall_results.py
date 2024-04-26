'''
Created on Nov 18, 2020

@author: Sascha Kuhnke
'''
import os
import sys
import pathlib


def get_lines_of_file(path_file):
    """Returns an array with all lines contained in the file."""
    
    file = open(path_file, 'r')
    lines = file.readlines()
    file.close()
    return lines


def collect_overall_results():
    """Collects the algorithm results of the algorithms passed via arguments."""
    
    # Change to the main working directory
    path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
    os.chdir(os.path.join(path_working_directory, "..", ".."))   
    
    # Open the overall results file
    path_overall_results_file = os.path.join("output", "results.ods")
    overall_results_file = open(path_overall_results_file, 'w')
    
    # Open the first results file
    path_results_file = sys.argv[1]
    path_results_file = os.path.join(path_results_file)
    results_file = open(path_results_file, 'r')
    lines = results_file.readlines()

    # Write the first column with the instance names    
    overall_results_file.write("\n")
    for num_line in range(len(lines)):
        line_curr = lines[num_line].split(',')
        overall_results_file.write(line_curr[0] + "\n")
    results_file.close()
    overall_results_file.close()
    
    lines_overall_results_file = get_lines_of_file(path_overall_results_file)
    
    # Collect results of all result files
    for i in range(len(sys.argv) - 1):
        path_results_file = sys.argv[i + 1]
        
        path_results_file = os.path.join(path_results_file)
        results_file = open(path_results_file, 'r')
        lines = results_file.readlines()

        # Determine algorithm
        if path_results_file[7:11] == "disc":
            column_objective = 9
            column_time = 11

            # Add the algorithm name in the first line
            lines_overall_results_file[0] = lines_overall_results_file[0][:-1] + "," + path_results_file[7:-4] + ",\n"
                    
        elif path_results_file[7:17] == "qcp-solver":
            column_dual_bound = 4
            column_objective = 5
            column_time = 7
            
            # Add the algorithm name in the first line
            lines_overall_results_file[0] = lines_overall_results_file[0][:-1] + "," + path_results_file[7:-4] + ",,\n"            

            # Add dual bound
            for num_line in range(len(lines) - 1):
                line_curr = lines[num_line].split(',')
                lines_overall_results_file[num_line + 1] = lines_overall_results_file[num_line + 1][:-1] + "," + line_curr[column_dual_bound] + "\n"
            
        # Add objective
        for num_line in range(len(lines) - 1):
            line_curr = lines[num_line].split(',')
            lines_overall_results_file[num_line + 1] = lines_overall_results_file[num_line + 1][:-1] + "," + line_curr[column_objective] + "\n"
        
        # Add CPU time
        for num_line in range(len(lines) - 1):
            line_curr = lines[num_line].split(',')
            lines_overall_results_file[num_line + 1] = lines_overall_results_file[num_line + 1][:-1] + "," + line_curr[column_time][:-1] + "\n"
                
    # Add averages    
    averages = ""
    column_prefix = ""
    column = "A"
    n_columns = lines_overall_results_file[0].count(',')
    n_instances = len(lines_overall_results_file) - 3
    for _ in range(n_columns):
        column = chr(ord(column) + 1)
        if "Z" < column:
            column_prefix = "A"
            column = "A"
        average_curr = "AVERAGE(" + column_prefix + column + "3:" + column_prefix + column + str(n_instances + 2) + ")"
        averages += ',"=IF(ISNUMBER(' + average_curr + '), ROUND(' + average_curr + ', 0), ' + '"-"' + ')"' 
    averages += "\n"
    
    num_last_line = len(lines_overall_results_file) - 1
    lines_overall_results_file[num_last_line] = lines_overall_results_file[num_last_line][:-1] + averages + "\n"
    
    # Write results to overall results file
    overall_results_file = open(path_overall_results_file, 'w')
    overall_results_file.writelines(lines_overall_results_file)
    overall_results_file.close()


if __name__ == '__main__':
    
    collect_overall_results()
    
    
