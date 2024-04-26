'''
Created on Feb 12, 2019

@author: Sascha Kuhnke
'''
import sys

from misc.exceptions import AlgorithmDataException


class Data():
    """Basic class for data containing the instance data and the algorithm data."""
    
    def __init__(self, name_of_instance, formulation, algorithm, disc_type, disc_variant, qcp_solver, tries_local_solver,
                time_limit_discretization, time_limit_iteration, time_limit_qcp, gap, disc_size, feasibility_tolerance,
                integer_tolerance, feasibility_tolerance_checker, perform_preprocessing, evaluate_preprocessing, stderr):
        
        self.instance_data = InstanceData(name_of_instance, stderr)
        self.algorithm_data = AlgorithmData(formulation, algorithm, disc_type, disc_variant, qcp_solver, tries_local_solver,
                time_limit_discretization, time_limit_iteration, time_limit_qcp, gap, disc_size, feasibility_tolerance,
                integer_tolerance, feasibility_tolerance_checker, perform_preprocessing, evaluate_preprocessing)

    
class InstanceData():
    """Class for all instance related data."""
    
    
    def __init__(self, name_of_instance, stderr):
        
        self.name = name_of_instance
        
        self.units = []
        self.units_out = []
        self.units_in = []
        self.water_sources = []
        self.pools = []
        self.water_demands = []
        self.contaminants = []
        self.fl_max_un = {}
        self.fl_max = {}
        self.cost = {}
        self.po_ws = {}
        self.po_min_wd = {}
        self.po_max_wd = {}
        self.cost_ws = {}
        self.revenue_wd = {}    
        self.pipe_exists = {}
        self.is_active_min = {}
        self.is_active_max = {}
        
        self.stderr = stderr
        
    
class AlgorithmData(object):
    """Class for all algorithm related data."""

    # Formulations
    PQ_FORMULATION = "pq"
    TP_FORMULATION = "tp"
    
    # Algorithms
    DISCRETIZATION = "disc"
    QCP_SOLVER = "qcp-solver"

    # Discretization types
    ADAPTIVE = "adaptive"
    NON_ITERATIVE = "non-iterative"
    
    # Discretization variants
    PROPORTION = "proportion"
    FLOW = "flow"
    POOL = "pool"
    
    # QCP solvers
    BARON = "baron"
    SCIP = "scip"
    GUROBI = "gurobi"
    IPOPT = "ipopt"
    SNOPT = "snopt"
    MINOS = "minos"    
    
    def __init__(self, formulation, algorithm, disc_type, disc_variant, qcp_solver, tries_local_solver,
                time_limit_discretization, time_limit_iteration, time_limit_qcp, gap, disc_size, feasibility_tolerance,
                integer_tolerance, feasibility_tolerance_checker, perform_preprocessing, evaluate_preprocessing):
        
        self.formulation = formulation
        self.algorithm = algorithm
        self.disc_type = disc_type
        self.disc_variant = disc_variant
        self.qcp_solver = qcp_solver
        self.tries_local_solver = tries_local_solver
        self.time_limit_discretization = time_limit_discretization
        self.time_limit_iteration = time_limit_iteration
        self.time_limit_qcp = time_limit_qcp
        self.gap = gap
        self.disc_size = disc_size
        self.feasibility_tolerance = feasibility_tolerance
        self.integer_tolerance = integer_tolerance
        self.feasibility_tolerance_checker = feasibility_tolerance_checker  
        self.perform_preprocessing = perform_preprocessing
        self.evaluate_preprocessing = evaluate_preprocessing
        self.is_active_checker = False
        self.iteration = 0

        # Adapt parameters in Discretization 
        if algorithm == AlgorithmData.DISCRETIZATION:
            
            # Adapt time limit and maximum number of iterations for non-iterative algorithms.
            if disc_type == AlgorithmData.NON_ITERATIVE:
                self.time_limit_iteration = time_limit_discretization
                self.max_iterations = 1       
                
        # Check if data is valid        
        self.check_algorithm_data()
            

    def check_algorithm_data(self):
        """Checks if all algorithm parameters are valid."""
        
        if self.formulation not in [AlgorithmData.PQ_FORMULATION, AlgorithmData.TP_FORMULATION]:
            self.raise_algorithm_data_exception("Please choose a valid formulation.")
            
        if self.algorithm not in [AlgorithmData.DISCRETIZATION, AlgorithmData.QCP_SOLVER]:
            self.raise_algorithm_data_exception("Please choose a valid algorithm.")
        
        if self.algorithm == AlgorithmData.DISCRETIZATION:
            if self.disc_type not in [AlgorithmData.ADAPTIVE, AlgorithmData.NON_ITERATIVE]:
                self.raise_algorithm_data_exception("Please choose a valid discretization type.")
            
            if self.disc_variant not in [AlgorithmData.PROPORTION, AlgorithmData.FLOW, AlgorithmData.POOL]:
                self.raise_algorithm_data_exception("Please choose a valid discretization variant.")            
            
            if not str(self.disc_size).isdigit():
                self.raise_algorithm_data_exception("Please choose a positive integer as discretization size.")
            else:
                self.disc_size = int(self.disc_size)
                
            if self.disc_size < 1:
                self.raise_algorithm_data_exception("Size of the discretization has to be greater or equal to 1.")
            
            if (self.disc_variant == AlgorithmData.PROPORTION) and (self.disc_size < 2):
                self.raise_algorithm_data_exception("Size of proportion or flow discretization has to be greater or equal to 2.")        
            
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
            self.raise_algorithm_data_exception("Solution checker tolerance has to be greater or equal to 0.")
        

    def raise_algorithm_data_exception(self, message):
        """Raises an algorithm data exception with information about the error."""
        
        try:
            raise AlgorithmDataException(message)
        except AlgorithmDataException as exception:
            print(exception)
            sys.exit()      
    
