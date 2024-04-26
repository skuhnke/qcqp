'''
Created on Feb 12, 2019

@author: Sascha Kuhnke
'''
import gams
import os

from data.data import AlgorithmData


# Constants
ZERO = 0.0

# Algorithm data
IPOPT = AlgorithmData.IPOPT
SNOPT = AlgorithmData.SNOPT
MINOS = AlgorithmData.MINOS
BARON = AlgorithmData.BARON
SCIP = AlgorithmData.SCIP
GUROBI = AlgorithmData.GUROBI


class EnvironmentGAMS(object):
    """Basic class for the GAMS environment."""
    
    def __init__(self, data, output_writer, model_type, model_name, gams_file, name_gams_workspace):

        self.instance_data = data.instance_data
        self.algorithm_data = data.algorithm_data
        self.model_name = model_name
        self.model_type = model_type
        self.job = None
        
        # Create directory for GAMS workspace
        path_gams_workspace = output_writer.create_gams_workspace_folder(name_gams_workspace)        

        # Create GAMS workspace
        self.gams_workspace = gams.GamsWorkspace(working_directory=path_gams_workspace)
        self.gams_database = self.gams_workspace.add_database()
    
        # Store the data in a GAMS database structure.
        self.write_data_to_gams_db()
        self.gams_database.export("data")
        
        # Load the model
        self.checkpoint = self.gams_workspace.add_checkpoint()
        path_gams_file = os.path.join("../../../../../gams_models", gams_file)
        model = self.gams_workspace.add_job_from_file(path_gams_file)    
        
        # Create a GAMS checkpoint which contains the model including all input data.
        gams_instance_data = self.gams_workspace.add_options()
        gams_instance_data.defines["gdxincname"] = "data"
        model.run(gams_instance_data, checkpoint = self.checkpoint, databases = self.gams_database)   
        
        # Choose solver
        self.choose_solver()
        
        
    def choose_solver(self):
        """Chooses the solvers for the different optimization problems."""

        self.option_solver = self.gams_workspace.add_options()
        self.option_solver.lp = "GUROBI"
        self.option_solver.mip = "GUROBI"
        if self.algorithm_data.is_active_checker:
            self.option_solver.qcp = "BARON" 
        else:
            if self.algorithm_data.qcp_solver == BARON:
                self.option_solver.qcp = "BARON"
            elif self.algorithm_data.qcp_solver == SCIP:
                self.option_solver.qcp = "SCIP"
            elif self.algorithm_data.qcp_solver == GUROBI:
                self.option_solver.qcp = "GUROBI"                
            elif self.algorithm_data.qcp_solver == IPOPT:
                self.option_solver.qcp = "IPOPT"
            elif self.algorithm_data.qcp_solver == SNOPT:
                self.option_solver.qcp = "SNOPT"
            elif self.algorithm_data.qcp_solver == MINOS:
                self.option_solver.qcp = "MINOS"   
                
                
    def get_options(self, time_limit):
        """Returns all necessary options for the optimization."""
        
        self.options = ""
        self.get_time_limit_and_gap(time_limit)
        self.get_solver_options()
        self.get_solve_statement()
        
        return self.options    
    
    
    def get_time_limit_and_gap(self, time_limit):
        """Returns time limit and relative gap in GAMS syntax."""
        
        self.options += "OPTION RESLIM = " + str(time_limit) + ";\n" + "OPTION OPTCR = " + str(self.algorithm_data.gap) + ";\n\n" 


    def get_solver_options(self):
        """Generates the solver specific options."""

        feasibility_tolerance = self.algorithm_data.feasibility_tolerance
        integer_tolerance = self.algorithm_data.integer_tolerance
    
        # Set LP options
        if self.model_type == "LP":
            # Return CPLEX LP options
            if self.option_solver.lp == "CPLEX": 
                self.options += "$onecho > cplex.opt\n"
                self.options += "\tthreads " + str(1) + "\n"
                self.options += "\teprhs " + str(feasibility_tolerance) + "\n"
                self.options += "$offecho\n\n"
            # Return Gurobi LP options
            elif self.option_solver.lp == "GUROBI": 
                self.options += "$onecho > gurobi.opt\n"
                self.options += "\tthreads " + str(1) + "\n"
                self.options += "\tfeasibilitytol " + str(feasibility_tolerance) + "\n"
                self.options += "$offecho\n\n"
        # Set MIP options                
        elif self.model_type == "MIP":
            # Return CPLEX MIP options
            if self.option_solver.mip == "CPLEX": 
                self.options += "$onecho > cplex.opt\n"
                self.options += "\tthreads " + str(1) + "\n"
                self.options += "\teprhs " + str(feasibility_tolerance) + "\n"
                self.options += "\tepint " + str(integer_tolerance) + "\n"
                self.options += "\tmipstart 1\n"
                self.options += "\tsolvefinal 0\n"
                self.options += "$offecho\n\n"
            # Return Gurobi MIP options
            elif self.option_solver.mip == "GUROBI": 
                self.options += "$onecho > gurobi.opt\n"
                self.options += "\tthreads " + str(1) + "\n"
                self.options += "\tfeasibilitytol " + str(feasibility_tolerance) + "\n"
                self.options += "\tintfeastol " + str(integer_tolerance) + "\n"
                self.options += "\tmipstart 1\n"
                self.options += "$offecho\n\n"                
        # Return QCP options
        elif self.model_type == "QCP":
            # Return BARON options
            if self.option_solver.qcp == "BARON": 
                self.options += "$onecho > baron.opt\n"
                self.options += "\tThreads " + str(1) + "\n"                
                self.options += "\tAbsConFeasTol " + str(feasibility_tolerance) + "\n"
                self.options += "$offecho\n\n"
            # Return SCIP options
            elif self.option_solver.qcp == "SCIP": 
                self.options += "$onecho > scip.opt\n"
                self.options += "\tnumerics/feastol = " + str(feasibility_tolerance) + "\n"
                self.options += "\tdisplay/verblevel = 5\n"
                self.options += "$offecho\n\n"
            # Return Gurobi options
            elif self.option_solver.qcp == "GUROBI": 
                self.options += "$onecho > gurobi.opt\n"
                self.options += "\tthreads " + str(1) + "\n"                
                self.options += "\tfeasibilitytol = " + str(feasibility_tolerance) + "\n"
                self.options += "\tnonconvex " + str(2) + "\n"                
                self.options += "$offecho\n\n"                
            # Return IPOPT options
            elif self.option_solver.qcp == "IPOPT":
                self.options += "$onecho > ipopt.opt\n"
                self.options += "$offecho\n\n"
            # Return SNOPT options
            elif self.option_solver.qcp == "SNOPT":
                self.options += "$onecho > snopt.opt\n"
                self.options += "\tmajor feasibility tolerance " + str(feasibility_tolerance) + "\n"
                self.options += "\tminor feasibility tolerance " + str(feasibility_tolerance) + "\n"                
                self.options += "$offecho\n\n"
            # Return MINOS options
            elif self.option_solver.qcp == "MINOS":
                self.options += "$onecho > minos.opt\n"
                self.options += "\tfeasibility tolerance " + str(feasibility_tolerance) + "\n"
                self.options += "\trow tolerance " + str(feasibility_tolerance) + "\n"
                self.options += "$offecho\n\n"          
    

    def get_solve_statement(self):
        """Returns solve statement for a maximization in GAMS syntax."""
            
        self.options += ("SOLVE " + self.model_name + " USING " + self.model_type + " MAXIMIZING OBJ;\n" + 
                         "MODEL_STATUS = " + self.model_name + ".MODELSTAT;\n" + 
                         "SOLVE_STATUS = " + self.model_name + ".SOLVESTAT;\n" + 
                         "OBJEST = " + self.model_name + ".OBJEST;\n" + 
                         "OBJVAL = " + self.model_name + ".OBJVAL;\n\n")


    def get_solution(self):
        """Returns the solution of the current problem."""
         
        solution = None
     
        if self.job_is_solved():    
            solution = self.job
     
        return solution  


    def get_dual_bound(self, digits=2):
        """Returns the dual bound of the current problem."""
        
        dual_bound = round(float(self.job.out_db.get_parameter("OBJEST").find_record().value), digits)
        
        return dual_bound


    def get_objective_value(self, digits=2):
        """Returns the objective value of the current problem."""
        
        objective_value = None
    
        if self.job_is_solved():    
            objective_value = round(float(self.job.out_db.get_parameter("OBJVAL").find_record().value), digits)
    
        return objective_value
    
    
    def job_is_solved(self):
        """Checks if the problem is solved properly."""
        
        solved = False
        
        if self.job != None:
            model_status = int(self.job.out_db.get_parameter("MODEL_STATUS").find_record().value)
            
            if (model_status == 1) or (model_status == 2) or (model_status == 7) or (model_status == 8):
                solved = True
        
        return solved   
    
    
    def job_is_infeasible(self):
        """Checks if the problem is infeasible."""
         
        infeasible = False
         
        if self.job != None:
            model_status = int(self.job.out_db.get_parameter("MODEL_STATUS").find_record().value)
             
            if (model_status == 4) or (model_status == 10):
                infeasible = True
         
        return infeasible      


    def set_gams_parameter(self, parameter, args, value):
        """Returns given parameter with its value in GAMS syntax."""
                
        # Determine number of allowed decimal places.
        decimal_places = 0
        for number in range(16, 0, -1):
            if abs(value) < pow(10, 16 - number):
                decimal_places = number            
                break
                    
        gams_parameter = parameter
        
        # Change args to list with one element if only one string is given as argument.
        if isinstance(args, str):
            args = (args, )
        
        if len(args) > 0:
            gams_parameter += "("
            for i in range(len(args) - 1):
                gams_parameter += "'" + str(args[i]) + "', "
            gams_parameter += "'" + str(args[len(args) - 1]) + "')"
        gams_parameter += " = " + str(round(value, decimal_places)) + ";\n"
        
        return gams_parameter 
    

class EnvironmentGAMSPoolingProblem(EnvironmentGAMS):
    """GAMS environment for the Pooling Problem."""
   
    def __init__(self, data, output_writer, model_type, model_name, gms_file, name_gams_workspace):
        
        self.disc_data = ""
        self.fixed_variables = ""
        self.starting_point = ""
        
        super().__init__(data, output_writer, model_type, model_name, gms_file, name_gams_workspace)  


    def write_data_to_gams_db(self):
        """Writes the instance data from Python data structures into a GAMS database."""
        
        gams_database = self.gams_database
        instance_data = self.instance_data
        algorithm_data = self.algorithm_data
        
        UN = instance_data.units
        UN_OUT = instance_data.units_out
        UN_IN = instance_data.units_in
        WS = instance_data.water_sources
        PL = instance_data.pools
        WD = instance_data.water_demands
        CO = instance_data.contaminants
        
        FL_MAX_UN = instance_data.fl_max_un
        FL_MAX = instance_data.fl_max
        COST = instance_data.cost
        PO_WS = instance_data.po_ws
        PO_MIN_WD = instance_data.po_min_wd
        PO_MAX_WD = instance_data.po_max_wd
        
        IS_ACTIVE_MIN = instance_data.is_active_min
        IS_ACTIVE_MAX = instance_data.is_active_max
        
        J = algorithm_data.disc_indices
        feasibility_tolerance = algorithm_data.feasibility_tolerance
        feasibility_tolerance_checker = algorithm_data.feasibility_tolerance_checker
        
        # Sets
        db_units = gams_database.add_set("UN", 1, "")
        db_units_out = gams_database.add_set("UN_OUT", 1, "")
        db_units_in = gams_database.add_set("UN_IN", 1, "")
        db_water_sources = gams_database.add_set("WS", 1, "")
        db_pools = gams_database.add_set("PL", 1, "")
        db_water_demands = gams_database.add_set("WD", 1, "")
        db_contaminants = gams_database.add_set("CO", 1, "")
        
        for ws in WS:
            db_units.add_record(ws)
            db_units_out.add_record(ws)
            db_water_sources.add_record(ws)
            
        for pl in PL:
            db_units.add_record(pl)
            db_units_out.add_record(pl)
            db_units_in.add_record(pl)    
            db_pools.add_record(pl)    

        for wd in WD:
            db_units.add_record(wd)
            db_units_in.add_record(wd)
            db_water_demands.add_record(wd)

        for co in CO:
            db_contaminants.add_record(co)

        # Discretization
        db_j = gams_database.add_set("J", 1, "")
        for j in J:
            db_j.add_record(j)
        
        # General
        db_fl_max_un = gams_database.add_parameter_dc("FL_MAX_UN", [db_units], "")
        for un in UN:
            db_fl_max_un.add_record(un).value = FL_MAX_UN[un]
    
        db_fl_max = gams_database.add_parameter_dc("FL_MAX", [db_units_out, db_units_in], "")
        for un_out in UN_OUT:
            for un_in in UN_IN:
                db_fl_max.add_record((un_out, un_in)).value = FL_MAX[(un_out, un_in)]
                
        db_cost = gams_database.add_parameter_dc("COST", [db_units_out, db_units_in], "")
        for un_out in UN_OUT:
            for un_in in UN_IN:
                db_cost.add_record((un_out, un_in)).value = COST[(un_out, un_in)]
                
        # Water Sources
        db_po_ws = gams_database.add_parameter_dc("PO_WS", [db_water_sources, db_contaminants], "")
        for ws in WS:
            for co in CO:
                db_po_ws.add_record((ws, co)).value = PO_WS[(ws, co)]
                
        # Water Demands
        db_po_min_wd = gams_database.add_parameter_dc("PO_MIN_WD", [db_water_demands, db_contaminants], "")
        for wd in WD:
            for co in CO:
                db_po_min_wd.add_record((wd, co)).value = PO_MIN_WD[(wd, co)]
                
        db_po_max_wd = gams_database.add_parameter_dc("PO_MAX_WD", [db_water_demands, db_contaminants], "")
        for wd in WD:
            for co in CO:
                db_po_max_wd.add_record((wd, co)).value = PO_MAX_WD[(wd, co)]
                
        # Preprocessing
        db_is_active_min = gams_database.add_parameter_dc("IS_ACTIVE_MIN", [db_water_demands, db_contaminants], "")
        for wd in WD:
            for co in CO:
                db_is_active_min.add_record((wd, co)).value = IS_ACTIVE_MIN[(wd, co)]
        
        db_is_active_max = gams_database.add_parameter_dc("IS_ACTIVE_MAX", [db_water_demands, db_contaminants], "")
        for wd in WD:
            for co in CO:
                db_is_active_max.add_record((wd, co)).value = IS_ACTIVE_MAX[(wd, co)]        
                        
        # Feasiblity Tolerance
        db_feas_tolerance = gams_database.add_parameter("FEAS_TOLERANCE", 0, "")
        db_feas_tolerance.add_record().value = feasibility_tolerance
        
        db_feas_tolerance_checker = gams_database.add_parameter("FEAS_TOLERANCE_CHECKER", 0, "")
        db_feas_tolerance_checker.add_record().value = feasibility_tolerance_checker
        
     
class EnvironmentGAMSPreprocessing(EnvironmentGAMS):
    """GAMS environment for preprocessing."""
   
    def __init__(self, data, output_writer, model_type, model_name, gms_file, name_gams_workspace):
        
        self.water_demand_data = ""
        
        super().__init__(data, output_writer, model_type, model_name, gms_file, name_gams_workspace)        
        
        
    def write_data_to_gams_db(self):
        """Writes the necessary instance data from Python data structures into a GAMS database."""
        
        gams_database = self.gams_database
        instance_data = self.instance_data
        algorithm_data = self.algorithm_data
        
        WS = instance_data.water_sources
        CO = instance_data.contaminants
        PO_WS = instance_data.po_ws
        feasibility_tolerance = algorithm_data.feasibility_tolerance
        
        # Sets
        db_water_sources = gams_database.add_set("WS", 1, "")
        db_contaminants = gams_database.add_set("CO", 1, "")
        
        for ws in WS:
            db_water_sources.add_record(ws)

        for co in CO:
            db_contaminants.add_record(co)

        # Water Sources
        db_po_ws = gams_database.add_parameter_dc("PO_WS", [db_water_sources, db_contaminants], "")
        for ws in WS:
            for co in CO:
                db_po_ws.add_record((ws, co)).value = PO_WS[(ws, co)]
                
        # Feasibility Tolerance
        db_feas_tolerance = gams_database.add_parameter("FEAS_TOLERANCE", 0, "")
        db_feas_tolerance.add_record().value = feasibility_tolerance   
    
    
