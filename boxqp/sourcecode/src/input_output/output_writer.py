'''
Created on Jun 9, 2020

@author: Sascha Kuhnke
'''
import os
import shutil
import sys

from data.data import AlgorithmData


# Constants
ZERO = 0.0

# Algorithm data
DISCRETIZATION = AlgorithmData.DISCRETIZATION
QCP_SOLVER = AlgorithmData.QCP_SOLVER
IPOPT = AlgorithmData.IPOPT
SNOPT = AlgorithmData.SNOPT
MINOS = AlgorithmData.MINOS


class OutputWriter(object):
    """Class to write all output data."""

    def __init__(self, data):
        
        self.instance_data = data.instance_data
        self.algorithm_data = data.algorithm_data

        self.path_output = None
        self.path_output_of_instance = None
        self.path_summary_file = None
        self.path_solution_file = None
        self.path_logs = None
        self.path_discretizations = None
        self.path_starting_points = None
        
        self.summary_file = None
       
        
    def initialize_output(self):
        """Initializes all necessary paths and folders for the output."""

        self.create_output_folder_for_instance()
        self.set_path_solution_and_results_file()
        self.open_summary_file()
        self.create_log_folders()
        
        if self.algorithm_data.algorithm == DISCRETIZATION:
            self.create_discretization_folder()
            
        if (self.algorithm_data.algorithm == DISCRETIZATION or 
                    (self.algorithm_data.algorithm == QCP_SOLVER and self.algorithm_data.qcp_solver in [IPOPT, SNOPT, MINOS])):
            self.create_starting_points_output_folder()            
        
    
    def create_output_folder_for_instance(self):
        """Creates an empty output directory for this instance."""
        
        name_of_instance = self.instance_data.name
        algorithm_data = self.algorithm_data

        if algorithm_data.algorithm == DISCRETIZATION: 
            self.path_output = os.path.join("output", algorithm_data.algorithm + "_" + algorithm_data.disc_type + "_" + 
                                            algorithm_data.disc_variable_selection + "_" + str(algorithm_data.disc_size))  
        elif algorithm_data.algorithm == QCP_SOLVER: 
            self.path_output = os.path.join("output", algorithm_data.algorithm + "_" + algorithm_data.qcp_solver)
        self.path_output_of_instance = os.path.join(self.path_output, name_of_instance)
        self.make_empty_dir(self.path_output_of_instance)  
        
        if self.instance_data.stderr == None:
            path_stderr = os.path.join(self.path_output_of_instance, "stderr.txt")
            sys.stderr = open(path_stderr, 'w')   
        

    def set_path_solution_and_results_file(self):
        """Sets the path of the solution and results file."""
        
        name_of_instance = self.instance_data.name
        self.path_solution_file = os.path.join(self.path_output_of_instance, name_of_instance + ".sol")
        self.path_results_file = os.path.join(self.path_output_of_instance, "results.csv")
        

    def open_summary_file(self):
        """Opens and initializes the summary file."""
        
        name_of_instance = self.instance_data.name
        algorithm_data = self.algorithm_data
        
        self.path_summary_file = os.path.join(self.path_output_of_instance, name_of_instance + ".sum")
        self.summary_file = open(self.path_summary_file, 'w')
        
        self.write_line(self.summary_file, "------------------------------------")
        self.write_line(self.summary_file, "------------------------------------")
        self.write_line(self.summary_file, "Instance:\t\t" + name_of_instance)
        self.write_line(self.summary_file, "Algorithm:\t\t" + algorithm_data.algorithm)
        if algorithm_data.algorithm == DISCRETIZATION:
            self.write_line(self.summary_file, "Disc type:\t\t" + algorithm_data.disc_type)
            self.write_line(self.summary_file, "Disc selection:\t\t" + algorithm_data.disc_variable_selection)
            self.write_line(self.summary_file, "Disc size:\t\t" + str(algorithm_data.disc_size))
            self.write_line(self.summary_file, "Time limit:\t\t" + str(algorithm_data.time_limit_discretization))
            self.write_line(self.summary_file, "Time limit iteration:\t" + str(algorithm_data.time_limit_iteration))
        elif algorithm_data.algorithm == QCP_SOLVER:
            self.write_line(self.summary_file, "QCP solver:\t\t" + algorithm_data.qcp_solver)
            self.write_line(self.summary_file, "Time limit:\t\t" + str(algorithm_data.time_limit_qcp))
        self.write_line(self.summary_file, "Optimality gap:\t\t" + str(algorithm_data.gap))
        self.write_line(self.summary_file, "------------------------------------\n")
        
        
    def write_line_to_summary_file(self, line):
        """Writes a line to the summary file."""
        
        self.write_line(self.summary_file, line)
        
        
    def write_summary(self, gams_environment, time_required):
        """Writes a summary after solving a problem (or subproblem)."""
        
        model_name = gams_environment.model_name
        dual_bound = gams_environment.get_dual_bound() 
        objective_value = gams_environment.get_objective_value()
        
        if objective_value not in [None, ZERO]:
            gap_reached = round(abs((dual_bound - objective_value) / objective_value), 4)    
        else:
            gap_reached = "NaN"
            
        self.write_line(self.summary_file, "------------------------------------")
        self.write_line(self.summary_file, model_name)
        self.write_line(self.summary_file, "------------------------------------")
        self.write_line(self.summary_file, "Dual:\t " + str(dual_bound))
        self.write_line(self.summary_file, "Primal:\t " + str(objective_value))
        self.write_line(self.summary_file, "Gap:\t " + str(gap_reached))
        self.write_line(self.summary_file, "Time:\t " + str(time_required) + "\n") 
        
        
    def write_error_message(self, error_message, instance_data, algorithm_data):
        """Writes an error message."""
        
        self.write_line(self.summary_file, error_message)
        print("\n\n")
        self.summary_file.close()
        
        instance_name = instance_data.name
        
        results_file = open(self.path_results_file, 'w')
        
        if algorithm_data.algorithm == DISCRETIZATION:
            results_file.write("Instance" + "," + "Algorithm" + "," + "Disc type" + "," + "Disc size" + "," + 
                               "Disc selection" + "," + "Disc selection time" + "," + "Disc variables %" + "," + 
                               "Iterations" + "," + "Solved" + "," + "Objective" + "," + "Time" + "," + 
                               "CPU time" + "\n")    
            results_file.write(instance_name + "," + algorithm_data.algorithm + "," + algorithm_data.disc_type + "," + 
                               str(algorithm_data.disc_size) + "," + algorithm_data.disc_variable_selection + "," + str("-") + "," + 
                               str("-") + "," + str(algorithm_data.iteration) + "," + 
                               error_message + "," + str("-") + "," + str("-") + "\n")
        elif algorithm_data.algorithm == QCP_SOLVER:
            results_file.write("Instance" + "," + "Algorithm" + "," + "QCP solver" + "," + "Solved" + "," + "Dual bound" + "," + 
                               "Objective" + "," + "Time" + "," + "CPU time" + "\n")    
            results_file.write(instance_name + "," + algorithm_data.algorithm + "," + algorithm_data.qcp_solver + "," + 
                           error_message + "," + str("-") + "," + str("-") + "," + str("-") + "\n")
            
        results_file.close()
        
        sys.exit(0)
        
        
    def close_summary_file(self, dual_bound, objective_value, time_required):
        """Writes final objective value and total running time before closing the summary file."""
    
        self.write_line(self.summary_file, "------------------------------------")
        self.write_line(self.summary_file, "Dual bound:\t " + str(dual_bound))
        self.write_line(self.summary_file, "Objective:\t " + str(objective_value))
        self.write_line(self.summary_file, "Total time:\t " + str(time_required))
        self.write_line(self.summary_file, "------------------------------------")
        print("\n\n")
        
        self.summary_file.close()                       
    
    
    def add_results(self, data, is_solved, dual_bound, objective_value, time_required):
        """Adds the current solution to the result file."""
        
        instance_name = data.instance_data.name
        instance_data = data.instance_data
        algorithm_data = data.algorithm_data
        
        results_file = open(self.path_results_file, 'w')
        
        if algorithm_data.algorithm == DISCRETIZATION:
            percentage_disc_variables = round(len(algorithm_data.disc_variables) / float(instance_data.num_variables), 2)           
            
            results_file.write("Instance" + "," + "Algorithm" + "," + "Disc type" + "," + "Disc size" + "," + 
                               "Disc selection" + "," + "Disc selection time" + "," + "Disc variables %" + "," + 
                               "Iterations" + "," + "Solved" + "," + "Objective" + "," + "Time" + "," + 
                               "CPU time" + "\n")    
            results_file.write(instance_name + "," + algorithm_data.algorithm + "," + algorithm_data.disc_type + "," + 
                        str(algorithm_data.disc_size) + "," + algorithm_data.disc_variable_selection + "," + 
                        str(algorithm_data.time_disc_variable_selection) + "," + str(percentage_disc_variables) + "," + 
                        str(algorithm_data.iteration) + "," + str(is_solved) + "," + 
                        str(objective_value) + "," + str(round(time_required)) + "\n")
        elif algorithm_data.algorithm == QCP_SOLVER:
            results_file.write("Instance" + "," + "Algorithm" + "," + "QCP solver" + "," + "Solved" + "," + "Dual bound" + "," + 
                               "Objective" + "," + "Time" + "," + "CPU time" + "\n")    
            results_file.write(instance_name + "," + algorithm_data.algorithm + "," + algorithm_data.qcp_solver + "," + 
                           str(is_solved) + "," + str(dual_bound) + "," + str(objective_value) + "," + 
                           str(round(time_required)) + "\n")
    
        results_file.close()
    
    
    def create_log_folders(self):
        """Creates the output folders for the log files."""
        
        folder_logs = "log_files"
        self.path_logs = os.path.join(self.path_output_of_instance, folder_logs)
        self.make_empty_dir(self.path_logs)


    def open_log_file(self, model_name, log_file_suffix):
        """Opens the log file of the current iteration."""
        
        if log_file_suffix != "":
            log_file_suffix = "_" + str(log_file_suffix)
        
        path_log_file = os.path.join(self.path_logs, model_name.lower() + str(log_file_suffix) + ".log")
        log_file = open(path_log_file, 'w')
    
        return log_file    
    
    
    def close_log_file(self, log_file):
        """Closes the log file of the current iteration."""
        
        log_file.close()    
                
            
    def create_discretization_folder(self):
        """Creates the output folders related to the discretizations."""
        
        folder_discretizations = "discretizations"        
        self.path_discretizations = os.path.join(self.path_output_of_instance, folder_discretizations)
        self.make_empty_dir(self.path_discretizations)
        
        
    def create_starting_points_output_folder(self):
        """Creates the output folder for the starting points."""        
        folder_starting_points = "starting_points"        
        self.path_starting_points = os.path.join(self.path_output_of_instance, folder_starting_points)
        self.make_empty_dir(self.path_starting_points)
        
        
    def write_discretization(self, disc_data, iteration):
        """Writes the discretization data into the corresponding directory."""

        self.write_data_to_file(self.path_discretizations, "discretization_" + str(iteration), disc_data)
        
        
    def write_starting_point(self, starting_point, iteration):
        """Writes the starting point data into the corresponding directory."""
        
        self.write_data_to_file(self.path_starting_points, "starting_point_" + str(iteration), starting_point)        
        
        
    def create_gams_workspace_folder(self, name_gams_workspace):
        """Creates the folder for the GAMS workspace."""
        
        self.path_GAMS_workspace = os.path.join(self.path_output_of_instance, "gams_workspaces", name_gams_workspace)
        self.make_empty_dir(self.path_GAMS_workspace) 
        
        return self.path_GAMS_workspace
    
    
    def clean_gams_workspace_folder(self):
        """Delete all log files in the GAMS workspace."""
        
        for file_old in os.listdir(self.path_GAMS_workspace):
            path_file_old = os.path.join(self.path_GAMS_workspace, file_old)
            if os.path.isfile(path_file_old):
                if path_file_old.endswith(".lst") or path_file_old.endswith(".gms") or path_file_old.endswith(".gdx"):
                    os.remove(path_file_old)
          
          
    def write_solution(self, solution): 
        """Writes the calculated solution into a text file."""
    
        variables = self.instance_data.variables
        
        try:
            with open(self.path_solution_file, 'w') as solution_file:
                
                # Write values of all variables
                for var in variables:
                    value = solution.out_db.get_variable("VAR").find_record(var).level
                    solution_file.write(var + "\t" + str(value) + "\n")
                
                solution_file.close() 
        
        except EnvironmentError:
            print("Could not open solution file for writing.")
            sys.exit() 
            
        
    def write_line(self, file, line):
        """Writes the given line into console and the given file."""
        
        file.write(line + "\n")
        print(line)        
        
        
    def write_data_to_file(self, path, file_name, data):
        """Writes the data into a file."""
        
        path_file = os.path.join(path, file_name + ".txt")
        file = open(path_file, 'w')
        file.write(data)
        file.close()  
                

    def make_empty_dir(self, path_dir):
        """Creates a new directory if it does not already exist. Otherwise, all files in the existing directory will be deleted."""
    
        # Create directory    
        if not os.path.exists(path_dir):
            os.makedirs(path_dir)
        # Delete all files and directories
        else:
            for file_old in os.listdir(path_dir):
                path_file_old = os.path.join(path_dir, file_old)
                if os.path.isfile(path_file_old):
                    os.remove(path_file_old)
                elif os.path.isdir(path_file_old): 
                    shutil.rmtree(path_file_old)        
        
        
