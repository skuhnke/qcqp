'''
Created on Sep 8, 2020

@author: Sascha Kuhnke
'''

import os
import pathlib
import random
import sys


# Constants
ONE = 1.0
ZERO = 0.0


def get_random_number_not_on_bounds():
    """Return a random number within the interval (0, 1)."""
    
    random_number = random.random()
    while random_number == ZERO or random_number == ONE:
        random_number = random.random()
    
    return random_number
    
    
def generate_boxQP_instance_with_random_bounds_on_bilinearities(name_of_instance, probability_of_lower_or_upper_bound):
    """Write boxQP instance with random bounds based on a given probability into an lp file."""
    
    # Set random seed
    seed = int(probability_of_lower_or_upper_bound * 100 + int(name_of_instance[4:7]) + 
                                int(name_of_instance[8:11]) + int(name_of_instance[12:13]))
    random.seed(seed)
    
    # Change to the main working directory
    path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
    os.chdir(os.path.join(path_working_directory, "..")) 
    
    # Open the boxQP input file 
    path_of_instance = os.path.join("input", "boxQP_instances", name_of_instance + ".dat")

    try:
        with open(path_of_instance, 'r') as input_file:
            lines = input_file.readlines()
    except EnvironmentError:
        print("Cannot not open instance file.")
        sys.exit()
    
    # Open the output file 
    path_output = os.path.join("output", "boxQP_instances")  
    if not os.path.exists(path_output):
        os.makedirs(path_output)  
    path_boxqp_instance = os.path.join(path_output, name_of_instance + "_" + str(probability_of_lower_or_upper_bound) + ".lp")
    boxqp_instance_file = open(path_boxqp_instance, 'w')
    
    num_line = 1    
    line_curr = lines[num_line].split()        
    
    num_variables = int(line_curr[0])
    num_equations_eq = 0
    num_equations_ge = 0
    num_equations_le = 0
    
    num_line = 3
    line_curr = lines[num_line].split()
    num_matrix_nonzeros = int(line_curr[0])
   
   
    string_objective = "Minimize\n"
    string_objective += " obj: "
    
    # Write quadratic part of objective function.
    string_objective += "["
    for i in range(num_matrix_nonzeros):
        num_line = 5 + i
        line_curr = lines[num_line].split()
        if line_curr[2][0] == "-":
            coefficient = " - " + line_curr[2][1:]
        else:
            coefficient = " + " + line_curr[2]
        string_objective += coefficient + " " + "x_" + line_curr[0] + " * " + "x_" + line_curr[1]
    string_objective += " ]"
    
    # Initialize linear part of objective function.
    linear_coefficients = {}
    for i in range(num_variables):
        linear_coefficients[i + 1] = str(0.0)
    
    num_line = 6 + num_matrix_nonzeros
    line_curr = lines[num_line].split()
    num_nonzeros = int(line_curr[0])
    
    # Collect non-zero linear part of objective function.
    for i in range(num_nonzeros):
        num_line = 8 + num_matrix_nonzeros + i
        line_curr = lines[num_line].split()
        linear_coefficients[int(line_curr[0])] = line_curr[1]
    
    # Write linear part of objective function.
    for i in range(num_variables):
        if linear_coefficients[i + 1][0] == "-":
            coefficient = " - " + linear_coefficients[i + 1][1:]
        else:
            coefficient = " + " + linear_coefficients[i + 1]
        string_objective += coefficient + " " + "x_" + str(i + 1)
    
    
    string_constraints = "Subject To\n"
    
    # Create constraints which require certain bilinear terms to be zero.
    num_constraint = 2    
    for i in range(num_matrix_nonzeros):
        # Only create constraints based on the given probability.
        if random.random() < probability_of_lower_or_upper_bound:
            num_line = 5 + i
            line_curr = lines[num_line].split()
            
            string_constraints += (" e" + str(num_constraint) + ": [ " + " x_" + line_curr[0] + " * " + 
                                        "x_" + line_curr[1] + " ] = " + str(ZERO) + "\n")            

            num_constraint += 1
            num_equations_eq += 1

    
    # Write box constraints
    string_bounds = "Bounds\n"
    for i in range(num_variables):
        string_bounds += " " + "x_" + str(i + 1) + " <= " + str(1.0) + "\n"
            

    boxqp_instance_file.write("\ Equation counts\n")
    boxqp_instance_file.write("\     Total        E        G        L        N        X        C        B\n")
    boxqp_instance_file.write("\\\t" + str(num_equations_eq + num_equations_le + num_equations_ge) + "\t" + 
                                        str(num_equations_eq) + "\t" + str(num_equations_ge) + "\t" + str(num_equations_le) + "\n")                    
    boxqp_instance_file.write("\\\n") 
    boxqp_instance_file.write("\ Variable counts\n")
    boxqp_instance_file.write("\                  x        b        i      s1s      s2s       sc       si\n")
    boxqp_instance_file.write("\     Total     cont   binary  integer     sos1     sos2    scont     sint\n")
    boxqp_instance_file.write("\\\t" + str(num_variables) + "\t" + str(num_variables) + "\n")
    boxqp_instance_file.write("\n")
    boxqp_instance_file.write("\ Nonzero counts\n")
    boxqp_instance_file.write("\     Total    const       NL      DLL\n")
    boxqp_instance_file.write("\\\n")
    boxqp_instance_file.write("\\\n")
    boxqp_instance_file.write(string_objective)
    boxqp_instance_file.write("\n\n")
    boxqp_instance_file.write(string_constraints)
    boxqp_instance_file.write("\n")
    boxqp_instance_file.write(string_bounds)
    boxqp_instance_file.write("\n")    
    boxqp_instance_file.write("End")
    boxqp_instance_file.close()    
      
    
if __name__ == '__main__':
    
    name_of_instance = sys.argv[1]
    
    probabilities = [0.0, 0.05, 0.1, 0.15, 0.20, 0.25, 0.5, 0.75, 1.0]
    for probability_of_lower_or_upper_bound in probabilities:
        generate_boxQP_instance_with_random_bounds_on_bilinearities(name_of_instance, probability_of_lower_or_upper_bound)


