'''
Created on Sep 12, 2019

@author: Sascha Kuhnke
'''
import copy
import sys

from data.data import AlgorithmData, Data
from input_output.input_reader import InputReader
from algorithms.formulations import PQChecker


# Constants
ONE = 1.0
ZERO = 0.0

# Algorithm Data
QCP_SOLVER = AlgorithmData.QCP_SOLVER
BARON = AlgorithmData.BARON


class PQFeasibilityChecker(object):
    """Class to check feasibility of a solution based on the pq-formulation."""

    def __init__(self, data, output_writer, solution, objective_value):

        self.data = data
        self.instance_data = data.instance_data
        self.algorithm_data = data.algorithm_data
        self.output_writer = output_writer
        self.solution = solution
        self.objective_value = objective_value

        self.is_solved = "Checker infeasible"
        
        
    def check_if_solved(self):
        """Checks if the current optimization problem is solved."""
        
        feasibility_tolerance_checker = self.algorithm_data.feasibility_tolerance_checker
        
        is_feasible_qcp = True
        is_feasible_constraints = True 

        self.check_feasibility_qcp()
        self.check_feasibility_constraints()

        if ((not self.is_solved_blp) or 
            abs(self.objective_value - self.objective_value_blp) > feasibility_tolerance_checker):
            is_feasible_qcp = False
        
        if ((not self.is_solved_constraints) or 
            abs(self.objective_value - self.objective_value_constraints) > feasibility_tolerance_checker):
            is_feasible_constraints = False
        
        if is_feasible_qcp or is_feasible_constraints:
            self.is_solved = "Solved"
            
        return self.is_solved


    def check_feasibility_qcp(self):
        """Checks feasibility of a solution by solving the original QCP of the pq-formulation with fixed variables. 
        Uses the preprocessed instance data."""
        
        self.is_solved_blp = True
        self.objective_value_blp = None
        
        time_limit_checker = 60.0
        
        # Create a copy in order not to change the original data
        algorithm_data_copy = copy.copy(self.algorithm_data)
        algorithm_data_copy.algorithm = QCP_SOLVER
        algorithm_data_copy.qcp_solver = BARON
        
        # Check feasibility via original pq-formulation
        problem_checker = PQChecker(self.data, self.output_writer, self.solution)
        gams_environment_checker = problem_checker.gams_environment
        problem_checker.solve(time_limit_checker)  
        
        if not gams_environment_checker.job_is_solved():
            self.is_solved_blp = False
            
        self.objective_value_blp = gams_environment_checker.get_objective_value()
        
        
    def check_feasibility_constraints(self):
        """Checks feasibility of a solution by considering all constraints of the original pq-formulation.
        Uses the original instance data without preprocessing."""

        self.is_solved_constraints = True
        self.objective_value_constraints = None
        
        # Generate original instance data without preprocessing
        self.data = Data(self.instance_data.name, self.algorithm_data.formulation, self.algorithm_data.algorithm, self.algorithm_data.disc_type, 
                self.algorithm_data.disc_variant, self.algorithm_data.qcp_solver, self.algorithm_data.tries_local_solver, 
                self.algorithm_data.time_limit_discretization, self.algorithm_data.time_limit_iteration, self.algorithm_data.time_limit_qcp, 
                self.algorithm_data.gap, self.algorithm_data.disc_size, self.algorithm_data.feasibility_tolerance, 
                self.algorithm_data.integer_tolerance, self.algorithm_data.feasibility_tolerance_checker, 
                self.algorithm_data.perform_preprocessing, self.algorithm_data.evaluate_preprocessing, self.instance_data.stderr)
        input_reader = InputReader(self.data)
        input_reader.read_input()
 
        # Checks feasibility using the pq-formulation
        self.get_variable_values()
        self.check_feasibility()
        self.get_objective_value()
        

    def get_variable_values(self):
        """Determines the values of all variables in the pq-formulation."""
        
        UN_IN = self.instance_data.units_in
        UN_OUT = self.instance_data.units_out
        WS = self.instance_data.water_sources
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        
        FL = {}
        FL_PR = {}
        PR = {}
        
        # Initialize all variables with zero
        for un_out in UN_OUT:
            for un_in in UN_IN:
                FL[(un_out, un_in)] = ZERO
            
        for ws in WS:
            for pl in PL:
                for wd in WD:
                    FL_PR[(ws, pl, wd)] = ZERO
                    
        for pl in PL:
            for ws in WS:
                PR[(pl, ws)] = ZERO
         
        try:
            with open(self.output_writer.path_solution_file, 'r') as solution_file:
                       
                # Read flow variables
                for line in solution_file:
                    line_curr = line.split()
                    
                    un_out = line_curr[0]
                    un_in = line_curr[1]
                    FL[(un_out, un_in)] = float(line_curr[2])
            
        except EnvironmentError:
            print("Could not open solution file for reading.")
            sys.exit()             
            
        # Determine proportion variables
        for pl in PL:
            fl_in_pl = ZERO
            for ws in WS:
                fl_in_pl += FL[(ws, pl)]
            
            if fl_in_pl > ZERO:
                for ws in WS:
                    PR[(pl, ws)] = FL[(ws, pl)] / fl_in_pl
            else:
                PR[(pl, WS[0])] = ONE
                
        # Determine path flow variables
        for ws in WS: 
            for pl in PL:
                for wd in WD:
                    FL_PR[(ws, pl, wd)] = PR[(pl, ws)] * FL[(pl, wd)]
                   
        self.FL = FL
        self.FL_PR = FL_PR
        self.PR = PR                   
                
                
    def check_feasibility(self):
        """Checks feasibility of the given solution using the constrains of the pq-formulation."""
                
        UN_IN = self.instance_data.units_in
        UN_OUT = self.instance_data.units_out
        WS = self.instance_data.water_sources
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        CO = self.instance_data.contaminants
        FL_MAX_UN = self.instance_data.fl_max_un
        FL_MAX = self.instance_data.fl_max
        PO_WS = self.instance_data.po_ws
        PO_MIN_WD = self.instance_data.po_min_wd
        PO_MAX_WD = self.instance_data.po_max_wd              
        FL = self.FL
        FL_PR = self.FL_PR
        PR = self.PR                
                
        # Check bilinear terms 
        for ws in WS: 
            for pl in PL:
                for wd in WD:
                    if not self.is_equal(FL_PR[(ws, pl, wd)], PR[(pl, ws)] * FL[(pl, wd)]):
                        message = "Not feasible: Bilinear " + ws + " " + pl + " " + wd
                        self.set_infeasible_and_write_message(message)                         
        
        # Check if proportions add to one                
        for pl in PL:
            lhs = ZERO
            for ws in WS:
                lhs += PR[(pl, ws)]
            if not self.is_equal(lhs, ONE):
                message = "Not feasible: Proportion Sum " + pl
                self.set_infeasible_and_write_message(message)                

        # Check specification requirements
        for wd in WD:
            for co in CO:
                lhs = ZERO
                rhs = ZERO
                
                for ws in WS:
                    lhs += PO_WS[(ws, co)] * FL[(ws, wd)]
                    rhs += FL[(ws, wd)]
                    
                for ws in WS:
                    for pl in PL:
                        lhs += PO_WS[(ws, co)] * FL_PR[(ws, pl, wd)]
                        rhs += FL_PR[(ws, pl, wd)]
                
                rhs_max = rhs * PO_MAX_WD[(wd, co)]
                rhs_min = rhs * PO_MIN_WD[(wd, co)]
                
                if not self.is_less_or_equal(lhs, rhs_max):
                    message = "Not feasible: SpecMax " + wd + " " + co
                    self.set_infeasible_and_write_message(message)

                if not self.is_less_or_equal(-1 * lhs, -1 * rhs_min):
                    message = "Not feasible: SpecMin " + wd + " " + co
                    self.set_infeasible_and_write_message(message)                    
        
        # Check capacities of units            
        for ws in WS:
            fl_out_ws = ZERO
            for un_in in UN_IN:
                fl_out_ws += FL[(ws, un_in)]
            if not self.is_less_or_equal(fl_out_ws, FL_MAX_UN[ws]):
                message = "Not feasible: Capacity1 " + ws
                self.set_infeasible_and_write_message(message)                     
                    
        for pl in PL:
            fl_out_pl = ZERO
            for wd in WD:
                fl_out_pl += FL[(pl, wd)]
            if not self.is_less_or_equal(fl_out_pl, FL_MAX_UN[pl]):
                message = "Not feasible: Capacity2 " + pl
                self.set_infeasible_and_write_message(message)                     
                    
        for wd in WD:
            fl_in_wd = ZERO
            for un_out in UN_OUT:
                fl_in_wd += FL[(un_out, wd)]
            if not self.is_less_or_equal(fl_in_wd, FL_MAX_UN[wd]):
                message = "Not feasible: Capacity3 " + wd
                self.set_infeasible_and_write_message(message) 
        
        # Check capacities on pipes            
        for un_out in UN_OUT:
            for un_in in UN_IN:
                if not self.is_less_or_equal(FL[(un_out, un_in)], FL_MAX[(un_out, un_in)]):
                    message = "Not feasible: Capacity4 " + un_out + " " + un_in
                    self.set_infeasible_and_write_message(message) 

        # Check non-negativity of variables
        for un_out in UN_OUT:
            for un_in in UN_IN:
                if not self.is_less_or_equal(-1 * FL[(un_out, un_in)], 0):
                    message = "Not feasible: NonNeg1 " + un_out + " " + un_in
                    self.set_infeasible_and_write_message(message)                     
            
        for ws in WS:
            for pl in PL:
                for wd in WD:
                    if not self.is_less_or_equal(-1 * FL_PR[(ws, pl, wd)], 0):
                        message = "Not feasible: NonNeg2 " + ws + " " + pl + " " + wd
                        self.set_infeasible_and_write_message(message)                         
                    
        for pl in PL:
            for ws in WS:
                if not self.is_less_or_equal(-1 * PR[(pl, ws)], 0):
                    message = "Not feasible: NonNeg3 " + pl + " " + ws
                    self.set_infeasible_and_write_message(message) 


    def get_objective_value(self):
        """Calculates the objective value of the given solution."""
        
        UN_IN = self.instance_data.units_in
        UN_OUT = self.instance_data.units_out       
        COST = self.instance_data.cost
        FL = self.FL
        objective_value_constraints = ZERO
        
        for un_out in UN_OUT:
            for un_in in UN_IN:
                objective_value_constraints += COST[(un_out, un_in)] * FL[(un_out, un_in)]
                
        self.objective_value_constraints = round(objective_value_constraints, 4)        
         

    def is_equal(self, lhs, rhs):
        """Returns True if lhs is equal to rhs.""" 

        feasibility_tolerance_checker = self.algorithm_data.feasibility_tolerance_checker
        
        if (lhs - feasibility_tolerance_checker <= rhs) and (rhs <= lhs + feasibility_tolerance_checker):
            return True
        else:
            self.is_feasible = False
            return False

        
    def is_less_or_equal(self, lhs, rhs):
        """Returns True if lhs is less or equal to rhs.""" 

        feasibility_tolerance_checker = self.algorithm_data.feasibility_tolerance_checker
        
        if lhs - feasibility_tolerance_checker <= rhs:
            return True
        else:
            self.is_feasible = False
            return False
        
     
    def set_infeasible_and_write_message(self, message):
        """Writes the given message into console and summary file."""
        
        self.is_solved_constraints = False
        self.output_writer.write_line_to_summary_file(message)
        
        