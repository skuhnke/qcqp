'''
Created on Nov 26, 2020

@author: Sascha Kuhnke
'''
import os
import sys

from algorithms.algorithms import Algorithm
from algorithms.formulations import OptimizationProblem
from data.data import AlgorithmData, Data
from input_output.input_reader import InputReader
from input_output.output_writer import OutputWriter
from misc.misc import get_time_passed


# Constants
ONE = 1.0
ZERO = 0.0

# Algorithm data
QCP_SOLVER = AlgorithmData.QCP_SOLVER
ADAPTIVE = AlgorithmData.ADAPTIVE
HIGHEST_DEGREE = AlgorithmData.HIGHEST_DEGREE
BARON = AlgorithmData.BARON


class BoundTightener(Algorithm):
    """Tightens all bounds by minimizing or maximizing each variable over the constraints of the original problem."""

    def __init__(self, data, output_writer, write_tightened_instance=True):
        
        self.write_tightened_instance = write_tightened_instance
        super().__init__(data, output_writer)
        

    def initialize_optimization_problem(self):
        """Initializes the bound tightener."""
    
        self.bound_tightener = QCPTightenBounds(self.data, self.output_writer)
        self.gams_environment = self.bound_tightener.gams_environment
    

    def solve(self):
        """Solves the bound tightening with a global optimization solver."""    
        
        data = self.data
        instance_data = self.instance_data
        algorithm_data = self.algorithm_data
        output_writer = self.output_writer
        variables = instance_data.variables

        # Open the instance output file 
        path_output = os.path.join("output", "tightened_bounds")  
        if not os.path.exists(path_output):
            os.makedirs(path_output)  
        path_tightened_bounds_file = os.path.join(path_output, instance_data.name)
        self.output_writer_tighten_bounds = OutputWriterTightenBounds(data, path_tightened_bounds_file + ".lp")

        time_limit_tighten_bounds_minmax = data.algorithm_data.time_limit_tighten_bounds_minmax
        default_bound = data.algorithm_data.default_bound
        
        instance_data.lower_bounds_tightened = {}
        instance_data.upper_bounds_tightened = {}
        
        algorithm_data.num_bounds_tightened = 0 
        
            
        # Tighten bounds
        for var in variables:
            
            # Tighten lower bound
            self.bound_tightener.initialize_lower_bound_tightening(var)
            self.bound_tightener.solve(time_limit_tighten_bounds_minmax)
            
            lower_bound_tightened = self.gams_environment.get_dual_bound(16)
            if lower_bound_tightened != ZERO:
                lower_bound_tightened = -ONE * lower_bound_tightened            
            
            instance_data.lower_bounds_tightened[var] = lower_bound_tightened
            
            if instance_data.lower_bounds_tightened[var] > -1e+40:
                output_writer.write_line_to_summary_file("Tightened lower bound of " + var + " to " + str(instance_data.lower_bounds_tightened[var]))
                algorithm_data.num_bounds_tightened += 1
            else:
                instance_data.lower_bounds_tightened[var] = -ONE * default_bound
                
            # Tighten upper bound
            self.bound_tightener.initialize_upper_bound_tightening(var)
            self.bound_tightener.solve(time_limit_tighten_bounds_minmax)
            
            upper_bound_tightened = self.gams_environment.get_dual_bound(16)
            
            instance_data.upper_bounds_tightened[var] = upper_bound_tightened 
            
            if instance_data.upper_bounds_tightened[var] < 1e+40:
                output_writer.write_line_to_summary_file("Tightened upper bound of " + var + " to " + str(instance_data.upper_bounds_tightened[var]))
                algorithm_data.num_bounds_tightened += 1
            else:
                instance_data.upper_bounds_tightened[var] = default_bound
                                
            # Clean GAMS workspace to save memory    
            output_writer.clean_gams_workspace_folder()
        
        
        if self.write_tightened_instance:                
            self.output_writer_tighten_bounds.write_instance_tightened_bounds()   
        output_writer.write_line_to_summary_file("\nTightened " + str(algorithm_data.num_bounds_tightened) + " bounds.")
        
        
    def finish_algorithm(self):
        """Calculates the required time."""
        
        self.time_required = get_time_passed(self.time_start)
        
        self.output_writer.close_summary_file("-", "-", self.time_required)
        self.output_writer.add_results(self.data, "-", self.instance_data.num_variables, self.algorithm_data.num_bounds_tightened, self.time_required)   
    

class QCPTightenBounds(OptimizationProblem):
    """Minimize or maximize a variable over the constraints of the original problem to tighten the bounds."""
    
    def __init__(self, data, output_writer):
        
        name_gams_workspace = "GAMS_workspace_BoundTightener"
        gams_file = "qcp_tighten_bounds.gms"
        model_name = "QCP_TIGHTEN_BOUNDS"
        model_type = "QCP"       

        super().__init__(data, output_writer, name_gams_workspace, gams_file, model_name, model_type)    
        
        
    def initialize_lower_bound_tightening(self, var):
        """Set variable coefficient in the objective function to tighten lower bound."""
        
        self.initialize_fixed_variables()
        self.set_fixed_variable("COEFF_OBJ_TIGHTEN_BOUNDS", var, -ONE)
        self.finalize_fixed_variables()
        
        
    def initialize_upper_bound_tightening(self, var):
        """Set variable coefficient in the objective function to tighten upper bound."""
        
        self.initialize_fixed_variables()
        self.set_fixed_variable("COEFF_OBJ_TIGHTEN_BOUNDS", var, ONE)        


class OutputWriterTightenBounds(OutputWriter):
    """Writes the tightened instance into a new instance file."""

    def __init__(self, data, path_tightened_bounds_file):
        
        self.path_tightened_bounds_file = path_tightened_bounds_file
        super().__init__(data)
        

    def write_instance_tightened_bounds(self): 
        """Writes a new instance file with the tightened bounds."""
    
        variables = self.instance_data.variables
        lower_bounds_tightened = self.instance_data.lower_bounds_tightened
        upper_bounds_tightened = self.instance_data.upper_bounds_tightened
        
        path_of_instance = os.path.join("input", "instances", self.instance_data.name + ".lp")
        
        # Open input file
        try:
            with open(path_of_instance, 'r') as input_file:
                lines = input_file.readlines()
                input_file.close()
        except EnvironmentError:
            print("Cannot not open instance file.")
            sys.exit()
            
        # Navigate to end of constraint section            
        num_line = 0    
        while lines[num_line].strip() not in ["Bounds", "End"]:
            num_line += 1
        
        # Open output file
        try:
            with open(self.path_tightened_bounds_file, 'w') as tightened_bounds_file:
                
                # Write tightened values of all standard lower and upper bounds
                tightened_bounds_file.writelines(lines[:num_line - 1])
                tightened_bounds_file.write("\nBounds\n")
                for var in variables:
                    bounds = str(lower_bounds_tightened[var]) + " <= " + var + " <= " + str(upper_bounds_tightened[var])
                    tightened_bounds_file.write(" " + str(bounds) + "\n")
                
                tightened_bounds_file.write("\nEnd")
                tightened_bounds_file.close() 
        
        except EnvironmentError:
            print("Could not open tightened bounds file for writing.")
            sys.exit()             
    
    
def get_data(name_of_instance, time_limit_tighten_bounds_minmax, default_bound):
    """Returns the instance data and output writer."""
    
    algorithm = QCP_SOLVER
    disc_type = ADAPTIVE
    disc_variable_selection = HIGHEST_DEGREE
    qcp_solver = BARON
    disc_size = 0
    
    stderr = sys.stderr
        
    # Time limits and optimality gap
    time_limit_discretization = 120.0
    time_limit_iteration = 60.0
    time_limit_qcp = 30.0
    gap = 0.000001
    
    # Tolerances
    feasibility_tolerance = pow(10, -6)
    integer_tolerance = pow(10, -5)
    feasibility_tolerance_checker = pow(10, -4)
    
    # Local solver options
    tries_local_solver = 10

    # Initialize data
    data = Data(name_of_instance, algorithm, disc_type, disc_variable_selection, qcp_solver, tries_local_solver, disc_size, 
                time_limit_discretization, time_limit_iteration, time_limit_qcp, gap, feasibility_tolerance, integer_tolerance, 
                feasibility_tolerance_checker, stderr)    
    
    # Read input
    input_reader = InputReader(data)
    input_reader.read_input()
    
    # Initialize output
    output_writer = OutputWriter(data)
    output_writer.initialize_output()
    
    data.algorithm_data.time_limit_tighten_bounds_minmax = time_limit_tighten_bounds_minmax
    data.algorithm_data.default_bound = default_bound
    
    return data, output_writer
        
        
if __name__ == '__main__':
    
    name_of_instance = sys.argv[1]
    time_limit_tighten_bounds_minmax = 60.0
    default_bound = float(pow(10, 9))

    data, output_writer = get_data(name_of_instance, time_limit_tighten_bounds_minmax, default_bound)
    
    BoundTightener(data, output_writer).start()
    
    