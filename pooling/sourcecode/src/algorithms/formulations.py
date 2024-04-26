'''
Created on Feb 12, 2019

@author: Sascha Kuhnke
'''
from gams.workspace import GamsExceptionExecution
from math import ceil
import operator
import random

from algorithms.gams_api import  EnvironmentGAMSPoolingProblem
from data.data import AlgorithmData
from misc.misc import get_start_time, get_time_passed


# Constants
ONE = 1.0
ZERO = 0.0

# Algorithm data
PQ_FORMULATION = AlgorithmData.PQ_FORMULATION
TP_FORMULATION = AlgorithmData.TP_FORMULATION
QCP_SOLVER = AlgorithmData.QCP_SOLVER


class PoolingProblem():
    """Base class for formulations of the Pooling Problem."""
    
    def __init__(self, data, output_writer, model_type, gams_file, model_name, name_gams_workspace):
        
        self.instance_data = data.instance_data
        self.algorithm_data = data.algorithm_data
        self.output_writer = output_writer
        
        # Set up GAMS environment
        self.gams_environment = EnvironmentGAMSPoolingProblem(data, output_writer, model_type, model_name, gams_file, name_gams_workspace)
        

    def solve(self, time_limit, log_file_suffix=""):
        """Solves the Pooling Problem."""
    
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
                    

class PoolingProblemDiscretized(PoolingProblem):
    """Class for formulations of the Pooling Problem based on discretization."""
    
    def __init__(self, data, output_writer, gams_file, model_name):
        
        model_type = "MIP"  
        name_gams_workspace = "gams_workspace_disc"         
        
        super().__init__(data, output_writer, model_type, gams_file, model_name, name_gams_workspace)
        

    def solve(self, time_limit, log_file_suffix=""):
        """Solves the discretized problem."""
    
        super().solve(time_limit, log_file_suffix)
        
        if self.gams_environment.job_is_solved():
            self.discretization_solved = True
            self.solution_iteration = self.gams_environment.get_solution()
            self.objective_value_iteration = self.gams_environment.get_objective_value()
        else:
            self.discretization_solved = False
            

    def initialize_discretization(self):
        """Sets the initial discretization values for the first iteration."""
        
        self.initialize_discretization_data()
        self.initialize_fixed_variables()
        self.initialize_discretization_values()
        self.write_discretization_to_file() 
        self.finalize_fixed_variables()
        
        
    def adapt_discretization(self):
        """Adapts the discretization values based on the previous solution."""
        
        self.initialize_discretization_data()
        self.initialize_starting_point()
        self.adapt_discretization_values()
        self.write_discretization_to_file()
        self.write_starting_point_to_file()  
        

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
                
        
class PQDiscPool(PoolingProblemDiscretized):
    """Class for pool discretization in the pq-formulation of the Pooling Problem with the formulation of Dey and Gupte."""
    
    def __init__(self, data, output_writer):
        
        gams_file = "pq_disc_pl_dey_gupte.gms"
        model_name = "PQ_DISC_PL_DEY_GUPTE"        
        
        super().__init__(data, output_writer, gams_file, model_name) 
        
        
    def initialize_discretization_values(self):
        """Initializes the pool discretization in the pq-formulation."""
        
        UN_OUT = self.instance_data.units_out
        WS = self.instance_data.water_sources        
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        PIPE_EXISTS = self.instance_data.pipe_exists
        J = self.algorithm_data.disc_indices

        START_SIZE_DISC = self.algorithm_data.disc_size
        FRAC = {}
        SIZE = {}  
        CHI_MIP_START = {}

        # Determine initial discretization values 
        for pl in PL:
            SIZE[pl] = START_SIZE_DISC
            for j in J:
                if int(j) < START_SIZE_DISC:
                    FRAC[(pl, j)] = ONE / START_SIZE_DISC
                else:
                    FRAC[(pl, j)] = ZERO

                self.set_discretization_value("FRAC", (pl, j), FRAC[(pl, j)])

        # Remove unused discretization                
        for pl in PL:
            for j in J:
                if int(j) >= START_SIZE_DISC:
                    found_existing_pipe = False
                    for wd in WD:
                        if found_existing_pipe == False and PIPE_EXISTS[(pl, wd)]:
                            self.set_discretization_value("CHI.Fx", (pl, j, wd), ONE)
                            found_existing_pipe = True
                        else:
                            self.set_discretization_value("CHI.Fx", (pl, j, wd), ZERO)
                        for ws in WS:
                            self.set_discretization_value("FL_PR_DISC.Fx", (ws, pl, j, wd), ZERO)
                            
        # Remove unused variables   
        for un_out in UN_OUT:
            for wd in WD:
                if not PIPE_EXISTS[(un_out, wd)]:
                    self.set_fixed_variable("FL.Fx", (un_out, wd), ZERO)

        for ws in WS:
            for pl in PL:
                for wd in WD:
                    if (not PIPE_EXISTS[(ws, pl)]) or (not PIPE_EXISTS[(pl, wd)]):
                        self.set_fixed_variable("FL_PR.Fx", (ws, pl, wd), ZERO)   
         
        for pl in PL:
            for wd in WD:
                if not PIPE_EXISTS[(pl, wd)]:
                    for j in J:
                        self.set_fixed_variable("CHI.Fx", (pl, j, wd), ZERO)
                        for ws in WS:     
                            self.set_fixed_variable("FL_PR_DISC.Fx", (ws, pl, j, wd), ZERO)                             

        self.algorithm_data.FRAC = FRAC
        self.algorithm_data.SIZE = SIZE
        self.algorithm_data.CHI_MIP_START = CHI_MIP_START        


    def adapt_discretization_values(self):
        """Adapts the pool discretization in the pq-formulation. 
        
        Currently not implemented. Here, the same function as for the tp-formulation can be used."""
        

class TPDiscProportion(PoolingProblemDiscretized):
    """Class for proportion discretization in the tp-formulation of the Pooling Problem."""
    
    def __init__(self, data, output_writer):
        
        gams_file = "tp_disc_pr.gms"
        model_name = "TP_DISC_PR"        
        
        super().__init__(data, output_writer, gams_file, model_name) 
        
        
    def initialize_discretization_values(self):
        """Initializes the proportion discretization in the tp-formulation."""
        
        UN_IN = self.instance_data.units_in
        WS = self.instance_data.water_sources        
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        PIPE_EXISTS = self.instance_data.pipe_exists
        J = self.algorithm_data.disc_indices
        SIZE_DISC = self.algorithm_data.disc_size
        
        PR_DISC = {}  
        LENGTH = {} 
        STEP_SIZE = {}  
        CHI_MIP_START = {}
        
        # Determine initial discretization values
        for pl in PL:
            for wd in WD:
                    
                LENGTH[(pl, wd)] = ONE
                STEP_SIZE[(pl, wd)] = LENGTH[(pl, wd)] / (SIZE_DISC - 1)
                for j in J:
                    PR_DISC[(pl, wd, j)] = int(j) * STEP_SIZE[(pl, wd)]
                    self.set_discretization_value("PR_DISC", (pl, wd, j), PR_DISC[(pl, wd, j)])
    
                    
        # Remove unused variables   
        for ws in WS:
            for un_in in UN_IN:
                if not PIPE_EXISTS[(ws, un_in)]:
                    self.set_fixed_variable("FL.Fx", (ws, un_in), ZERO)

        for ws in WS:
            for pl in PL:
                for wd in WD:
                    if (not PIPE_EXISTS[(ws, pl)]) or (not PIPE_EXISTS[(pl, wd)]):
                        self.set_fixed_variable("FL_PR.Fx", (ws, pl, wd), ZERO)   
        
        for pl in PL:
            for wd in WD:
                if not PIPE_EXISTS[(pl, wd)]:
                    self.set_fixed_variable("PR.Fx", (pl, wd), ZERO)   
         
        for pl in PL:
            for wd in WD:
                if not PIPE_EXISTS[(pl, wd)]:
                    for j in J:
                        if int(j) == 0:
                            self.set_fixed_variable("CHI.Fx", (pl, wd, j), ONE)
                        else:
                            self.set_fixed_variable("CHI.Fx", (pl, wd, j), ZERO)    
                            for ws in WS:
                                self.set_fixed_variable("FL_DISC.Fx", (ws, pl, wd, j), ZERO)     
                                
        for ws in WS:
            for pl in PL:
                if not PIPE_EXISTS[(ws, pl)]:   
                    for wd in WD:
                        for j in J:
                            self.set_fixed_variable("FL_DISC.Fx", (ws, pl, wd, j), ZERO)

        self.algorithm_data.PR_DISC = PR_DISC
        self.algorithm_data.LENGTH = LENGTH
        self.algorithm_data.STEP_SIZE = STEP_SIZE 
        self.algorithm_data.CHI_MIP_START = CHI_MIP_START        


    def adapt_discretization_values(self):  
        """Adapts the proportion discretization in the tp-formulation."""
        
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        J = self.algorithm_data.disc_indices
        SIZE_DISC = self.algorithm_data.disc_size
        feasibility_tolerance = self.algorithm_data.feasibility_tolerance
        integer_tolerance = self.algorithm_data.integer_tolerance
        solution_previous = self.gams_environment.job
        PR_DISC = self.algorithm_data.PR_DISC   
        LENGTH = self.algorithm_data.LENGTH  
        STEP_SIZE = self.algorithm_data.STEP_SIZE   
        CHI_MIP_START = self.algorithm_data.CHI_MIP_START

        # Determine adapted discretization values
        for pl in PL:
            for wd in WD:
                chi_selected = -1
                pr_selected = ZERO
                
                for j in J:
                    chi_curr = solution_previous.out_db.get_variable("CHI").find_record((pl, wd, j)).level
                    if chi_curr >= ONE - integer_tolerance:
                        chi_selected = int(j)
                        pr_selected = PR_DISC[(pl, wd, j)]
                
                # An interior point is selected        
                if (chi_selected > 0) and (chi_selected < SIZE_DISC - 1):

                    LENGTH[(pl, wd)] = LENGTH[(pl, wd)] / 2.0
                    STEP_SIZE[(pl, wd)] = LENGTH[(pl, wd)] / (SIZE_DISC - 1)
                    
                    # Align new discretization at the previous one
                    chi_selected_new = ceil(SIZE_DISC / 2.0) - 1
                    pr_disc_min = pr_selected - STEP_SIZE[(pl, wd)] * chi_selected_new
                    pr_disc_max = pr_disc_min + LENGTH[(pl, wd)]
                    
                    # Shift discretization to the left boundary
                    while (pr_disc_min < ZERO):
                        chi_selected_new -= 1
                        pr_disc_min = pr_selected - STEP_SIZE[(pl, wd)] * chi_selected_new
                        pr_disc_max = pr_disc_min + LENGTH[(pl, wd)]
                        
                    # Shift discretization to the right boundary
                    while (pr_disc_max > ONE):
                        chi_selected_new += 1
                        pr_disc_min = pr_selected - STEP_SIZE[(pl, wd)] * chi_selected_new
                        pr_disc_max = pr_disc_min + LENGTH[(pl, wd)]

                # The first point is selected
                elif chi_selected == 0:
                    
                    # The selected point is on the left boundary
                    if pr_selected <= feasibility_tolerance: 
                        
                        LENGTH[(pl, wd)] = LENGTH[(pl, wd)] / 2.0                        
                        STEP_SIZE[(pl, wd)] = LENGTH[(pl, wd)] / (SIZE_DISC - 1)

                        # Align new discretization at the previous one
                        chi_selected_new = 0
                        pr_disc_min = ZERO
                        
                    # The selected point is not on the left boundary   
                    else:
                        
                        # Keep the step size and shift discretization to the left 
                        STEP_SIZE[(pl, wd)] = LENGTH[(pl, wd)] / (SIZE_DISC - 1)
                        
                        # Align new discretization at the previous one
                        chi_selected_new = ceil(SIZE_DISC / 2.0) - 1
                        pr_disc_min = pr_selected - STEP_SIZE[(pl, wd)] * chi_selected_new
                        
                        # Shift discretization to the left boundary
                        while (pr_disc_min < ZERO):
                            chi_selected_new -= 1
                            pr_disc_min = pr_selected - STEP_SIZE[(pl, wd)] * chi_selected_new
                                                    
                # The last point is selected    
                elif chi_selected == SIZE_DISC - 1:
                    
                    # The selected point is on the right boundary
                    if pr_selected + feasibility_tolerance >= ONE: 
                        
                        LENGTH[(pl, wd)] = LENGTH[(pl, wd)] / 2.0
                        STEP_SIZE[(pl, wd)] = LENGTH[(pl, wd)] / (SIZE_DISC - 1)

                        # Align new discretization at the previous one
                        chi_selected_new = SIZE_DISC - 1
                        pr_disc_min = pr_selected - STEP_SIZE[(pl, wd)] * chi_selected_new
                        
                    # The selected point is not on the right boundary   
                    else:
                        
                        # Keep the step size and shift discretization to the right 
                        STEP_SIZE[(pl, wd)] = LENGTH[(pl, wd)] / (SIZE_DISC - 1)
                                    
                        # Align new discretization at the previous one
                        chi_selected_new = ceil(SIZE_DISC / 2.0) - 1
                        pr_disc_min = pr_selected - STEP_SIZE[(pl, wd)] * chi_selected_new
                        pr_disc_max = pr_disc_min + LENGTH[(pl, wd)]
                    
                        # Shift discretization to the right boundary
                        while (pr_disc_max > ONE):
                            chi_selected_new += 1
                            pr_disc_min = pr_selected - STEP_SIZE[(pl, wd)] * chi_selected_new
                            pr_disc_max = pr_disc_min + LENGTH[(pl, wd)]                        
                
                # Set new discretization values and corresponding MIP start    
                for j in J:
                    PR_DISC[(pl, wd, j)] = pr_disc_min + int(j) * STEP_SIZE[(pl, wd)]
                    
                    if int(j) == chi_selected_new:
                        CHI_MIP_START[(pl, wd, j)] = ONE
                    else:
                        CHI_MIP_START[(pl, wd, j)] = ZERO
        
        # Update discretization values and corresponding MIP start                                            
        for pl in PL:
            for wd in WD:   
                for j in J:
                    self.set_discretization_value("PR_DISC", (pl, wd, j), PR_DISC[(pl, wd, j)])  
                    self.set_starting_point_value("CHI.L", (pl, wd, j), CHI_MIP_START[(pl, wd, j)]) 
                    

class TPDiscFlow(PoolingProblemDiscretized):
    """Class for flow discretization in the tp-formulation of the Pooling Problem."""
    
    def __init__(self, data, output_writer):
        
        gams_file = "tp_disc_fl.gms"
        model_name = "TP_DISC_FL"        
        
        super().__init__(data, output_writer, gams_file, model_name) 
        
        
    def initialize_discretization_values(self):
        """Initializes the flow discretization in the tp-formulation."""
        
        UN_IN = self.instance_data.units_in
        WS = self.instance_data.water_sources        
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        PIPE_EXISTS = self.instance_data.pipe_exists        
        J = self.algorithm_data.disc_indices
        SIZE_DISC = self.algorithm_data.disc_size
        FL_MAX = self.instance_data.fl_max
        
        FL_DISC = {}  
        LENGTH = {}
        STEP_SIZE = {}
        CHI_MIP_START = {}

        # Determine initial discretization values
        for ws in WS:
            for pl in PL:
                    
                LENGTH[(ws, pl)] = FL_MAX[(ws, pl)]
                STEP_SIZE[(ws, pl)] = LENGTH[(ws, pl)] / (SIZE_DISC - 1)
                for j in J:
                    FL_DISC[(ws, pl, j)] = int(j) * STEP_SIZE[(ws, pl)]
                    self.set_discretization_value("FL_DISC", (ws, pl, j), FL_DISC[(ws, pl, j)])
    
                         
        # Remove unused variables   
        for ws in WS:
            for un_in in UN_IN:
                if not PIPE_EXISTS[(ws, un_in)]:
                    self.set_fixed_variable("FL.Fx", (ws, un_in), ZERO)

        for ws in WS:
            for pl in PL:
                for wd in WD:
                    if (not PIPE_EXISTS[(ws, pl)]) or (not PIPE_EXISTS[(pl, wd)]):
                        self.set_fixed_variable("FL_PR.Fx", (ws, pl, wd), ZERO)   
                        
        for pl in PL:
            for wd in WD:
                if not PIPE_EXISTS[(pl, wd)]:
                    self.set_fixed_variable("PR.Fx", (pl, wd), ZERO)                           
    
        for ws in WS:     
            for pl in PL:
                if not PIPE_EXISTS[(ws, pl)]:
                    for j in J:
                        if int(j) == 0:
                            self.set_fixed_variable("CHI.Fx", (ws, pl, j), ONE)
                        else:
                            self.set_fixed_variable("CHI.Fx", (ws, pl, j), ZERO)
                            for wd in WD:
                                self.set_fixed_variable("PR_DISC.Fx", (pl, wd, ws, j), ZERO)
                                
        for pl in PL:
            for wd in WD:
                if not PIPE_EXISTS[(pl, wd)]:   
                    for ws in WS:
                        for j in J:
                            self.set_fixed_variable("PR_DISC.Fx", (pl, wd, ws, j), ZERO)                                                 

        self.algorithm_data.FL_DISC = FL_DISC  
        self.algorithm_data.LENGTH = LENGTH
        self.algorithm_data.STEP_SIZE = STEP_SIZE
        self.algorithm_data.CHI_MIP_START = CHI_MIP_START    
        
        
    def adapt_discretization_values(self):
        """Adapts the flow discretization in the tp-formulation."""
        
        WS = self.instance_data.water_sources
        PL = self.instance_data.pools
        FL_MAX = self.instance_data.fl_max
        J = self.algorithm_data.disc_indices
        SIZE_DISC = self.algorithm_data.disc_size
        feasibility_tolerance = self.algorithm_data.feasibility_tolerance
        integer_tolerance = self.algorithm_data.integer_tolerance
        solution_previous = self.gams_environment.job
        FL_DISC = self.algorithm_data.FL_DISC  
        LENGTH = self.algorithm_data.LENGTH
        STEP_SIZE = self.algorithm_data.STEP_SIZE
        CHI_MIP_START = self.algorithm_data.CHI_MIP_START

        # Determine adapted discretization values
        for ws in WS: 
            for pl in PL:
                chi_selected = -1
                fl_selected = ZERO
                
                for j in J:
                    chi_curr = solution_previous.out_db.get_variable("CHI").find_record((ws, pl, j)).level
                    if chi_curr >= ONE - integer_tolerance:
                        chi_selected = int(j)
                        fl_selected = FL_DISC[(ws, pl, j)]                

                # An interior point is selected        
                if (chi_selected > 0) and (chi_selected < SIZE_DISC - 1):
                    
                    LENGTH[(ws, pl)] = LENGTH[(ws, pl)] / 2.0
                    STEP_SIZE[(ws, pl)] = LENGTH[(ws, pl)] / (SIZE_DISC - 1)
                    
                    # Align new discretization at the previous one
                    chi_selected_new = ceil(SIZE_DISC / 2.0) - 1                    
                    fl_disc_min = fl_selected - STEP_SIZE[(ws, pl)] * chi_selected_new
                    fl_disc_max = fl_disc_min + LENGTH[(ws, pl)]
                    
                    # Shift discretization to the left boundary
                    while (fl_disc_min < ZERO):
                        chi_selected_new -= 1
                        fl_disc_min = fl_selected - STEP_SIZE[(ws, pl)] * chi_selected_new
                        fl_disc_max = fl_disc_min + LENGTH[(ws, pl)]
                        
                    # Shift discretization to the right boundary
                    while (fl_disc_max > FL_MAX[(ws, pl)]):
                        chi_selected_new += 1
                        fl_disc_min = fl_selected - STEP_SIZE[(ws, pl)] * chi_selected_new
                        fl_disc_max = fl_disc_min + LENGTH[(ws, pl)]               

                # The first point is selected
                elif chi_selected == 0:
                     
                    # The selected point is on the left boundary
                    if fl_selected <= feasibility_tolerance: 
                                             
                        LENGTH[(ws, pl)] = LENGTH[(ws, pl)] / 2.0                        
                        STEP_SIZE[(ws, pl)] = LENGTH[(ws, pl)] / (SIZE_DISC - 1)                            
                         
                        # Align new discretization at the previous one
                        chi_selected_new = 0                             
                        fl_disc_min = ZERO
                         
                    # The selected point is not on the left boundary   
                    else:
                        # Keep the step size and shift discretization to the left 
                        STEP_SIZE[(ws, pl)] = LENGTH[(ws, pl)] / (SIZE_DISC - 1) 

                        # Align new discretization at the previous one
                        chi_selected_new = ceil(SIZE_DISC / 2.0) - 1 
                        fl_disc_min = fl_selected - STEP_SIZE[(ws, pl)] * chi_selected_new

                        # Shift discretization to the left boundary
                        while (fl_disc_min < ZERO):
                            chi_selected_new -= 1
                            fl_disc_min = fl_selected - STEP_SIZE[(ws, pl)] * chi_selected_new
                         
                # The last point is selected    
                elif chi_selected == SIZE_DISC - 1:
                     
                    # The selected point is on the right boundary
                    if fl_selected + feasibility_tolerance >= FL_MAX[(ws, pl)]: 
                                                
                        LENGTH[(ws, pl)] = LENGTH[(ws, pl)] / 2.0                        
                        STEP_SIZE[(ws, pl)] = LENGTH[(ws, pl)] / (SIZE_DISC - 1) 
                         
                        # Align new discretization at the previous one
                        chi_selected_new = SIZE_DISC - 1                             
                        fl_disc_min = fl_selected - STEP_SIZE[(ws, pl)] * chi_selected_new
                    
                    # The selected point is not on the right boundary   
                    else:
                        
                        # Keep the step size and shift discretization to the right 
                        STEP_SIZE[(ws, pl)] = LENGTH[(ws, pl)] / (SIZE_DISC - 1)     
                         
                        # Align new discretization at the previous one
                        chi_selected_new = ceil(SIZE_DISC / 2.0) - 1                    
                        fl_disc_min = fl_selected - STEP_SIZE[(ws, pl)] * chi_selected_new
                        fl_disc_max = fl_disc_min + LENGTH[(ws, pl)]
                         
                        # Shift discretization to the right boundary
                        while (fl_disc_max > FL_MAX[(ws, pl)]):
                            chi_selected_new += 1
                            fl_disc_min = fl_selected - STEP_SIZE[(ws, pl)] * chi_selected_new
                            fl_disc_max = fl_disc_min + LENGTH[(ws, pl)]                           

                # Store discretization values and corresponding MIP start
                for j in J:
                    FL_DISC[(ws, pl, j)] = fl_disc_min + int(j) * STEP_SIZE[(ws, pl)]
                
                    if int(j) == chi_selected_new:
                        CHI_MIP_START[(ws, pl, j)] = ONE
                    else:
                        CHI_MIP_START[(ws, pl, j)] = ZERO                    
        
        # Update discretization values and corresponding MIP start
        for ws in WS: 
            for pl in PL:        
                for j in J:
                    self.set_discretization_value("FL_DISC", (ws, pl, j), FL_DISC[(ws, pl, j)])
                    self.set_starting_point_value("CHI.L", (ws, pl, j), CHI_MIP_START[(ws, pl, j)]) 
                    
        
class TPDiscPool(PoolingProblemDiscretized):
    """Class for pool discretization in the tp-formulation of the Pooling Problem."""
    
    def __init__(self, data, output_writer):

        gams_file = "tp_disc_pl.gms"
        model_name = "TP_DISC_PL"
        
        super().__init__(data, output_writer, gams_file, model_name)       
        
            
    def initialize_discretization_values(self):
        """Initializes the pool discretization in the tp-formulation."""
        
        UN_IN = self.instance_data.units_in
        WS = self.instance_data.water_sources        
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        PIPE_EXISTS = self.instance_data.pipe_exists
        J = self.algorithm_data.disc_indices

        START_SIZE_DISC = 1
        FRAC = {}
        SIZE = {}  
        CHI_MIP_START = {}

        # Determine initial discretization values 
        for pl in PL:
            SIZE[pl] = START_SIZE_DISC
            for j in J:
                if int(j) < START_SIZE_DISC:
                    FRAC[(pl, j)] = ONE / START_SIZE_DISC
                else:
                    FRAC[(pl, j)] = ZERO

                self.set_discretization_value("FRAC", (pl, j), FRAC[(pl, j)])

        # Remove unused discretization                
        for pl in PL:
            for j in J:
                if int(j) >= START_SIZE_DISC:
                    found_outgoing_pipe = False
                    for wd in WD:
                        if found_outgoing_pipe == False and PIPE_EXISTS[(pl, wd)]:
                            self.set_discretization_value("CHI.Fx", (pl, j, wd), ONE)
                            found_outgoing_pipe = True
                        else:
                            self.set_discretization_value("CHI.Fx", (pl, j, wd), ZERO)
                        for ws in WS:
                            self.set_discretization_value("FL_PR_DISC.Fx", (ws, pl, j, wd), ZERO)
                            
        # Remove unused variables   
        for ws in WS:
            for un_in in UN_IN:
                if not PIPE_EXISTS[(ws, un_in)]:
                    self.set_fixed_variable("FL.Fx", (ws, un_in), ZERO)

        for ws in WS:
            for pl in PL:
                for wd in WD:
                    if (not PIPE_EXISTS[(ws, pl)]) or (not PIPE_EXISTS[(pl, wd)]):
                        self.set_fixed_variable("FL_PR.Fx", (ws, pl, wd), ZERO)   
         
        for pl in PL:
            for wd in WD:
                if not PIPE_EXISTS[(pl, wd)]:
                    for j in J:
                        self.set_fixed_variable("CHI.Fx", (pl, j, wd), ZERO)
                        for ws in WS:     
                            self.set_fixed_variable("FL_PR_DISC.Fx", (ws, pl, j, wd), ZERO)                             

        self.algorithm_data.FRAC = FRAC
        self.algorithm_data.SIZE = SIZE
        self.algorithm_data.CHI_MIP_START = CHI_MIP_START  
        
        
    def adapt_discretization_values(self):
        """Adapts the pool discretization in the tp-formulation."""
        
        WS = self.instance_data.water_sources
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        PIPE_EXISTS = self.instance_data.pipe_exists
        J = self.algorithm_data.disc_indices
        SIZE_DISC = self.algorithm_data.disc_size
        feasibility_tolerance = self.algorithm_data.feasibility_tolerance
        integer_tolerance = self.algorithm_data.integer_tolerance
        solution_previous = self.gams_environment.job
        FRAC = self.algorithm_data.FRAC
        SIZE = self.algorithm_data.SIZE
        CHI_MIP_START = self.algorithm_data.CHI_MIP_START
        
        # Determine adapted discretization values
        for pl in PL:
            
            # Set values for MIP start 
            for j in J:
                for wd in WD:
                    chi_curr = solution_previous.out_db.get_variable("CHI").find_record((pl, j, wd)).level
                    if chi_curr >= ONE - integer_tolerance and int(j) < SIZE[pl]:
                        CHI_MIP_START[(pl, j, wd)] = ONE
                    else: 
                        CHI_MIP_START[(pl, j, wd)] = ZERO
            
            # Determine outlet flow of pool
            fl_out = ZERO 
            for j in J:
                for wd in WD:
                    chi_curr = solution_previous.out_db.get_variable("CHI").find_record((pl, j, wd)).level
                    if chi_curr >= ONE - integer_tolerance:
                        for ws in WS: 
                            fl_pr_disc_curr = solution_previous.out_db.get_variable("FL_PR_DISC").find_record((ws, pl, j, wd)).level
                            fl_out += fl_pr_disc_curr
            
            # Only adapt discretization if outlet flow is positive
            if fl_out > feasibility_tolerance:
                
                # Determine numbers of selected water demands
                num_selected = {}
                max_num_selected = 0
                wd_max_num_selected = None
                    
                for wd in WD:
                    num_selected[wd] = 0
                    for j in J:
                        chi_curr = solution_previous.out_db.get_variable("CHI").find_record((pl, j, wd)).level
                            
                        if chi_curr >= ONE - integer_tolerance:
                            fl_curr = ZERO
                            for ws in WS: 
                                fl_pr_disc_curr = solution_previous.out_db.get_variable("FL_PR_DISC").find_record((ws, pl, j, wd)).level
                                fl_curr += fl_pr_disc_curr
                            
                            if fl_curr > feasibility_tolerance:
                                num_selected[wd] += 1
                            
                    if num_selected[wd] > max_num_selected:
                        max_num_selected = num_selected[wd]
                        wd_max_num_selected = wd

                # Each water demand has been selected at most once -> increase size of discretization by 1
                if max_num_selected <= 1:
                    if SIZE[pl] < SIZE_DISC:
                        frac_max = ZERO
                        frac_max_index = None
                        
                        # Find greatest fraction
                        for j in J:
                            if FRAC[(pl, j)] > frac_max:
                                frac_max = FRAC[(pl, j)]
                                frac_max_index = j
                        
                        # Reduce the size of the greatest fraction        
                        FRAC[(pl, frac_max_index)] =  2.0 / 3.0 * frac_max
                        FRAC[(pl, str(SIZE[pl]))] = 1.0 / 3.0 * frac_max
    
                        # Adapt MIP start for water demand with greatest fraction
                        wd_selected = None
                        for wd in WD:
                            chi_curr = solution_previous.out_db.get_variable("CHI").find_record((pl, frac_max_index, wd)).level
                            if chi_curr >= ONE - integer_tolerance:
                                wd_selected = wd
                            
                        CHI_MIP_START[(pl, str(SIZE[pl]), wd_selected)] = ONE
                        SIZE[pl] += 1

                # At least one water demand has been selected twice -> keep size of discretization but change proportions
                elif max_num_selected >= 2:
                    
                    # Find greatest fraction
                    frac_max = ZERO
                    index_max = None
                    for j in J:
                        chi_curr = solution_previous.out_db.get_variable("CHI").find_record((pl, j, wd_max_num_selected)).level
                        if chi_curr >= ONE - integer_tolerance:
                            if FRAC[(pl, j)] > frac_max:
                                frac_max = FRAC[(pl, j)]
                                index_max = j                       
                    
                    # Find second greatest fraction            
                    frac_second_max = ZERO
                    index_second_max = None
                    for j in J:
                        chi_curr = solution_previous.out_db.get_variable("CHI").find_record((pl, j, wd_max_num_selected)).level
                        if chi_curr >= ONE - integer_tolerance:
                            if (j != index_max) and (FRAC[(pl, j)] > frac_second_max):
                                frac_second_max = FRAC[(pl, j)]
                                index_second_max = j  
                    
                    # Adapt fractions
                    FRAC[(pl, index_max)] = FRAC[(pl, index_max)] + 2.0 / 3.0 * FRAC[(pl, index_second_max)]
                    FRAC[(pl, index_second_max)] = 1.0 / 3.0 * FRAC[(pl, index_second_max)]                              
                        
                # Sort FRAC values in decreasing order
                FRAC_PL = {}
                for j in J:
                    FRAC_PL[j] = FRAC[(pl, j)]
                FRAC_PL_SORTED = sorted(FRAC_PL.items(), key=operator.itemgetter(1), reverse=True)
                
                # Store discretization values and corresponding MIP start
                CHI_MIP_START_PL_SORTED = {}
                for j in J:
                    j_sorted = FRAC_PL_SORTED[int(j)][0]
                    FRAC[(pl, j)] = FRAC_PL_SORTED[int(j)][1]  
                    for wd in WD:
                        CHI_MIP_START_PL_SORTED[(j, wd)] = CHI_MIP_START[(pl, j_sorted, wd)] 
                    
                for j in J:
                    for wd in WD:
                        CHI_MIP_START[(pl, j, wd)] = CHI_MIP_START_PL_SORTED[(j, wd)]
                
            # Set size of the discretization to one if the flow is 0        
            else:
                for j in J:
                    if int(j) == 0:
                        FRAC[(pl, j)] = ONE
                    else:
                        FRAC[(pl, j)] = ZERO

                SIZE[pl] = 1

        # Update discretization values and corresponding MIP start                    
        for pl in PL:
            for j in J:
                self.set_discretization_value("FRAC", (pl, j), FRAC[(pl, j)])
                if int(j) < SIZE[pl]:
                    for wd in WD:
                        self.set_starting_point_value("CHI.L", (pl, j, wd), CHI_MIP_START[(pl, j, wd)])
                
        # Remove unused discretization               
        for pl in PL:
            for j in J:
                if int(j) >= SIZE[pl]:
                    found_outgoing_pipe = False
                    for wd in WD:
                        if found_outgoing_pipe == False and PIPE_EXISTS[(pl, wd)]:
                            self.set_discretization_value("CHI.Fx", (pl, j, wd), ONE)
                            found_outgoing_pipe = True
                        else:
                            self.set_discretization_value("CHI.Fx", (pl, j, wd), ZERO)
                        for ws in WS:
                            self.set_discretization_value("FL_PR_DISC.Fx", (ws, pl, j, wd), ZERO)                                          


class PoolingProblemQCP(PoolingProblem):
    """Class for original QCP formulations of the Pooling Problem."""
    
    def __init__(self, data, output_writer, gams_file, model_name):
        
        model_type = "QCP"       
        name_GAMS_workspace = "gams_workspace_qcp"    
        
        super().__init__(data, output_writer, model_type, gams_file, model_name, name_GAMS_workspace)

        
class PQQCP(PoolingProblemQCP):
    """Class for pq-formulation of the Pooling Problem."""
    
    def __init__(self, data, output_writer):
        
        gams_file = "pq_formulation.gms"
        model_name = "PQ_FORMULATION"        
        
        super().__init__(data, output_writer, gams_file, model_name)
        
        
class TPQCP(PoolingProblemQCP):
    """Class for tp-formulation of the Pooling Problem."""
    
    def __init__(self, data, output_writer, gams_file):
        
        model_name = "TP_FORMULATION"        
        
        super().__init__(data, output_writer, gams_file, model_name)  
        

class TPQCPStandard(TPQCP):
    """Class for tp-formulation of the Pooling Problem with path flow variables."""
    
    def __init__(self, data, output_writer):
        
        gams_file = "tp_formulation.gms"
        
        super().__init__(data, output_writer, gams_file) 
        

class TPQCPNoPathFlows(TPQCP):
    """Class for tp-formulation of the Pooling Problem without path flow variables."""
    
    def __init__(self, data, output_writer):
        
        gams_file = "tp_formulation_no_pathflows.gms"
        
        super().__init__(data, output_writer, gams_file)                  
        

    """Sets the standard starting point with all values at zero."""
    def set_starting_point_zero(self):
        
        UN_IN = self.instance_data.units_in
        WS = self.instance_data.water_sources
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
                    
        self.initialize_starting_point()
        
        # Set flow variables  
        for ws in WS:
            for un_in in UN_IN:
                self.set_starting_point_value("FL.L", (ws, un_in), ZERO) 

        # Set proportion variables 
        for pl in PL:
            for wd in WD:
                self.set_starting_point_value("PR.L", (pl, wd), ZERO)
                    
        self.write_starting_point_to_file() 
        
    
    """Sets a random starting point with a given random seed."""
    def set_random_starting_point(self, seed):
        
        UN_IN = self.instance_data.units_in
        WS = self.instance_data.water_sources
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        FL_MAX = self.instance_data.fl_max
                    
        self.initialize_starting_point()
        
        # Set random seed
        random.seed(seed)
        
        # Set flow variables  
        for ws in WS:
            for un_in in UN_IN:
                self.set_starting_point_value("FL.L", (ws, un_in), FL_MAX[(ws, un_in)] * random.random()) 

        # Set proportion variables 
        for pl in PL:
            for wd in WD:
                self.set_starting_point_value("PR.L", (pl, wd), ONE * random.random())
                    
        self.write_starting_point_to_file()                    
        

class PoolingProblemChecker(PoolingProblem):
    """Class for original QCP formulations of the Pooling Problem with fixed variables."""
    
    def __init__(self, data, output_writer, solution, gams_file, model_name):
        
        model_type = "QCP"       
        name_GAMS_workspace = "gams_workspace_checker"    
        
        data.algorithm_data.is_active_checker = True
        
        super().__init__(data, output_writer, model_type, gams_file, model_name, name_GAMS_workspace)
        
        self.fix_flow_variables(solution)      
        
        
    def fix_flow_variables(self, solution):
        """Fixes all flow variables of the given solution."""
        
        self.initialize_fixed_variables()
        self.fix_flow_variable_values(solution)   
        self.finalize_fixed_variables()       
        
        
class PQChecker(PoolingProblemChecker):
    """Class for pq-formulation of the Pooling Problem with fixed variables."""
    
    def __init__(self, data, output_writer, solution):
        
        gams_file = "pq_formulation.gms"
        model_name = "PQ_CHECKER"        
        
        super().__init__(data, output_writer, solution, gams_file, model_name)    
        

    def fix_flow_variable_values(self, solution):
        """Fixes the flow variables to the values of the given solution."""
        
        formulation = self.algorithm_data.formulation
        algorithm = self.algorithm_data.algorithm
        UN_OUT = self.instance_data.units_out
        WS = self.instance_data.water_sources
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands

        if formulation == PQ_FORMULATION:    
            # Fix/set flow variables
            for un_out in UN_OUT:
                for wd in WD:
                    flow_curr = solution.out_db.get_variable("FL").find_record((un_out, wd)).level 
                    self.set_fixed_variable("FL.Fx", (un_out, wd), flow_curr)
                    
            for ws in WS:
                for pl in PL:
                    for wd in WD:
                        flow_pr_curr = solution.out_db.get_variable("FL_PR").find_record((ws, pl, wd)).level 
                        self.set_fixed_variable("FL_PR.Fx", (ws, pl, wd), flow_pr_curr) 
                        
            # Fix/set proportion variables
            for pl in PL:
                fl_out_pl = ZERO
                for wd in WD:
                    fl_out_pl += solution.out_db.get_variable("FL").find_record((pl, wd)).level
                
                if fl_out_pl > ZERO:
                    for ws in WS:
                        flow_in_curr = ZERO
                        for wd in WD:
                            flow_in_curr += solution.out_db.get_variable("FL_PR").find_record((ws, pl, wd)).level
                        pr_curr = flow_in_curr / fl_out_pl
                        self.set_fixed_variable("PR.Fx", (ws, pl), pr_curr)
                else:
                    for ws in WS:
                        if ws == WS[0]:
                            self.set_fixed_variable("PR.Fx", (ws, pl), ONE)
                        else:
                            self.set_fixed_variable("PR.Fx", (ws, pl), ZERO)                        
            
    
        elif formulation == TP_FORMULATION:    
            # Fix/set flow variables
            for ws in WS:
                for wd in WD:
                    flow_curr = solution.out_db.get_variable("FL").find_record((ws, wd)).level 
                    self.set_fixed_variable("FL.Fx", (ws, wd), flow_curr)
            
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
                    self.set_fixed_variable("FL.Fx", (pl, wd), flow_curr)
                    
            for ws in WS:                    
                for pl in PL:
                    for wd in WD:
                        if algorithm == QCP_SOLVER:
                            fl_curr = solution.out_db.get_variable("FL").find_record((ws, pl)).level
                            pr_curr = solution.out_db.get_variable("PR").find_record((pl, wd)).level
                            flow_pr_curr = fl_curr * pr_curr
                        else:
                            flow_pr_curr = solution.out_db.get_variable("FL_PR").find_record((ws, pl, wd)).level
                        self.set_fixed_variable("FL_PR.Fx", (ws, pl, wd), flow_pr_curr) 
                        
                        
            # Fix/set proportion variables
            for pl in PL:
                fl_in_pl = ZERO
                for ws in WS:
                    fl_in_pl += solution.out_db.get_variable("FL").find_record((ws, pl)).level
                
                if fl_in_pl > ZERO:
                    for ws in WS:
                        flow_in_curr = solution.out_db.get_variable("FL").find_record((ws, pl)).level
                        pr_curr = flow_in_curr / fl_in_pl
                        self.set_fixed_variable("PR.Fx", (ws, pl), pr_curr)
                else:
                    for ws in WS:
                        if ws == WS[0]:
                            self.set_fixed_variable("PR.Fx", (ws, pl), ONE)
                        else:
                            self.set_fixed_variable("PR.Fx", (ws, pl), ZERO)
            

class TPChecker(PoolingProblemChecker):
    """Class for tp-formulation of the Pooling Problem with fixed variables."""
    
    def __init__(self, data, output_writer, solution):
        
        gams_file = "tp_formulation.gms"
        model_name = "TP_CHECKER"         
        
        super().__init__(data, output_writer, solution, gams_file, model_name) 
        
        
    def fix_flow_variable_values(self, solution):
        """Fixes the flow variables to the values of the given solution."""
        
        formulation = self.algorithm_data.formulation
        UN_IN = self.instance_data.units_in
        WS = self.instance_data.water_sources
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands

        if formulation == PQ_FORMULATION:    
            # Fix/set flow variables
            for ws in WS:
                for wd in WD:
                    flow_curr = solution.out_db.get_variable("FL").find_record((ws, wd)).level 
                    self.set_fixed_variable("FL.Fx", (ws, wd), flow_curr)
            
            for ws in WS:
                for pl in PL:
                    flow_curr = ZERO
                    for wd in WD:
                        flow_curr += solution.out_db.get_variable("FL_PR").find_record((ws, pl, wd)).level 
                    self.set_fixed_variable("FL.Fx", (ws, pl), flow_curr)
            
    
        elif formulation == TP_FORMULATION:    
            # Fix/set flow variables
            for ws in WS:
                for un_in in UN_IN:
                    flow_curr = solution.out_db.get_variable("FL").find_record((ws, un_in)).level 
                    self.set_fixed_variable("FL.Fx", (ws, un_in), flow_curr)
            
        
                
