'''
Created on Jun 9, 2020

@author: Sascha Kuhnke
'''
import sys

from algorithms.algorithms import QCPSolver, AdaptiveDiscretization
from data.data import AlgorithmData, Data
from input_output.input_reader import InputReader
from input_output.output_writer import OutputWriter


# Algorithm data
DISCRETIZATION = AlgorithmData.DISCRETIZATION
QCP_SOLVER = AlgorithmData.QCP_SOLVER
ADAPTIVE = AlgorithmData.ADAPTIVE
NON_ITERATIVE = AlgorithmData.NON_ITERATIVE
ALL = AlgorithmData.ALL
RANDOM = AlgorithmData.RANDOM 
HIGHEST_DEGREE = AlgorithmData.HIGHEST_DEGREE
RELAXATION_VERTEX_COVER = AlgorithmData.RELAXATION_VERTEX_COVER
BARON = AlgorithmData.BARON
SCIP = AlgorithmData.SCIP
GUROBI = AlgorithmData.GUROBI
IPOPT = AlgorithmData.IPOPT
SNOPT = AlgorithmData.SNOPT
MINOS = AlgorithmData.MINOS


if __name__ == '__main__':
    
    
    # Use algorithm data from arguments if given
    if len(sys.argv) == 7:
        name_of_instance = sys.argv[1]
        algorithm = sys.argv[2]
        disc_type = sys.argv[3]
        disc_variable_selection = sys.argv[4]  
        qcp_solver = sys.argv[5]
        disc_size = sys.argv[6] 
        
        stderr = None
        
    # Use manual algorithm data for testing
    else:    
        name_of_instance = "small"
        available_algorithms = [DISCRETIZATION, QCP_SOLVER]
        algorithm = available_algorithms[0]
        available_disc_types = [ADAPTIVE, NON_ITERATIVE]
        disc_type = available_disc_types[0]
        available_disc_variable_seletion = [ALL, RANDOM, HIGHEST_DEGREE, RELAXATION_VERTEX_COVER]
        disc_variable_selection = available_disc_variable_seletion[2]
        available_qcp_solvers = [BARON, SCIP, GUROBI, IPOPT, SNOPT, MINOS]
        qcp_solver = available_qcp_solvers[1]
        disc_size = 3
        
        stderr = sys.stderr
        
    
    # Time limits and optimality gap
    time_limit_discretization = 3600.0
    time_limit_iteration = 1200.0
    time_limit_qcp = 4 * time_limit_discretization
    gap = 0.0001
    
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
    
    if algorithm == DISCRETIZATION:
        AdaptiveDiscretization(data, output_writer).start()
    elif algorithm == QCP_SOLVER:
        QCPSolver(data, output_writer).start()
    
    
