'''
Created on Feb 12, 2019

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
PQ_FORMULATION = AlgorithmData.PQ_FORMULATION
TP_FORMULATION = AlgorithmData.TP_FORMULATION
IPOPT = AlgorithmData.IPOPT
SNOPT = AlgorithmData.SNOPT
MINOS = AlgorithmData.MINOS


class OutputWriter(object):
    """Class to write all output data."""

    def __init__(self, data):
        
        self.instance_data = data.instance_data
        self.algorithm_data = data.algorithm_data


    def initialize_output(self):
        """Initializes all necessary paths and folders for the output."""
        
        self.create_output_folder_for_instance()
        self.set_path_solution_and_results_file()
        self.open_summary_file()
        self.create_log_folders()  
        
        if self.algorithm_data.perform_preprocessing:
            self.create_preprocessing_output_folder()
        
        if self.algorithm_data.algorithm == DISCRETIZATION:
            self.create_discretization_output_folder()

        if (self.algorithm_data.algorithm == DISCRETIZATION or 
                    (self.algorithm_data.algorithm == QCP_SOLVER and self.algorithm_data.qcp_solver in [IPOPT, SNOPT, MINOS])):
            self.create_starting_points_output_folder()
        
    
    def create_output_folder_for_instance(self):
        """Create empty directory for this instance."""
            
        name_of_instance = self.instance_data.name
        algorithm_data = self.algorithm_data
            
        if algorithm_data.algorithm == DISCRETIZATION:
            self.path_output = os.path.join("output", algorithm_data.formulation + "_" + algorithm_data.algorithm + "_" + 
                                            algorithm_data.disc_type + "_" + algorithm_data.disc_variant + "_" + str(algorithm_data.disc_size)) 
        elif algorithm_data.algorithm == QCP_SOLVER:
            self.path_output = os.path.join("output", algorithm_data.formulation + "_" + algorithm_data.algorithm + "_" + 
                                            str(algorithm_data.qcp_solver))
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
        self.path_preprocessing_results_file = os.path.join(self.path_output_of_instance, "results_preprocessing.ods")   
        

    def open_summary_file(self):
        """Opens and initializes the summary file."""
        
        name_of_instance = self.instance_data.name
        algorithm_data = self.algorithm_data        
        
        self.path_summary_file = os.path.join(self.path_output_of_instance, name_of_instance + ".sum")
        self.summary_file = open(self.path_summary_file, 'w')
        
        self.write_line(self.summary_file, "------------------------------------")
        self.write_line(self.summary_file, "------------------------------------")
        self.write_line(self.summary_file, "Instance:\t\t" + name_of_instance)
        self.write_line(self.summary_file, "Formulation:\t\t" + algorithm_data.formulation)
        self.write_line(self.summary_file, "Algorithm:\t\t" + algorithm_data.algorithm)
        if algorithm_data.algorithm == DISCRETIZATION:
            self.write_line(self.summary_file, "Disc type:\t\t" + algorithm_data.disc_type)
            self.write_line(self.summary_file, "Disc variant:\t\t" + algorithm_data.disc_variant)
            self.write_line(self.summary_file, "Disc size:\t\t" + str(algorithm_data.disc_size))
            self.write_line(self.summary_file, "Time limit:\t\t" + str(algorithm_data.time_limit_discretization))
            self.write_line(self.summary_file, "Time limit iteration:\t" + str(algorithm_data.time_limit_iteration))
        elif algorithm_data.algorithm == QCP_SOLVER:
            self.write_line(self.summary_file, "QCP solver:\t\t" + algorithm_data.qcp_solver)
            self.write_line(self.summary_file, "Time limit:\t\t" + str(algorithm_data.time_limit_qcp))        
        self.write_line(self.summary_file, "Optimality gap:\t\t" + str(algorithm_data.gap))
        self.write_line(self.summary_file, "------------------------------------\n")
        
    
    def write_summary_preprocessing(self, time_required, n_ws_deleted, n_pl_deleted, n_wd_deleted, n_constr_deleted):
        """Writes a summary after performing preprocessing."""
        
        self.write_line(self.summary_file, "------------------------------------")
        self.write_line(self.summary_file, "PREPROCESSING")
        self.write_line(self.summary_file, "------------------------------------")
        self.write_line(self.summary_file, "Inputs del:\t " + str(n_ws_deleted))
        self.write_line(self.summary_file, "Pools del:\t " + str(n_pl_deleted))
        self.write_line(self.summary_file, "Outputs del:\t " + str(n_wd_deleted))
        self.write_line(self.summary_file, "Constr del:\t " + str(n_constr_deleted))
        self.write_line(self.summary_file, "Time:\t\t " + str(time_required) + "\n")     
        
      
    def write_line_to_summary_file(self, line):
        """Writes a line to the summary file."""
        
        self.write_line(self.summary_file, line)
              
        
    def write_summary(self, gams_environment, time_required):
        """Writes a summary after solving an optimization problem."""
        
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
    
    
    def close_summary_file(self, dual_bound, objective_value, time_required):
        """Writes final objective value along with the dual bound and total running time before closing the summary file."""
    
        self.write_line(self.summary_file, "------------------------------------")
        self.write_line(self.summary_file, "Dual bound:\t " + str(dual_bound))
        self.write_line(self.summary_file, "Objective:\t " + str(objective_value))
        self.write_line(self.summary_file, "Total time:\t " + str(time_required))
        self.write_line(self.summary_file, "------------------------------------")
        print("\n\n")
        
        self.summary_file.close()  
        
        
    def add_preprocessing_results(self, data, n_water_sources, n_pools, n_water_demands, n_arcs, 
                                        n_spec_requirement_constraints, n_water_sources_deleted, n_pools_deleted, 
                                            n_water_demands_deleted, n_arcs_deleted, n_constraints_deleted):
        """Adds the current preprocessing to the result file."""
        
        instance_name = data.instance_data.name
        
        if os.path.isfile(self.path_preprocessing_results_file):
            results_file = open(self.path_preprocessing_results_file, 'r')
            results = results_file.readlines()
            results_file.close()
        else:
            results = []
            results.append("Instance" + "," + "Inputs" + "," + "Pools" + "," + "Outputs" + "," + "Arcs" + "," + "Spec Constr" + 
                    "," + "Inputs del" + "," + "Pools del" + "," + "Outputs del" + "," + "Arcs del" + "," + "Spec Constr del" + "\n")
        
        results_file = open(self.path_preprocessing_results_file, 'w')
        results.append(instance_name + "," + str(n_water_sources) + "," + str(n_pools) + "," + str(n_water_demands) + "," + 
                       str(n_arcs) + "," + str(n_spec_requirement_constraints) + "," + str(n_water_sources_deleted) + "," + 
                       str(n_pools_deleted) + "," + str(n_water_demands_deleted) + "," + str(n_arcs_deleted) + "," + 
                       str(n_constraints_deleted) + "\n")
    
        results_file.writelines(results)
        results_file.close()         
        
        
    def add_results(self, data, is_solved, dual_bound, objective_value, time_required):
        """Adds the current solution to the result file."""
        
        instance_data = data.instance_data
        algorithm_data = data.algorithm_data
        
        results_file = open(self.path_results_file, 'w')
        
        if algorithm_data.algorithm == DISCRETIZATION:
            results_file.write("Instance" + "," + "Formulation" + "," + "Algorithm" + "," + "Disc type" + "," + "Disc variant  " + "," + 
                                "Disc size" + "," + "Iterations" + "," + "Solved" + "," + "Objective" + "," + "Time" + "," + "CPU Time" + "\n")    
            results_file.write(instance_data.name + "," + algorithm_data.formulation + "," + 
                               algorithm_data.algorithm + "," + algorithm_data.disc_type + "," + algorithm_data.disc_variant + "," + 
                               str(algorithm_data.disc_size) + "," + str(algorithm_data.iteration) + "," + str(is_solved) + "," + 
                               str(objective_value) + "," + str(round(time_required)) + "\n")
        elif algorithm_data.algorithm == QCP_SOLVER:
            results_file.write("Instance" + "," + "Formulation" + "," + "Algorithm" + "," + "QCP solver" + "," + "Solved" + "," + 
                               "Dual bound" + "," + "Objective" + "," + "Time" + "," + "CPU Time" + "\n")    
            results_file.write(instance_data.name + "," + algorithm_data.formulation + "," + algorithm_data.algorithm + "," + 
                               algorithm_data.qcp_solver + "," + str(is_solved) + "," + str(dual_bound) + "," + 
                               str(objective_value) + "," + str(round(time_required)) + "\n")            
    
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
    
    
    def open_log_file_preprocessing(self, model_name, log_file_suffix):
        """Opens the log file of the current preprocessing."""
        
        if log_file_suffix != "":
            log_file_suffix = "_" + str(log_file_suffix)
        
        path_log_file = os.path.join(self.path_preprocessing, model_name.lower() + str(log_file_suffix) + ".log")
        log_file = open(path_log_file, 'w')
    
        return log_file      
    
    
    def close_log_file(self, log_file):
        """Closes the log file of the current iteration."""
        
        log_file.close()  


    def create_preprocessing_output_folder(self):
        """Creates the output folder for preprocessing."""
        
        folder_preprocessing = "preprocessing"
        self.path_preprocessing = os.path.join(self.path_output_of_instance, folder_preprocessing)
        self.make_empty_dir(self.path_preprocessing)        


    def create_discretization_output_folder(self):
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


    def write_solution(self, solution): 
        """Writes the calculated solution into a text file."""
    
        algorithm = self.algorithm_data.algorithm
        UN_IN = self.instance_data.units_in
        UN_OUT = self.instance_data.units_out
        WS = self.instance_data.water_sources
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        
        try:
            with open(self.path_solution_file, 'w') as solution_file:
                # pq-formulation
                if self.algorithm_data.formulation == PQ_FORMULATION:
                    for un_out in UN_OUT:
                        for wd in WD:
                            flow_curr = solution.out_db.get_variable("FL").find_record((un_out, wd)).level
                            if flow_curr > ZERO: 
                                solution_file.write(un_out + "\t" + wd + "\t" + str(flow_curr) + "\n")
                                
                    for ws in WS:
                        for pl in PL:
                            flow_curr = ZERO
                            for wd in WD:
                                fl_pr_curr = solution.out_db.get_variable("FL_PR").find_record((ws, pl, wd)).level
                                flow_curr += fl_pr_curr
                            if flow_curr > ZERO: 
                                solution_file.write(ws + "\t" + pl + "\t" + str(flow_curr) + "\n")
                 
                # tp-formulation                
                elif self.algorithm_data.formulation == TP_FORMULATION:
                    for ws in WS:
                        for un_in in UN_IN:
                            flow_curr = solution.out_db.get_variable("FL").find_record((ws, un_in)).level
                            if flow_curr > ZERO: 
                                solution_file.write(ws + "\t" + un_in + "\t" + str(flow_curr) + "\n")
                                
                    for pl in PL:
                        for wd in WD:
                            flow_curr = ZERO
                            if algorithm == QCP_SOLVER: 
                                for ws in WS:
                                    flow_curr += solution.out_db.get_variable("FL").find_record((ws, pl)).level
                                flow_curr *= solution.out_db.get_variable("PR").find_record((pl, wd)).level
                            else:
                                for ws in WS:
                                    flow_curr += solution.out_db.get_variable("FL_PR").find_record((ws, pl, wd)).level
                            if flow_curr > ZERO: 
                                solution_file.write(pl + "\t" + wd + "\t" + str(flow_curr) + "\n")
                                
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
