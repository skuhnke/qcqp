'''
Created on Jun 17, 2020

@author: Sascha Kuhnke
'''
import math

from algorithms.formulations import DiscretizedMIP, OriginalQCP, FeasibilityChecker
from data.data import AlgorithmData
from misc.misc import get_start_time, get_time_passed


# Constants
ZERO = 0.0
INFINITY = float("inf")

# Algorithm data
ADAPTIVE = AlgorithmData.ADAPTIVE
NON_ITERATIVE = AlgorithmData.NON_ITERATIVE
BARON = AlgorithmData.BARON
SCIP = AlgorithmData.SCIP
GUROBI = AlgorithmData.GUROBI
IPOPT = AlgorithmData.IPOPT
SNOPT = AlgorithmData.SNOPT
MINOS = AlgorithmData.MINOS


class Algorithm():
    """Superclass for all algorithms."""
    
    def __init__(self, data, output_writer):
        
        self.data = data
        self.instance_data = data.instance_data
        self.algorithm_data = data.algorithm_data
        self.output_writer = output_writer
        
        self.dual_bound = INFINITY
        self.objective_value = -1 * INFINITY
            
        self.solution = None
        self.is_solved = "Not solved"
        
        
    def start(self):
        """Starts the performance of the algorithm."""
        
        self.initialize_algorithm()
        self.solve()
        self.finish_algorithm()


    def initialize_algorithm(self):
        """Initializes the time counter and creates the optimization problem."""
    
        self.time_start = get_start_time()
        self.initialize_optimization_problem()
            
    
    def finish_algorithm(self):
        """Calculates the required time."""
        
        self.time_required = get_time_passed(self.time_start)
        
        # Problem is solved
        if self.solution != None:
            # Check feasibility of solution
            self.check_feasiblity()
            
            # Write solution inta a .sol file 
            self.output_writer.write_solution(self.solution)
          
        self.output_writer.close_summary_file(self.dual_bound, self.objective_value, self.time_required)
        self.output_writer.add_results(self.data, self.is_solved, self.dual_bound, self.objective_value, self.time_required)     
 
 
    def check_feasiblity(self):
        """Checks the feasibility of the calculated solution."""
        
        feasibility_tolerance_checker = self.algorithm_data.feasibility_tolerance_checker
        time_limit_checker = 60.0
         
        feasibility_checker = FeasibilityChecker(self.data, self.output_writer, self.solution)
        gams_environment_checker = feasibility_checker.gams_environment
        feasibility_checker.solve(time_limit_checker)
        
        if (gams_environment_checker.job_is_solved() and 
            abs(self.objective_value - gams_environment_checker.get_objective_value()) <= feasibility_tolerance_checker):
            self.is_solved = "Solved" 
        

class AdaptiveDiscretization(Algorithm):
    """Solve the QCP with an adaptive discretization algorithm."""

    def initialize_optimization_problem(self):
        """Initializes the discretized MIP."""
        
        if self.algorithm_data.disc_type in [ADAPTIVE, NON_ITERATIVE]:
            self.optimization_problem = DiscretizedMIP(self.data, self.output_writer)
        self.gams_environment = self.optimization_problem.gams_environment
        
        self.optimization_problem.initialize_discretization()
        

    def solve(self):
        """Iteration loop of the adaptive discretzation."""
    
        time_start = self.time_start
        algorithm_data = self.algorithm_data
        time_limit_discretization = algorithm_data.time_limit_discretization
        time_limit_iteration = algorithm_data.time_limit_iteration
        
        terminate_algorithm = False
        objective_value_last = -1 * INFINITY
        objective_value_second_last = -1 * INFINITY
        
        while ((time_limit_discretization - get_time_passed(time_start) > 10) and not terminate_algorithm):
            
            # Reduce time limit for discretized problem if necessary
            if time_limit_discretization - get_time_passed(time_start) < time_limit_iteration:
                time_limit_iteration = round(time_limit_discretization - get_time_passed(time_start) - 10)
                
            self.optimization_problem.solve(time_limit_iteration, algorithm_data.iteration)    

            # Discretized problem is solved
            if self.optimization_problem.discretization_solved:
                objective_value_curr = self.optimization_problem.objective_value_iteration
                
                if objective_value_curr > self.objective_value:
                    self.objective_value = objective_value_curr
                    self.solution = self.optimization_problem.solution_iteration
                    
                # Check improvement of the last two iterations
                if algorithm_data.iteration >= 2:
                    # No significant improvements in the last two iterations -> stop algorithm
                    if ((self.objective_value != ZERO and 
                         abs((self.objective_value - objective_value_second_last) / self.objective_value) <= 0.0001) or
                         (self.objective_value == objective_value_second_last)):
                        terminate_algorithm = True
    
                objective_value_second_last = objective_value_last
                objective_value_last = self.objective_value
                
                algorithm_data.iteration += 1    
                
                self.optimization_problem.adapt_discretization()
    
            # Discretized problem is not solved -> stop the algorithmn
            else:
                if self.gams_environment.job_is_infeasible():
                    self.is_solved = "Infeasible"
                terminate_algorithm = True
    
   
class QCPSolver(Algorithm):
    """Solve the QCP with a global optimization solver."""

    def initialize_optimization_problem(self):
        """Initializes the original QCP."""
        
        self.optimization_problem = OriginalQCP(self.data, self.output_writer)
        self.gams_environment = self.optimization_problem.gams_environment
        

    def solve(self):
        """Solves the original QCP."""
    
        qcp_solver = self.algorithm_data.qcp_solver
        tries_local_solver = self.algorithm_data.tries_local_solver
    
        # Use a global solver
        if qcp_solver in [BARON, SCIP, GUROBI]:
            self.optimization_problem.solve(self.algorithm_data.time_limit_qcp)
            
            if not math.isnan(self.gams_environment.get_dual_bound()):
                self.dual_bound = self.gams_environment.get_dual_bound()
            
            if self.gams_environment.job_is_solved():
                self.solution = self.gams_environment.get_solution()
                self.objective_value = self.gams_environment.get_objective_value()
        
        # Use a local solver   
        elif qcp_solver in [IPOPT, SNOPT, MINOS]:
            for try_local_solver in range(tries_local_solver):
                
                if try_local_solver == 0:
                    # Set standard starting point of zero
                    self.optimization_problem.set_starting_point_zero()
                else:
                    # Generate random starting point
                    self.optimization_problem.set_random_starting_point(try_local_solver)
                
                self.optimization_problem.solve(self.algorithm_data.time_limit_discretization / tries_local_solver, try_local_solver)      
     
                if self.gams_environment.job_is_solved():
                    objective_value_curr = self.gams_environment.get_objective_value()   
                    
                    if objective_value_curr > self.objective_value:
                        self.solution = self.gams_environment.get_solution()
                        self.objective_value = objective_value_curr
                        
                self.algorithm_data.iteration += 1        
        
