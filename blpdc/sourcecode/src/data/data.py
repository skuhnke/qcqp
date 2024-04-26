'''
Created on Jun 9, 2020

@author: Sascha Kuhnke
'''
import sys

from misc.exceptions import AlgorithmDataException


class Data():
    """Basic class for data containing the instance data and the algorithm data."""
    
    def __init__(self, name_of_instance, algorithm, disc_type, disc_variable_selection, qcp_solver, tries_local_solver, disc_size, 
                time_limit_discretization, time_limit_iteration, time_limit_qcp, gap, feasibility_tolerance, integer_tolerance, 
                feasibility_tolerance_checker, stderr):
        
        self.instance_data = InstanceData(name_of_instance, stderr)
        self.algorithm_data = AlgorithmData(algorithm, disc_type, disc_variable_selection, qcp_solver, tries_local_solver, disc_size, 
                    time_limit_discretization, time_limit_iteration, time_limit_qcp, gap, feasibility_tolerance, integer_tolerance, 
                    feasibility_tolerance_checker)
    

class InstanceData():
    """Class for all instance related data."""
    
    # Objective sense
    MIN = "minimize"
    MAX = "maximize"    
    
    def __init__(self, name_of_instance, stderr):
        
        self.name = name_of_instance
        
        self.num_variables = 0
        self.num_constraints = 0
        self.num_constraints_eq = 0
        self.num_constraints_ge = 0
        self.num_constraints_le = 0
        
        self.objective_sense = None
        
        self.variables = []
        self.constraints = []
        self.constraints_eq = []
        self.constraints_ge = []
        self.constraints_le = []
        
        self.coefficients_quad = {}
        self.coefficients = {}
        self.rhs = {}
        self.coefficients_quad_objective = {}
        self.coefficients_objective = {}
        self.lower_bounds = {}
        self.upper_bounds = {}
        
        self.quadratic_variables = []
        self.squared_variables = []
        self.quadratic_non_squared_variables = []
        self.bilinear_terms = []
        
        self.stderr = stderr
        
        
class AlgorithmData(object):
    """Class for all algorithm related data."""

    # Algorithms
    DISCRETIZATION = "disc"
    QCP_SOLVER = "qcp-solver"
    
    # Types of discretization
    ADAPTIVE = "adaptive"
    NON_ITERATIVE = "non-iterative"
    
    # Discretized variables
    ALL = "all"
    RANDOM = "random"
    HIGHEST_DEGREE = "highest-degree"
    RELAXATION_VERTEX_COVER = "relaxation-vertex-cover" 
    
    # QCP solvers
    BARON = "baron"
    SCIP = "scip"
    GUROBI = "gurobi"    
    IPOPT = "ipopt"
    SNOPT = "snopt"
    MINOS = "minos"
    
    def __init__(self, algorithm, disc_type, disc_variable_selection, qcp_solver, tries_local_solver, disc_size, time_limit_discretization, 
                 time_limit_iteration, time_limit_qcp, gap, feasibility_tolerance, integer_tolerance, feasibility_tolerance_checker):
        
        self.algorithm = algorithm
        self.disc_type = disc_type
        self.disc_variable_selection = disc_variable_selection
        self.qcp_solver = qcp_solver
        self.tries_local_solver = tries_local_solver
        self.disc_size = disc_size
        self.time_limit_discretization = time_limit_discretization
        self.time_limit_iteration = time_limit_iteration
        self.time_limit_qcp = time_limit_qcp
        self.gap = gap
        self.feasibility_tolerance = feasibility_tolerance
        self.integer_tolerance = integer_tolerance
        self.feasibility_tolerance_checker = feasibility_tolerance_checker
        self.is_active_checker = False 
        self.iteration = 0

        # Adapt parameters in discretization algorithms 
        if algorithm == AlgorithmData.DISCRETIZATION:
            
            # Adapt time limit and maximum number of iterations for non-iterative algorithms.
            if disc_type == AlgorithmData.NON_ITERATIVE:
                self.time_limit_iteration = time_limit_discretization
                self.max_iterations = 1
                
        # Check if data is valid        
        self.check_algorithm_data()
            

    def check_algorithm_data(self):
        """Checks if all algorithm parameters are valid."""
        
        if self.algorithm not in [AlgorithmData.DISCRETIZATION, AlgorithmData.QCP_SOLVER]:
            self.raise_algorithm_data_exception("Please choose a valid algorithm.") 
        
        if self.algorithm == AlgorithmData.DISCRETIZATION:
            if self.disc_type not in [AlgorithmData.ADAPTIVE, AlgorithmData.NON_ITERATIVE]:
                self.raise_algorithm_data_exception("Please choose a valid discretization type.")

            if (self.disc_variable_selection not in [AlgorithmData.ALL, AlgorithmData.RANDOM, 
                                                            AlgorithmData.HIGHEST_DEGREE, AlgorithmData.RELAXATION_VERTEX_COVER]):
                self.raise_algorithm_data_exception("Please choose a valid method for the selection of discretized variables.")
                
            if not str(self.disc_size).isdigit():
                self.raise_algorithm_data_exception("Please choose a positive integer as discretization size.")
            else:
                self.disc_size = int(self.disc_size)            
            
            if self.disc_size < 2:
                self.raise_algorithm_data_exception("Size of the discretization has to be greater or equal to 2.")                   

        elif self.algorithm == AlgorithmData.QCP_SOLVER: 
            if self.qcp_solver not in [AlgorithmData.BARON, AlgorithmData.SCIP, AlgorithmData.GUROBI, AlgorithmData.IPOPT, 
                                                                                        AlgorithmData.SNOPT, AlgorithmData.MINOS]:
                self.raise_algorithm_data_exception("Please choose a valid QCP solver.")
            
        if self.time_limit_discretization <= 0:
            self.raise_algorithm_data_exception("Time limit for discretization has to be positive.")
            
        if self.time_limit_iteration < 0:
            self.raise_algorithm_data_exception("Time limit for one iteration has to be non-negative.")
            
        if self.time_limit_qcp <= 0:
            self.raise_algorithm_data_exception("Time limit for QCP has to be positive.")            
            
        if self.time_limit_iteration > self.time_limit_discretization:
            self.raise_algorithm_data_exception("Time limit for one iteration cannot be more than time limit of discretization.")
        
        if self.gap < 0:
            self.raise_algorithm_data_exception("Gap has to be greater or equal to 0.")
        
        if self.feasibility_tolerance < 0:
            self.raise_algorithm_data_exception("Feasiblity tolerance has to be greater or equal to 0.")
        
        if self.integer_tolerance < 0:
            self.raise_algorithm_data_exception("Integrality tolerance has to be greater or equal to 0.")
        
        if self.feasibility_tolerance_checker < 0:
            self.raise_algorithm_data_exception("Solution checker feasibility tolerance has to be greater or equal to 0.")
        
        
    def raise_algorithm_data_exception(self, message):
        """Raises an algorithm data exception with information about the error."""
        
        try:
            raise AlgorithmDataException(message)
        except AlgorithmDataException as exception:
            print(exception)
            sys.exit()  
              
        