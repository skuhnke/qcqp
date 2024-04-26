'''
Created on Nov 18, 2020

@author: Sascha Kuhnke
'''
import os
import pathlib


def collect_objectives_iterations():
    """Collects the objectives of each iteration and stores them in a file."""
    
    # Change to the main working directory
    path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
    os.chdir(os.path.join(path_working_directory, "..", "..", "output"))   

    NUM_ITERATIONS = 8
    
    # Create iterations header
    iterations_header = ""
    for i in range(NUM_ITERATIONS):
        iterations_header += str(i) + ", "    

    # Initialize string array for output    
    lines_output = []
    lines_output.append(", ")
    lines_output.append("Instance, ")
    for algorithm in os.listdir("."):
        if os.path.isdir(algorithm):
            for instance in os.listdir(algorithm):
                if os.path.isdir(os.path.join(algorithm, instance)):
                    lines_output.append(instance + ", ")
            break

                    
    for algorithm in os.listdir("."):
        if os.path.isdir(algorithm) and (algorithm.startswith("disc_adaptive") or algorithm.startswith("tp_disc_adaptive")):
            # Write algorithm name and iterations header
            lines_output[0] += algorithm + ", " * NUM_ITERATIONS
            lines_output[1] += iterations_header  
            num_instance = 1          
            for instance in os.listdir(algorithm):
                if os.path.isdir(os.path.join(algorithm, instance)):
                    num_instance += 1
                       
                    # Open the instance summary file
                    path_summary_file = os.path.join(algorithm, instance, instance + ".sum")
                    summary_file = open(path_summary_file, 'r')
                    lines = summary_file.readlines()
                    summary_file.close()
                    
                    # Extract objectives of iterations
                    num_collected = 0
                    for line in lines:
                        if line.startswith("PQ_CHECKER") or line.startswith("QCP_CHECKER"):
                            break
                        if line.startswith("Primal:"):
                            num_collected += 1
                            current_objective = line.split()[1]
                            lines_output[num_instance] += current_objective + ", "
                            if num_collected == NUM_ITERATIONS:
                                break
                    if num_collected < NUM_ITERATIONS:
                        lines_output[num_instance] += (current_objective + ", ") * (NUM_ITERATIONS - num_collected)                            
    
    
    # Write objectives of iterations to the output file
    path_output_file = os.path.join("objectives_iterations.ods")
    output_file = open(path_output_file, 'w')
    output_file.writelines("%s\n" % l for l in lines_output)
    output_file.close()            
    
    
if __name__ == '__main__':
    
    collect_objectives_iterations()
    
    
