'''
Created on Jun 17, 2020

@author: Sascha Kuhnke
'''
import gams
import os

from algorithms import formulations
from data.data import AlgorithmData


# Constants
ONE = 1.0

# Algorithm data
IPOPT = AlgorithmData.IPOPT
SNOPT = AlgorithmData.SNOPT
MINOS = AlgorithmData.MINOS
BARON = AlgorithmData.BARON
SCIP = AlgorithmData.SCIP
GUROBI = AlgorithmData.GUROBI


class EnvironmentGAMS(object):
    """Basic class for the GAMS environment."""
    
    def __init__(self, data, output_writer, name_gams_workspace, gams_file, model_name, model_type):

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
    
        # Store the data in a GAMS database structure
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
        
        # Choose the solvers
        self.choose_solver()
        
        
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
        # Set QCP options
        elif self.model_type == "QCP":
            # Return BARON options
            if self.option_solver.qcp == "BARON": 
                self.options += "$onecho > baron.opt\n"
                self.options += "\tThreads " + str(1) + "\n"                
                self.options += "\tAbsConFeasTol " + str(feasibility_tolerance) + "\n"
                self.options += "$offecho\n\n"
            # Set SCIP options
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
            # Set IPOPT options
            elif self.option_solver.qcp == "IPOPT":
                self.options += "$onecho > ipopt.opt\n"
                self.options += "$offecho\n\n"
            # Set SNOPT options
            elif self.option_solver.qcp == "SNOPT":
                self.options += "$onecho > snopt.opt\n"
                self.options += "\tmajor feasibility tolerance " + str(feasibility_tolerance) + "\n"
                self.options += "\tminor feasibility tolerance " + str(feasibility_tolerance) + "\n"                
                self.options += "$offecho\n\n"
            # Set MINOS options
            elif self.option_solver.qcp == "MINOS":
                self.options += "$onecho > minos.opt\n"
                self.options += "\tfeasibility tolerance " + str(feasibility_tolerance) + "\n"
                self.options += "\trow tolerance " + str(feasibility_tolerance) + "\n"
                self.options += "$offecho\n\n"

    
    def get_solve_statement(self):
        """Returns solve statement for maximization in GAMS syntax."""
            
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
        

class EnvironmentGAMSOptimizationProblem(EnvironmentGAMS):
    """GAMS environment for optimization problems."""
    
    def __init__(self, optimization_problem, data, output_writer, name_gams_workspace, gams_file, model_name, model_type):

        self.optimization_problem = optimization_problem
        
        self.disc_data = ""
        self.fixed_variables = ""
        self.starting_point = ""

        super().__init__(data, output_writer, name_gams_workspace, gams_file, model_name, model_type)
        

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
        
        
    def write_data_to_gams_db(self):
        """Writes the instance data from Python data structures into a GAMS database."""
        
        gams_database = self.gams_database
        instance_data = self.instance_data
        algorithm_data = self.algorithm_data
        optimization_problem = self.optimization_problem
        
        variables = instance_data.variables
        constraints = instance_data.constraints
        constraints_eq = instance_data.constraints_eq
        constraints_ge = instance_data.constraints_ge
        constraints_le = instance_data.constraints_le
        
        coefficients_quad = instance_data.coefficients_quad
        coefficients = instance_data.coefficients
        rhs = instance_data.rhs
        coefficients_quad_objective = instance_data.coefficients_quad_objective
        coefficients_objective = instance_data.coefficients_objective
        bounds_lower = instance_data.lower_bounds
        bounds_upper = instance_data.upper_bounds
        feasibility_tolerance = algorithm_data.feasibility_tolerance
        feasibility_tolerance_checker = algorithm_data.feasibility_tolerance_checker
        
        # Sets
        db_i = gams_database.add_set("I", 1, "")
        db_k = gams_database.add_set("K", 1, "")
        db_k_eq = gams_database.add_set("K_EQ", 1, "")
        db_k_ge = gams_database.add_set("K_GE", 1, "")
        db_k_le = gams_database.add_set("K_LE", 1, "")
        
        for var in variables:
            db_i.add_record(var)
            
        for constr in constraints:
            db_k.add_record(constr)
            
        for constr_eq in constraints_eq:
            db_k_eq.add_record(constr_eq)            

        for constr_ge in constraints_ge:
            db_k_ge.add_record(constr_ge)
            
        for constr_le in constraints_le:
            db_k_le.add_record(constr_le)
        
        # Parameters
        if isinstance(optimization_problem, formulations.DiscretizedMIP):            
            db_coeff_quad = gams_database.add_parameter_dc("COEFF_QUAD", [db_k, db_i, db_i], "")
            for constr in constraints:
                for (var_a, var_b) in coefficients_quad[constr]:
                    # First variable in quadratic term has to be discretized -> switch if not the case
                    if var_a not in algorithm_data.disc_variables:
                        if (var_a, var_b) in instance_data.bilinear_terms:
                            instance_data.bilinear_terms.remove((var_a, var_b))
                        if (var_b, var_a) not in instance_data.bilinear_terms:
                            instance_data.bilinear_terms.append((var_b, var_a))
                        db_coeff_quad.add_record((constr, var_b, var_a)).value = coefficients_quad[constr][(var_a, var_b)]
                    else:
                        db_coeff_quad.add_record((constr, var_a, var_b)).value = coefficients_quad[constr][(var_a, var_b)]
                        
            db_coeff_quad_obj = gams_database.add_parameter_dc("COEFF_QUAD_OBJ", [db_i, db_i], "")
            for (var_a, var_b) in coefficients_quad_objective:
                # First variable in quadratic term has to be discretized -> switch if not the case
                if var_a not in algorithm_data.disc_variables:
                    if (var_a, var_b) in instance_data.bilinear_terms:
                        instance_data.bilinear_terms.remove((var_a, var_b))
                    if (var_b, var_a) not in instance_data.bilinear_terms:
                        instance_data.bilinear_terms.append((var_b, var_a))
                    db_coeff_quad_obj.add_record((var_b, var_a)).value = coefficients_quad_objective[(var_a, var_b)]
                else:
                    db_coeff_quad_obj.add_record((var_a, var_b)).value = coefficients_quad_objective[(var_a, var_b)] 
                    
        else:
            db_coeff_quad = gams_database.add_parameter_dc("COEFF_QUAD", [db_k, db_i, db_i], "")
            for constr in constraints:
                for (var_a, var_b) in coefficients_quad[constr]:
                    db_coeff_quad.add_record((constr, var_a, var_b)).value = coefficients_quad[constr][(var_a, var_b)] 
                    
            db_coeff_quad_obj = gams_database.add_parameter_dc("COEFF_QUAD_OBJ", [db_i, db_i], "")
            for (var_a, var_b) in coefficients_quad_objective:
                db_coeff_quad_obj.add_record((var_a, var_b)).value = coefficients_quad_objective[(var_a, var_b)]                                                      
    
        db_coeff = gams_database.add_parameter_dc("COEFF", [db_k, db_i], "")
        for constr in constraints:
            for var in coefficients[constr]:
                db_coeff.add_record((constr, var)).value = coefficients[constr][var]
                
        db_rhs = gams_database.add_parameter_dc("RHS", [db_k], "")
        for constr in constraints:
            db_rhs.add_record(constr).value = rhs[constr]
                
        db_coeff_obj = gams_database.add_parameter_dc("COEFF_OBJ", [db_i], "")
        for var in coefficients_objective:
            db_coeff_obj.add_record(var).value = coefficients_objective[var]

        db_bound_lo = gams_database.add_parameter_dc("BOUND_LO", [db_i], "")
        for var in variables:
            db_bound_lo.add_record(var).value = bounds_lower[var]
            
        db_bound_up = gams_database.add_parameter_dc("BOUND_UP", [db_i], "")
        for var in variables:
            db_bound_up.add_record(var).value = bounds_upper[var]            
                
        # Feasibility tolerance
        db_feas_tolerance = gams_database.add_parameter("FEAS_TOLERANCE", 0, "")
        db_feas_tolerance.add_record().value = feasibility_tolerance
        
        # Feasibility tolerance checker
        db_feas_tolerance_checker = gams_database.add_parameter("FEAS_TOLERANCE_CHECKER", 0, "")
        db_feas_tolerance_checker.add_record().value = feasibility_tolerance_checker
        
        # Discretization
        if isinstance(optimization_problem, formulations.DiscretizedMIP):
            disc_indices = algorithm_data.disc_indices
            disc_variables = algorithm_data.disc_variables
            bilinear_terms = instance_data.bilinear_terms
            squared_variables = instance_data.squared_variables
            
            db_i_disc = gams_database.add_set("I_DISC", 1, "")
            for var in disc_variables:
                db_i_disc.add_record(var) 
            
            db_n = gams_database.add_set("N", 1, "")
            for n in disc_indices:
                db_n.add_record(n)
            
            db_is_bilinear = gams_database.add_parameter_dc("IS_BILINEAR", [db_i, db_i], "")
            for (var_a, var_b) in bilinear_terms:
                db_is_bilinear.add_record((var_a, var_b)).value = ONE
                
            db_is_squared = gams_database.add_parameter_dc("IS_SQUARED", [db_i], "")
            for var in squared_variables:
                db_is_squared.add_record(var).value = ONE        
     
    
class EnvironmentGAMSVertexCover(EnvironmentGAMS):
    """GAMS environment for vertex cover."""
    
    def __init__(self, data, output_writer, name_gams_workspace, gams_file, model_name, model_type):

        self.fixed_variables = ""

        super().__init__(data, output_writer, name_gams_workspace, gams_file, model_name, model_type)


    def choose_solver(self):
        """Chooses the solver for the optimization problem."""

        self.option_solver = self.gams_workspace.add_options()
        self.option_solver.lp = "GUROBI"
        
    
    def write_data_to_gams_db(self):
        """Writes the instance data from Python data structures into a GAMS database."""
        
        gams_database = self.gams_database
        instance_data = self.instance_data
        algorithm_data = self.algorithm_data
        
        quadratic_terms = instance_data.quadratic_terms
        feasibility_tolerance = algorithm_data.feasibility_tolerance
        quadratic_variables = instance_data.quadratic_variables
        quadratic_diagonal_variables = instance_data.quadratic_diagonal_variables
        
        # Sets
        db_i = gams_database.add_set("I", 1, "")
        
        for var in quadratic_variables:
            db_i.add_record(var)


        # Fix strictly quadratic variables to 1
        for var in quadratic_diagonal_variables:
            self.fixed_variables += self.set_gams_parameter("VAR.Fx", var, ONE)        
            
        
        # Parameters
        db_edge = gams_database.add_parameter_dc("EDGE", [db_i, db_i], "")
        for (var_a, var_b) in quadratic_terms:
            db_edge.add_record((var_a, var_b)).value = ONE
                    
                    
        # Feasibility tolerance
        db_feas_tolerance = gams_database.add_parameter("FEAS_TOLERANCE", 0, "")
        db_feas_tolerance.add_record().value = feasibility_tolerance                    
    
