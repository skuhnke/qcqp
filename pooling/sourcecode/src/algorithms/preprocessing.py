'''
Created on Jul 16, 2019

@author: Sascha Kuhnke
'''
import copy
from gams.workspace import GamsExceptionExecution

from algorithms.gams_api import EnvironmentGAMSPreprocessing
from misc.misc import get_start_time, get_time_passed


# Constants
ONE = 1.0
ZERO = 0.0
INFINITY = float("inf")


class Preprocessing(object):
    """Class for LP preprocessing."""

    def __init__(self, data, output_writer):
        
        self.data = data
        self.instance_data = data.instance_data
        self.algorithm_data = data.algorithm_data
        self.output_writer = output_writer
        
        self.delete_water_demand = {}
        self.n_water_sources_deleted = 0
        self.n_pools_deleted = 0
        self.n_water_demands_deleted = 0
        self.n_constraints_deleted = 0    
        
        
    def perform_preprocessing(self):
        """Performs the LP preprocessing."""        
        
        if self.algorithm_data.evaluate_preprocessing:
            preprocessing_evaluator = PreprocessingEvaluator(self.data, self.output_writer)
        
        self.initialize_preprocessing()
        self.run_preprocessing()
        self.finish_preprocessing()
        
        if self.algorithm_data.evaluate_preprocessing:
            preprocessing_evaluator.evaluate_preprocessing(self.n_water_sources_deleted, self.n_pools_deleted, 
                                                           self.n_water_demands_deleted, self.n_constraints_deleted)
        
               
    def initialize_preprocessing(self):
        """Set up preprocessing environment."""
        
        self.time_start = get_start_time()
        
        # Set up GAMS environment
        model_type = "LP"
        model_name = "PREPROCESSING"   
        gms_file = "preprocessing.gms"        
        name_GAMS_workspace = "gams_workspace_preprocessing"
        
        self.gams_environment = EnvironmentGAMSPreprocessing(self.data, self.output_writer, model_type, model_name, gms_file, name_GAMS_workspace)

        
    def run_preprocessing(self):
        """Runs the LP preprocessing."""
        
        self.get_predecessors()
        self.determine_water_demands_to_be_deleted()
        self.preprocess_water_demands()
        self.preprocess_pools()
        self.preprocess_water_sources()        


    def finish_preprocessing(self):
        """Write preprocessing results into summary file."""
        
        time_required = get_time_passed(self.time_start)
        
        self.output_writer.write_summary_preprocessing(time_required, self.n_water_sources_deleted, self.n_pools_deleted, 
                                                       self.n_water_demands_deleted, self.n_constraints_deleted)

        
    def get_predecessors(self):
        """Get all predecessors of each output."""

        WS = self.instance_data.water_sources
        PL = self.instance_data.pools
        WD = self.instance_data.water_demands
        pipe_exists = self.instance_data.pipe_exists

        predecessors = {}
        
        for wd in WD:
            pred_curr = []
            
            # Add inputs directly connected to output.
            for ws in WS:
                if pipe_exists[(ws, wd)]:
                    pred_curr.append(ws)
                    
            # Add inputs connected via pool to output.
            for pl in PL:
                if pipe_exists[(pl, wd)]:
                    for ws in WS:
                        if pipe_exists[(ws, pl)]:
                            if ws not in pred_curr:
                                pred_curr.append(ws)
        
            predecessors[wd] = pred_curr
        
        self.predecessors = predecessors
        
        
    def determine_water_demands_to_be_deleted(self):
        """Determines all water demands that can be deleted by the preprocessing."""
        
        WD = self.instance_data.water_demands
        
        for wd in WD: 
            self.get_LP_data_for_water_demand(wd)
            self.solve_LP(wd)
            
            if not self.gams_environment.job_is_solved():
                self.delete_water_demand[wd] = True
            else:
                self.delete_water_demand[wd] = False        
        
        
    def get_LP_data_for_water_demand(self, water_demand):    
        """Get LP data for specific output."""
        
        WS = self.instance_data.water_sources
        CO = self.instance_data.contaminants
        PO_MIN_WD = self.instance_data.po_min_wd
        PO_MAX_WD = self.instance_data.po_max_wd
        predecessors_wd = self.predecessors[water_demand]
        
        for ws in WS:
            if ws in predecessors_wd:
                self.set_water_demand_parameter("IS_PRED", (ws, ), ONE)
            else:
                self.set_water_demand_parameter("IS_PRED", (ws, ), ZERO)
                
        for co in CO:
            self.set_water_demand_parameter("PO_MIN_WD", (co, ), PO_MIN_WD[(water_demand, co)])
            self.set_water_demand_parameter("PO_MAX_WD", (co, ), PO_MAX_WD[(water_demand, co)])
            
        
    def solve_LP(self, water_demand):
        """Solves LP corresponding to given water demand."""
        
        gams_workspace = self.gams_environment.gams_workspace
        checkpoint = self.gams_environment.checkpoint
        option_solver = self.gams_environment.option_solver
        model_name = self.gams_environment.model_name
        water_demand_data = self.gams_environment.water_demand_data
        
        time_limit_LP = 60.0
        
        options = self.gams_environment.get_options(time_limit_LP)
        job = gams_workspace.add_job_from_string(water_demand_data + options, checkpoint)
        log_file = self.output_writer.open_log_file_preprocessing(model_name, water_demand)
        
        try: 
            job.run(option_solver, output=log_file)
        except GamsExceptionExecution:
            pass
        
        self.output_writer.close_log_file(log_file)
        self.gams_environment.job = job

        
    def preprocess_water_demands(self):
        """Reduces the size of the problem by deleting water demands and specification requirement constraints 
        based on the preprocessing results."""
        
        units = self.instance_data.units
        units_in = self.instance_data.units_in
        water_demands = self.instance_data.water_demands
        WD = copy.deepcopy(water_demands)
        CO = self.instance_data.contaminants
        PO_WS = self.instance_data.po_ws
        PO_MIN_WD = self.instance_data.po_min_wd
        PO_MAX_WD = self.instance_data.po_max_wd 
        IS_ACTIVE_MIN = self.instance_data.is_active_min
        IS_ACTIVE_MAX = self.instance_data.is_active_max       
        predecessors = self.predecessors
        water_demands_to_be_deleted = self.delete_water_demand
        
        for wd in WD:
            predecessors_wd = predecessors[wd]
        
            # Remove water demand from data.
            if water_demands_to_be_deleted[wd]:
                units.remove(wd)
                units_in.remove(wd)
                water_demands.remove(wd)
                self.n_water_demands_deleted += 1
            
            # Remove redundant constraints.
            else:
                for co in CO:
                    po_min = INFINITY
                    po_max = ZERO
                    for ws in predecessors_wd:
                        if PO_WS[(ws, co)] < po_min:
                            po_min = PO_WS[(ws, co)]
                        if PO_WS[(ws, co)] > po_max:
                            po_max = PO_WS[(ws, co)]
                
                    if PO_MIN_WD[(wd, co)] <= po_min:
                        IS_ACTIVE_MIN[(wd, co)] = ZERO
                        self.n_constraints_deleted += 1
                    if PO_MAX_WD[(wd, co)] >= po_max:
                        IS_ACTIVE_MAX[(wd, co)] = ZERO                    
                        self.n_constraints_deleted += 1
                        
                        
    def preprocess_pools(self):
        """Reduces the size of the problem by deleting pools."""
        
        units = self.instance_data.units
        units_in = self.instance_data.units_in
        units_out = self.instance_data.units_out
        pools = self.instance_data.pools
        WS = self.instance_data.water_sources
        PL = copy.deepcopy(pools)
        WD = self.instance_data.water_demands
        pipe_exists = self.instance_data.pipe_exists
        
        for pl in PL:
            in_degree = 0
            out_degree = 0
            
            for ws in WS:
                if pipe_exists[(ws, pl)]:
                    in_degree += 1
                    
            for wd in WD:
                if pipe_exists[(pl, wd)]:
                    out_degree += 1
            
            # Remove pool from data.        
            if (in_degree == 0) or (out_degree == 0):
                units.remove(pl)
                units_in.remove(pl)
                units_out.remove(pl)
                pools.remove(pl)
                self.n_pools_deleted += 1
                
                
    def preprocess_water_sources(self):
        """Reduces the size of the problem by deleting water sources."""
        
        units = self.instance_data.units
        units_out = self.instance_data.units_out
        water_sources = self.instance_data.water_sources
        UN_IN = self.instance_data.units_in
        WS = copy.deepcopy(water_sources)
        pipe_exists = self.instance_data.pipe_exists
        
        for ws in WS:
            out_degree = 0
            
            for un_in in UN_IN:
                if pipe_exists[(ws, un_in)]:
                    out_degree += 1
                    
            # Remove water source from data.        
            if out_degree == 0:
                units.remove(ws)
                units_out.remove(ws)
                water_sources.remove(ws)
                self.n_water_sources_deleted += 1
                
                
    def set_water_demand_parameter(self, gams_variable, args, value):
        """Writes a line to the water demand data."""
        
        self.gams_environment.water_demand_data += self.gams_environment.set_gams_parameter(gams_variable, args, value)                
                
                
class PreprocessingEvaluator(object):
    """Class for evaluation of preprocessing."""

    def __init__(self, data, output_writer):
        
        self.data = data
        self.instance_data = data.instance_data
        self.output_writer = output_writer
        
        # Store the original instance data
        self.n_water_sources = len(self.instance_data.water_sources)
        self.n_pools = len(self.instance_data.pools)
        self.n_water_demands = len(self.instance_data.water_demands)
        self.n_spec_requirement_constraints = len(self.instance_data.water_demands) * len(self.instance_data.contaminants)
        
        self.n_arcs = 0
        for un_out in self.instance_data.units_out:
            for un_in in self.instance_data.units_in:
                if self.instance_data.pipe_exists[(un_out, un_in)]:
                    self.n_arcs += 1


    def evaluate_preprocessing(self, n_water_sources_deleted, n_pools_deleted, n_water_demands_deleted, n_constraints_deleted):
        """Stores the preprocessed instance data and writes all data into the results file."""
    
        n_arcs_pp = 0
        for un_out in self.instance_data.units_out:
            for un_in in self.instance_data.units_in:
                if self.instance_data.pipe_exists[(un_out, un_in)]:
                    n_arcs_pp += 1
        
        n_arcs_deleted = self.n_arcs - n_arcs_pp
                    
        self.output_writer.add_preprocessing_results(self.data, self.n_water_sources, self.n_pools, 
                                  self.n_water_demands, self.n_arcs, self.n_spec_requirement_constraints, n_water_sources_deleted, 
                                  n_pools_deleted, n_water_demands_deleted, n_arcs_deleted, n_constraints_deleted)
                    
