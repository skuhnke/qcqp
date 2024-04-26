'''
Created on Sep 8, 2020

@author: Sascha Kuhnke
'''
import os
import sys

from data.data import Data
from input_output.input_reader import InputReader
from input_output.output_writer import OutputWriter
from algorithms.preprocessing import Preprocessing



def convert_tp_formulation_to_lp_format(data, use_original_names=False):
    """Writes a Pooling instance in tp-formulation into .lp format."""
    
    instance_data = data.instance_data
    
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

    path_output = os.path.join("output", "instances_lp_format")  
    if not os.path.exists(path_output):
        os.makedirs(path_output)  
    path_lp_instance = os.path.join(path_output, instance_data.name + ".lp")
    lp_instance_file = open(path_lp_instance, 'w')
    
    num_variables = len(WS) * len(UN_IN) + len(WS) * len(PL) * len(WD) + len(PL) * len(WD)
    num_equations_eq = 0
    num_equations_ge = 0
    num_equations_le = 0
    
    
    FL = {}
    FL_PR = {}
    PR = {}
    
    if use_original_names:
        for ws in WS:
            for un_in in UN_IN:
                FL[(ws, un_in)] = "fl_" + ws + "_" + un_in 
                
        for ws in WS:
            for pl in PL:
                for wd in WD:
                    FL_PR[(ws, pl, wd)] = "fl_pr_" + ws + "_" + pl + "_" + wd
        
        for pl in PL:
            for wd in WD:
                PR[(pl, wd)] = "pr_" + pl + "_" + wd
    else:
        n_variable = 1 
        n_constraint = 2
        
        for ws in WS:
            for un_in in UN_IN:
                FL[(ws, un_in)] = "x_" + str(n_variable)
                n_variable += 1 
                
        for ws in WS:
            for pl in PL:
                for wd in WD:
                    FL_PR[(ws, pl, wd)] = "x_" + str(n_variable)
                    n_variable += 1 
        
        for pl in PL:
            for wd in WD:
                PR[(pl, wd)] = "x_" + str(n_variable)
                n_variable += 1
    
    
    string_constraints = "Subject To\n"
    for ws in WS:
        num_equations_le += 1
        
        if use_original_names:
            name_constraint = " GE_FL_MAX_WS_" + ws
        else:
            name_constraint = " e" + str(n_constraint)
            n_constraint += 1
        string_constraints += name_constraint + ": "
        for un_in in UN_IN:
            string_constraints += FL[(ws, un_in)] + " + "
        string_constraints = string_constraints[0:-2]
        string_constraints += "<= " + str(FL_MAX_UN[ws]) + "\n"
    
    for pl in PL:
        num_equations_le += 1
        
        if use_original_names:
            name_constraint = " GE_FL_MAX_PL_" + pl
        else:
            name_constraint = " e" + str(n_constraint)
            n_constraint += 1
        string_constraints += name_constraint + ": "
        for ws in WS:
            string_constraints += FL[(ws, pl)] + " + "
        string_constraints = string_constraints[0:-2]
        string_constraints += "<= " + str(FL_MAX_UN[pl]) + "\n" 
        
    for wd in WD:
        num_equations_le += 1
        
        if use_original_names:
            name_constraint = " GE_FL_MAX_WD_" + wd
        else:
            name_constraint = " e" + str(n_constraint)
            n_constraint += 1
        string_constraints += name_constraint + ": "
        for ws in WS:
            string_constraints += FL[(ws, wd)] + " + "
        for ws in WS:
            for pl in PL:
                string_constraints += FL_PR[(ws, pl, wd)] + " + "
        string_constraints = string_constraints[0:-2]
        string_constraints += "<= " + str(FL_MAX_UN[wd]) + "\n" 
        
    # GE_FL_MAX_PI is covered in the bounds section    
        
    for pl in PL:
        for wd in WD:
            num_equations_le += 1
            
            if use_original_names:
                name_constraint = " GE_FL_MAX_PI_PR_" + pl + "_" + wd
            else:
                name_constraint = " e" + str(n_constraint)
                n_constraint += 1
            string_constraints += name_constraint + ": "
            for ws in WS:
                string_constraints += FL_PR[(ws, pl, wd)] + " + "
            string_constraints = string_constraints[0:-2]
            string_constraints += "<= " + str(FL_MAX[(pl, wd)]) + "\n"  

    for pl in PL:
        num_equations_eq += 1
            
        if use_original_names:
            name_constraint = " TP_PR_BALANCE_" + pl
        else:
            name_constraint = " e" + str(n_constraint)
            n_constraint += 1            
        string_constraints += name_constraint + ": "
        for wd in WD:
            string_constraints += PR[(pl, wd)] + " + "
        string_constraints = string_constraints[0:-2]
        string_constraints += "= " + str(1.0) + "\n"             

    for ws in WS:
        for pl in PL:
            for wd in WD:
                num_equations_eq += 1
                    
                if use_original_names:
                    name_constraint = " TP_FL_PR_" + ws + "_" + pl + "_" + wd
                else:
                    name_constraint = " e" + str(n_constraint)
                    n_constraint += 1                       
                string_constraints += name_constraint + ": "
                string_constraints += FL_PR[(ws, pl, wd)] + " " 
                string_constraints += "- [ " + FL[(ws, pl)] + " * " + PR[(pl, wd)] + " ] " 
                string_constraints += "= " + str(0.0) + "\n"   
        
    for wd in WD:
        for co in CO:
            if IS_ACTIVE_MIN[(wd, co)]:
                num_equations_ge += 1
                
                if use_original_names:
                    name_constraint = " TP_PO_MIN_WD_" + wd + "_" + co
                else:
                    name_constraint = " e" + str(n_constraint)
                    n_constraint += 1  
                string_constraints += name_constraint + ":"
                for ws in WS:
                    if PO_WS[(ws, co)] - PO_MIN_WD[(wd, co)] < 0:
                        coefficient = " - " + str(-1 * (PO_WS[(ws, co)] - PO_MIN_WD[(wd, co)]))
                    else:
                        coefficient = " + " + str(PO_WS[(ws, co)] - PO_MIN_WD[(wd, co)])
                    string_constraints += coefficient + " " + FL[(ws, wd)]
                for ws in WS:
                    for pl in PL:
                        if PO_WS[(ws, co)] - PO_MIN_WD[(wd, co)] < 0:
                            coefficient = " - " + str(-1 * (PO_WS[(ws, co)] - PO_MIN_WD[(wd, co)]))
                        else:
                            coefficient = " + " + str(PO_WS[(ws, co)] - PO_MIN_WD[(wd, co)])                        
                        string_constraints += coefficient + " " + FL_PR[(ws, pl, wd)]
                string_constraints += " >= " + str(0.0) + "\n" 
                
    for wd in WD:
        for co in CO:
            if IS_ACTIVE_MAX[(wd, co)]:
                num_equations_le += 1
                
                if use_original_names:
                    name_constraint = " TP_PO_MAX_WD_" + wd + "_" + co
                else:
                    name_constraint = " e" + str(n_constraint)
                    n_constraint += 1  
                string_constraints += name_constraint + ":"
                for ws in WS:
                    if PO_WS[(ws, co)] - PO_MAX_WD[(wd, co)] < 0:
                        coefficient = " - " + str(-1 * (PO_WS[(ws, co)] - PO_MAX_WD[(wd, co)]))
                    else:
                        coefficient = " + " + str(PO_WS[(ws, co)] - PO_MAX_WD[(wd, co)])                    
                    string_constraints += coefficient + " " + FL[(ws, wd)]
                for ws in WS:
                    for pl in PL:
                        if PO_WS[(ws, co)] - PO_MAX_WD[(wd, co)] < 0:
                            coefficient = " - " + str(-1 * (PO_WS[(ws, co)] - PO_MAX_WD[(wd, co)]))
                        else:
                            coefficient = " + " + str(PO_WS[(ws, co)] - PO_MAX_WD[(wd, co)])                         
                        string_constraints += coefficient + " " + FL_PR[(ws, pl, wd)]
                string_constraints += " <= " + str(0.0) + "\n"                

    for ws in WS:
        for pl in PL:
            num_equations_eq += 1
              
            if use_original_names:
                name_constraint = " TP_VALID_1_" + ws + "_" + pl
            else:
                name_constraint = " e" + str(n_constraint)
                n_constraint += 1    
            string_constraints += name_constraint + ": "
            for wd in WD:
                string_constraints += FL_PR[(ws, pl, wd)] + " + "
            string_constraints = string_constraints[0:-2]
            string_constraints += "- " + FL[(ws, pl)] + " "
            string_constraints += "= " + str(0.0) + "\n"

    for pl in PL:
        for wd in WD:
            num_equations_le += 1
                
            if use_original_names:
                name_constraint = " TP_VALID_2_" + pl + "_" + wd
            else:
                name_constraint = " e" + str(n_constraint)
                n_constraint += 1    
            string_constraints += name_constraint + ": "
            for ws in WS:
                string_constraints += FL_PR[(ws, pl, wd)] + " + "
            string_constraints = string_constraints[0:-2]
            string_constraints += "- " + str(FL_MAX_UN[pl]) + " " + PR[(pl, wd)] + " "
            string_constraints += "<= " + str(0.0) + "\n"

    
    string_objective = "Maximize\n"
    string_objective += " obj:"
    for ws in WS:
        for wd in WD:
            if COST[(ws, wd)] < 0:
                coefficient = " - " + str(-1 * COST[(ws, wd)])
            else:
                coefficient = " + " + str(COST[(ws, wd)])             
            string_objective += coefficient + " " + FL[(ws, wd)]
    for ws in WS:
        for pl in PL:
            for wd in WD:
                if COST[(ws, pl)] + COST[(pl, wd)] < 0:
                    coefficient = " - " + str(-1 * (COST[(ws, pl)] + COST[(pl, wd)]))
                else:
                    coefficient = " + " + str(COST[(ws, pl)] + COST[(pl, wd)])                    
                string_objective += coefficient + " " + FL_PR[(ws, pl, wd)]
    string_objective += " + "
    for ws in WS:
        for pl in PL:
            string_objective += str(0.0) + " " + FL[(ws, pl)] + " + "
    for pl in PL:
        for wd in WD:
            string_objective += str(0.0) + " " + PR[(pl, wd)] + " + "
    string_objective = string_objective[0:-2]


    string_bounds = "Bounds\n"
    for ws in WS:
        for un_in in UN_IN:
            string_bounds += " " + FL[(ws, un_in)] + " <= " + str(FL_MAX[(ws, un_in)]) + "\n"
    for pl in PL:
        for wd in WD:
            string_bounds += " " + PR[(pl, wd)] + " <= " + str(1.0) + "\n"
    # These bounds are already implicitly defined, but required by the local solver starting points
    for ws in WS:
        for pl in PL:
            for wd in WD:
                string_bounds += " " + FL_PR[(ws, pl, wd)] + " <= " + str(min(FL_MAX[(ws, pl)], FL_MAX[(pl, wd)])) + "\n"       
            

    lp_instance_file.write("\ Equation counts\n")
    lp_instance_file.write("\     Total        E        G        L        N        X        C        B\n")
    lp_instance_file.write("\\\t" + str(num_equations_eq + num_equations_le + num_equations_ge) + "\t" + str(num_equations_eq) + "\t" + str(num_equations_ge) + "\t" + str(num_equations_le) + "\n")                    
    lp_instance_file.write("\\\n") 
    lp_instance_file.write("\ Variable counts\n")
    lp_instance_file.write("\                  x        b        i      s1s      s2s       sc       si\n")
    lp_instance_file.write("\     Total     cont   binary  integer     sos1     sos2    scont     sint\n")
    lp_instance_file.write("\\\t" + str(num_variables) + "\t" + str(num_variables) + "\n")
    lp_instance_file.write("\n")
    lp_instance_file.write("\ Nonzero counts\n")
    lp_instance_file.write("\     Total    const       NL      DLL\n")
    lp_instance_file.write("\\\n")
    lp_instance_file.write("\\\n")
    lp_instance_file.write(string_objective)
    lp_instance_file.write("\n\n")
    lp_instance_file.write(string_constraints)
    lp_instance_file.write("\n")
    lp_instance_file.write(string_bounds)
    lp_instance_file.write("\n")    
    lp_instance_file.write("End")
    lp_instance_file.close()


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
    
    # Perform preprocessing
    Preprocessing(data, output_writer).perform_preprocessing()
    
    convert_tp_formulation_to_lp_format(data)

