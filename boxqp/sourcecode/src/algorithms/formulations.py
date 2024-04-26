'''
Created on Jun 17, 2020

@author: Sascha Kuhnke
'''
from gams.workspace import GamsExceptionExecution
from math import ceil
import random

from algorithms.gams_api import EnvironmentGAMSVertexCover, EnvironmentGAMSOptimizationProblem
from data.data import AlgorithmData
from data.graph import Graph
from misc.misc import get_start_time, get_time_passed


# Constants
ONE = 1.0
ZERO = 0.0
INFINITY = float("inf")

# Algorithm data
ALL = AlgorithmData.ALL
RANDOM = AlgorithmData.RANDOM 
HIGHEST_DEGREE = AlgorithmData.HIGHEST_DEGREE
RELAXATION_VERTEX_COVER = AlgorithmData.RELAXATION_VERTEX_COVER


class OptimizationProblem():
    """Base class for optimization problem formulations."""
    
    def __init__(self, data, output_writer, name_gams_workspace, gams_file, model_name, model_type):
        
        self.instance_data = data.instance_data
        self.algorithm_data = data.algorithm_data
        self.output_writer = output_writer

        # Set up GAMS environment
        self.gams_environment = EnvironmentGAMSOptimizationProblem(self, data, output_writer, name_gams_workspace, gams_file, model_name, model_type)
        

    def solve(self, time_limit, log_file_suffix=""):
        """Solves the problem."""
    
        gams_workspace = self.gams_environment.gams_workspace
        checkpoint = self.gams_environment.checkpoint
        option_solver = self.gams_environment.option_solver
        model_name = self.gams_environment.model_name
        
        disc_data = self.gams_environment.disc_data
        fixed_variables = self.gams_environment.fixed_variables
        starting_point = self.gams_environment.starting_point
        options = self.gams_environment.get_options(time_limit)
        
        job = gams_workspace.add_job_from_string(disc_data + fixed_variables + starting_point + options, checkpoint)
        log_file = self.output_writer.open_log_file(model_name, log_file_suffix)
               
        time_start = get_start_time()
        
        try: 
            job.run(option_solver, output=log_file)
        except GamsExceptionExecution:
            pass
            
        time_required = get_time_passed(time_start)
        
        self.output_writer.close_log_file(log_file)
        self.gams_environment.job = job
        self.output_writer.write_summary(self.gams_environment, time_required)
        
        
    def initialize_fixed_variables(self):
        """Initializes the fixed variables heading."""
        
        self.gams_environment.fixed_variables = "*----------------------\n"
        self.gams_environment.fixed_variables += "* Fixed variables\n"
        self.gams_environment.fixed_variables += "*----------------------\n\n"
        
        
    def finalize_fixed_variables(self):
        """Finalizes the fixed variables data."""
        
        self.gams_environment.fixed_variables += "\n\n"        
        
        
    def set_fixed_variable(self, gams_variable, args, value):
        """Writes a line to the fixed variables data."""
        
        self.gams_environment.fixed_variables += self.gams_environment.set_gams_parameter(gams_variable, args, value)    
        
            
    def initialize_starting_point(self):
        """Initializes the starting point data heading."""
        
        self.gams_environment.starting_point = "*----------------------\n"
        self.gams_environment.starting_point += "* Starting point\n"
        self.gams_environment.starting_point += "*----------------------\n\n"    
        
        
    def set_starting_point_value(self, gams_parameter, args, value):
        """Writes a line to the starting point data."""
        
        self.gams_environment.starting_point += self.gams_environment.set_gams_parameter(gams_parameter, args, value)                 
        
        
    def write_starting_point_to_file(self):
        """Writes the starting point data into a file."""
        
        self.output_writer.write_starting_point(self.gams_environment.starting_point, self.algorithm_data.iteration)
        self.gams_environment.starting_point += "\n\n"   
        

class DiscretizedMIP(OptimizationProblem):
    """Discretized MIP formulation of the problem."""
    
    def __init__(self, data, output_writer):
        
        name_gams_workspace = "gams_workspace_disc"
        gams_file = "discretized_mip.gms"
        model_name = "DISCRETIZED_MIP"
        model_type = "MIP"   
        
        self.check_bounds_of_quadratic_variables(data, output_writer)
        self.determine_discretized_variables(data, output_writer)        
        
        super().__init__(data, output_writer, name_gams_workspace, gams_file, model_name, model_type)


    def solve(self, time_limit, log_file_suffix=""):
        """Solves the discretized problem."""
    
        super().solve(time_limit, log_file_suffix)
        
        if self.gams_environment.job_is_solved():
            self.discretization_solved = True
            self.objective_value_iteration = self.gams_environment.get_objective_value()
            self.solution_iteration = self.gams_environment.job
        else:
            self.discretization_solved = False


    def check_bounds_of_quadratic_variables(self, data, output_writer):
        """Checks if lower and upper bounds of discretized variables are finite."""
        
        lower_bounds = data.instance_data.lower_bounds
        upper_bounds = data.instance_data.upper_bounds        
        quadratic_variables = data.instance_data.quadratic_variables
        
        for var in quadratic_variables:
            if lower_bounds[var] == -INFINITY:
                output_writer.write_error_message("Infinite lower bound for " + var, data.instance_data, data.algorithm_data)
            elif upper_bounds[var] == INFINITY:
                output_writer.write_error_message("Infinite upper bound for " + var, data.instance_data, data.algorithm_data)
                 
         
    def determine_discretized_variables(self, data, output_writer):
        """Determines the variables that are discretized."""

        quadratic_variables = data.instance_data.quadratic_variables
        squared_variables = data.instance_data.squared_variables
        quadratic_non_squared_variables = data.instance_data.quadratic_non_squared_variables
        bilinear_terms = data.instance_data.bilinear_terms
        disc_variable_selection = data.algorithm_data.disc_variable_selection
        
        disc_variables = []
        
        time_start = get_start_time()
        
        # Discretize all quadratic variables
        if disc_variable_selection == ALL:
            for var in quadratic_variables:
                disc_variables.append(var)
        
        # Remove nodes randomly to determine vertex cover    
        elif disc_variable_selection == RANDOM:
            # Create graph
            graph = Graph(bilinear_terms)

            # Remove quadratic diagonal variables and its neighbors
            for var in squared_variables:
                graph.remove(var)
                disc_variables.append(var)
                
            while not graph.is_empty():
                # Remove randomly all nodes
                var = graph.get_random_node()
                degree = graph.get_degree(var)
                graph.remove(var)
                if degree > 0:
                    disc_variables.append(var)
                
        # Remove nodes with highest degree to determine vertex cover    
        elif disc_variable_selection == HIGHEST_DEGREE:
            # Create graph
            graph = Graph(bilinear_terms)

            # Remove quadratic diagonal variables
            for var in squared_variables:
                disc_variables.append(var)
                graph.remove(var)
                
            while not graph.is_empty():
                # Determine highest degree
                highest_degree = -1
                var_highest_degree = None
                
                for var in graph.get_nodes():
                    if graph.get_degree(var) > highest_degree:
                        var_highest_degree = var
                        highest_degree = graph.get_degree(var)
                         
                # Remove node with highest degree
                if highest_degree > 0:
                    disc_variables.append(var_highest_degree)  
                graph.remove(var_highest_degree)
                    
        # Determine vertex cover by solving relaxation and rounding afterwards    
        elif disc_variable_selection == RELAXATION_VERTEX_COVER: 
            
            if quadratic_non_squared_variables:
                
                # Set up GAMS environment
                name_gams_workspace = "gams_workspace_vertex_cover"
                gams_file = "relaxation_vertex_cover.gms"
                model_name = "RELAXATION_VERTEX_COVER"  
                model_type = "LP"          
                gams_environment = EnvironmentGAMSVertexCover(data, output_writer, name_gams_workspace, gams_file, model_name, model_type)
                
                # Solve vertex cover relaxation
                gams_workspace = gams_environment.gams_workspace
                checkpoint = gams_environment.checkpoint
                option_solver = gams_environment.option_solver
                 
                fixed_variables = gams_environment.fixed_variables
                options = gams_environment.get_options(60)
                
                job = gams_workspace.add_job_from_string(fixed_variables + options, checkpoint)
                log_file = output_writer.open_log_file(model_name, "")
                        
                try: 
                    job.run(option_solver, output=log_file)
                except GamsExceptionExecution:
                    pass
                     
                output_writer.close_log_file(log_file)
                gams_environment.job = job  
                
                # Discretize all nonzero variables in the vertex cover
                for var in quadratic_non_squared_variables:
                    if job.out_db.get_variable("VAR").find_record(var).level >= 0.5:
                        disc_variables.append(var)
                    
            # Discretize all quadratic diagonal variables
            for var in squared_variables:
                disc_variables.append(var)                     
            
            
        data.algorithm_data.disc_variables = disc_variables
        data.algorithm_data.time_disc_variable_selection = get_time_passed(time_start)           
        
        
    def initialize_discretization(self):
        """Sets the initial discretization values for the first iteration."""
        
        self.initialize_discretization_data()
        self.initialize_discretization_values()
        self.write_discretization_to_file()   


    def adapt_discretization(self):
        """Adapts the discretization values based on the previous solution."""
        
        self.initialize_discretization_data()
        self.initialize_starting_point()
        self.adapt_discretization_values()
        self.write_discretization_to_file()
        self.write_starting_point_to_file()        
         
    
    def initialize_discretization_values(self):
        """Initializes the discretization values of the discretized MIP."""
        
        lower_bounds = self.instance_data.lower_bounds
        upper_bounds = self.instance_data.upper_bounds
        disc_variables = self.algorithm_data.disc_variables
        disc_size = self.algorithm_data.disc_size
        disc_indices = self.algorithm_data.disc_indices

        disc_values = {}  
        disc_length = {} 
        disc_step_size = {}  
        chi_mip_start = {}
        
        # Initialize discretization values
        for var in disc_variables:
            
            disc_length[var] = upper_bounds[var] - lower_bounds[var]
            disc_step_size[var] = disc_length[var] / (disc_size - 1)
            for n in disc_indices:
                disc_values[(var, n)] = lower_bounds[var] + int(n) * disc_step_size[var]
                self.set_discretization_value("VALUE_DISC", (var, n), disc_values[(var, n)])
    
        self.algorithm_data.disc_values = disc_values
        self.algorithm_data.disc_length = disc_length
        self.algorithm_data.disc_step_size = disc_step_size 
        self.algorithm_data.chi_mip_start = chi_mip_start   


    def adapt_discretization_values(self):  
        """Adapts the discretization values of the discretized MIP based on the previous solution."""
        
        previous_solution = self.gams_environment.job
        lower_bounds = self.instance_data.lower_bounds
        upper_bounds = self.instance_data.upper_bounds
        disc_variables = self.algorithm_data.disc_variables
        disc_size = self.algorithm_data.disc_size
        disc_indices = self.algorithm_data.disc_indices
        feasibility_tolerance = self.algorithm_data.feasibility_tolerance
        integer_tolerance = self.algorithm_data.integer_tolerance
        disc_values = self.algorithm_data.disc_values
        disc_length = self.algorithm_data.disc_length
        disc_step_size = self.algorithm_data.disc_step_size
        chi_mip_start = self.algorithm_data.chi_mip_start

        for var in disc_variables:
            chi_selected = -1
            disc_value_selected = ZERO
            
            for n in disc_indices:
                chi_curr = previous_solution.out_db.get_variable("CHI").find_record((var, n)).level
                if chi_curr >= ONE - integer_tolerance:
                    chi_selected = int(n)
                    disc_value_selected = disc_values[(var, n)]
            
            # An interior point is selected        
            if (chi_selected > 0) and (chi_selected < disc_size - 1):
                
                # Reduce length of discretization
                disc_length[var] = disc_length[var] / 2.0     
                disc_step_size[var] = disc_length[var] / (disc_size - 1)
                
                # Align new discretization with the previous one
                chi_selected_new = ceil(disc_size / 2.0) - 1
                disc_value_min = disc_value_selected - disc_step_size[var] * chi_selected_new
                disc_value_max = disc_value_min + disc_length[var]
                
                # Shift discretization to the left boundary
                while (disc_value_min + feasibility_tolerance < lower_bounds[var]):
                    chi_selected_new -= 1
                    disc_value_min = disc_value_selected - disc_step_size[var] * chi_selected_new
                    disc_value_max = disc_value_min + disc_length[var]
                    
                # Shift discretization to the right boundary
                while (disc_value_max - feasibility_tolerance > upper_bounds[var]):
                    chi_selected_new += 1
                    disc_value_min = disc_value_selected - disc_step_size[var] * chi_selected_new
                    disc_value_max = disc_value_min + disc_length[var]
                
            # The first point is selected
            elif chi_selected == 0:
                
                # The selected point is on the left boundary
                if disc_value_selected <= lower_bounds[var] + feasibility_tolerance: 
                    
                    # Reduce length of discretization
                    disc_length[var] = disc_length[var] / 2.0                        
                    disc_step_size[var] = disc_length[var] / (disc_size - 1)

                    # Align new discretization with the previous one
                    chi_selected_new = 0
                    disc_value_min = lower_bounds[var]
                
                # The selected point is not on the left boundary   
                else:
                    
                    # Shift discretization to the left and align new discretization with the previous one
                    chi_selected_new = ceil(disc_size / 2.0) - 1
                    disc_value_min = disc_value_selected - disc_step_size[var] * chi_selected_new
                    
                    # Shift discretization to the left boundary
                    while (disc_value_min + feasibility_tolerance < lower_bounds[var]):
                        chi_selected_new -= 1
                        disc_value_min = disc_value_selected - disc_step_size[var] * chi_selected_new

            # The last point is selected    
            elif chi_selected == disc_size - 1:
                
                # The selected point is on the right boundary
                if disc_value_selected >= upper_bounds[var] - feasibility_tolerance: 
                    
                    # Reduce length of discretization
                    disc_length[var] = disc_length[var] / 2.0
                    disc_step_size[var] = disc_length[var] / (disc_size - 1)                           

                    # Align new discretization with the previous one
                    chi_selected_new = disc_size - 1
                    disc_value_min = upper_bounds[var] - disc_step_size[var] * chi_selected_new
                                               
                # The selected point is not on the right boundary   
                else:
                        
                    # Shift discretization to the right and align new discretization at the previous one
                    chi_selected_new = ceil(disc_size / 2.0) - 1
                    disc_value_min = disc_value_selected - disc_step_size[var] * chi_selected_new
                    disc_value_max = disc_value_min + disc_length[var]
                
                    # Shift discretization to the right boundary
                    while (disc_value_max - feasibility_tolerance > upper_bounds[var]):
                        chi_selected_new += 1
                        disc_value_min = disc_value_selected - disc_step_size[var] * chi_selected_new
                        disc_value_max = disc_value_min + disc_length[var]
            
            
            # Set new discretization values and corresponding MIP start    
            for n in disc_indices:
                disc_values[(var, n)] = disc_value_min + int(n) * disc_step_size[var]
                
                if int(n) == chi_selected_new:
                    chi_mip_start[(var, n)] = ONE
                else:
                    chi_mip_start[(var, n)] = ZERO
         
        # Update discretization values and corresponding MIP start                    
        for var in disc_variables:   
            for n in disc_indices:
                self.set_discretization_value("VALUE_DISC", (var, n), disc_values[(var, n)])
                self.set_starting_point_value("CHI.L", (var, n), chi_mip_start[(var, n)])
                

    def initialize_discretization_data(self):
        """Initializes the discretization data heading."""
        
        self.gams_environment.disc_data = "*----------------------\n"
        self.gams_environment.disc_data += "* Discretization data\n"
        self.gams_environment.disc_data += "*----------------------\n\n"
        
        
    def set_discretization_value(self, gams_parameter, args, value):
        """Writes a line to the discretization data."""
        
        self.gams_environment.disc_data += self.gams_environment.set_gams_parameter(gams_parameter, args, value)
        
        
    def write_discretization_to_file(self):
        """Writes the discretization data into a file."""
        
        self.output_writer.write_discretization(self.gams_environment.disc_data, self.algorithm_data.iteration)
        self.gams_environment.disc_data += "\n\n"
        
        
class OriginalQCP(OptimizationProblem):
    """Original QCP formulation of the problem."""
    
    def __init__(self, data, output_writer):
        
        name_gams_workspace = "gams_workspace_qcp"
        gams_file = "qcp.gms"
        model_name = "QCP"
        model_type = "QCP"       

        super().__init__(data, output_writer, name_gams_workspace, gams_file, model_name, model_type)
                

    """Sets the standard starting point with all values at zero."""
    def set_starting_point_zero(self, ):
        
        variables = self.instance_data.variables

        self.initialize_starting_point()
        
        # Set levels for variables
        for var in variables:
            self.set_starting_point_value("VAR.L", var, ZERO)
        
        self.write_starting_point_to_file() 
        
                
    """Sets a random starting point with a given random seed."""
    def set_random_starting_point(self, seed):
        
        variables = self.instance_data.variables
        lower_bounds = self.instance_data.lower_bounds
        upper_bounds = self.instance_data.upper_bounds        

        self.initialize_starting_point()
        
        # Set random seed
        random.seed(seed)
        
        # Set levels for variables
        for var in variables:
            self.set_starting_point_value("VAR.L", var, lower_bounds[var] + (upper_bounds[var] - lower_bounds[var]) * random.random())
        
        self.write_starting_point_to_file()     
                        
        
class FeasibilityChecker(OptimizationProblem):
    """Checks the feasibility of the solution by fixing all variables in the original QCP formulation."""
    
    def __init__(self, data, output_writer, solution):
        
        name_gams_workspace = "gams_workspace_checker"    
        gams_file = "qcp.gms"
        model_name = "QCP_CHECKER"     
        model_type = "QCP"       
        
        data.algorithm_data.is_active_checker = True
        
        super().__init__(data, output_writer, name_gams_workspace, gams_file, model_name, model_type)
        
        self.fix_variables(solution)
        

    def fix_variables(self, solution):
        """Fixes all variables of the given solution."""
        
        self.initialize_fixed_variables()
        self.fix_variable_values(solution)
        self.finalize_fixed_variables()
        
        
    def fix_variable_values(self, solution):
        """Fixes the values of all variables to the ones of the given solution."""
        
        variables = self.instance_data.variables

        for var in variables:
            value = solution.out_db.get_variable("VAR").find_record(var).level
            self.set_fixed_variable("VAR.Fx", var, value)
            
            