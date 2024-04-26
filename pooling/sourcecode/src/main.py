'''
Created on Feb 12, 2019

@author: Sascha Kuhnke
'''
import sys

from data.data import AlgorithmData, Data
from input_output.input_reader import InputReader
from input_output.output_writer import OutputWriter
from algorithms.algorithms import AdaptiveDiscretization, QCPSolver


# Algorithm data
PQ_FORMULATION = AlgorithmData.PQ_FORMULATION
TP_FORMULATION = AlgorithmData.TP_FORMULATION
DISCRETIZATION = AlgorithmData.DISCRETIZATION
QCP_SOLVER = AlgorithmData.QCP_SOLVER
ADAPTIVE = AlgorithmData.ADAPTIVE
NON_ITERATIVE = AlgorithmData.NON_ITERATIVE
PROPORTION = AlgorithmData.PROPORTION
FLOW = AlgorithmData.FLOW
POOL = AlgorithmData.POOL
BARON = AlgorithmData.BARON
SCIP = AlgorithmData.SCIP
GUROBI = AlgorithmData.GUROBI
IPOPT = AlgorithmData.IPOPT
SNOPT = AlgorithmData.SNOPT
MINOS = AlgorithmData.MINOS


if __name__ == '__main__':


    # Use algorithm data from arguments if given
    if len(sys.argv) == 8:
        name_of_instance = sys.argv[1]
        formulation = sys.argv[2]  
        algorithm = sys.argv[3]
        disc_type = sys.argv[4]  
        disc_variant = sys.argv[5] 
        qcp_solver = sys.argv[6]     
        disc_size = sys.argv[7] 
        
        stderr = None

    # Use manual algorithm data for testing
    else:
        name_of_instance = "stdAsmall"
        available_formulations = [PQ_FORMULATION, TP_FORMULATION]
        formulation = available_formulations[1]
        available_algorithms = [DISCRETIZATION, QCP_SOLVER]
        algorithm = available_algorithms[1]
        available_disc_types = [ADAPTIVE, NON_ITERATIVE]
        disc_type = available_disc_types[0]
        available_disc_variants = [PROPORTION, FLOW, POOL]
        disc_variant = available_disc_variants[0]
        available_qcp_solvers = [BARON, SCIP, GUROBI, IPOPT, SNOPT, MINOS]
        qcp_solver = available_qcp_solvers[3]       
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
    
    # Preprocessing
    perform_preprocessing = True
    evaluate_preprocessing = False
    
    # Local solver options
    tries_local_solver = 10
    
    # Initialize data
    data = Data(name_of_instance, formulation, algorithm, disc_type, disc_variant, qcp_solver, tries_local_solver, 
                time_limit_discretization, time_limit_iteration, time_limit_qcp, gap, disc_size, feasibility_tolerance, 
                integer_tolerance, feasibility_tolerance_checker, perform_preprocessing, evaluate_preprocessing, stderr)
    
    # Read input
    input_reader = InputReader(data)
    input_reader.read_input()
    
    # Initialize output
    output_writer = OutputWriter(data)
    output_writer.initialize_output()
    
    # Run algorithm
    if algorithm == DISCRETIZATION:
        AdaptiveDiscretization(data, output_writer).start()
    elif algorithm == QCP_SOLVER:
        QCPSolver(data, output_writer).start()

