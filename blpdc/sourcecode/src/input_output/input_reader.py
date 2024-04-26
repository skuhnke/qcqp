'''
Created on Jun 9, 2020

@author: Sascha Kuhnke
'''
import os
import pathlib
import sys

from data.data import InstanceData, AlgorithmData
from misc.exceptions import InputFormatException


# Constants
ONE = 1.0
ZERO = 0.0
INFINITY = float("inf")

# Objective sense
MIN = InstanceData.MIN
MAX = InstanceData.MAX

# Algorithm data
DISCRETIZATION = AlgorithmData.DISCRETIZATION


class InputReader():
    """Class to read the instance data from a file in .lp format."""
    
    def __init__(self, data):
        
        self.instance_data = data.instance_data
        self.algorithm_data = data.algorithm_data
        name_of_instance = data.instance_data.name
                
        # Change to the main working directory
        path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
        os.chdir(os.path.join(path_working_directory, "..", "..")) 
        
        self.path_of_instance = os.path.join("input", "instances", name_of_instance + ".lp")
        
        
    def read_input(self):
        """Reads the input file in .lp format and stores the data."""
        
        self.read_input_lp_file()
        self.add_remaining_data()
        
        
    def read_input_lp_file(self):
        """Reads the input from an .lp file."""
    
        lines = self.open_input_file()  
         
        # Set number of constraints
        num_line = 2    
        line_curr = lines[num_line].split()        
        self.instance_data.num_constraints = int(line_curr[1])
        self.instance_data.num_constraints_eq = int(line_curr[2])
        self.instance_data.num_constraints_ge = int(line_curr[3])
        self.instance_data.num_constraints_le = int(line_curr[4])

        if (self.instance_data.num_constraints != self.instance_data.num_constraints_eq + 
                            self.instance_data.num_constraints_ge + self.instance_data.num_constraints_le):
            self.raise_input_format_exception("line " + str(num_line + 1), "Number of constraints are inconsistent.")
            
        # Set number of variables            
        num_line += 5
        line_curr = lines[num_line].split()
        self.instance_data.num_variables = int(line_curr[1])
        num_var_cont = int(line_curr[2])
        
        if self.instance_data.num_variables != num_var_cont:
            self.raise_input_format_exception("line " + str(num_line + 1), "Number of variables are inconsistent.")    
        
        # Read objective function sense            
        num_line += 6
        num_line = self.get_next_line(lines, num_line)
        
        # Consider all problems as maximization problems -> Negate objective if necessary
        if lines[num_line].strip() == "Minimize":
            self.instance_data.objective_sense = MIN
            negate_objective = -1
        elif lines[num_line].strip() == "Maximize":
            self.instance_data.objective_sense = MAX
            negate_objective = 1
        else:
            self.raise_input_format_exception("line " + str(num_line + 1), "No objective sense is given.")
            
        # Read coefficients of objective function    
        num_line += 1
        num_line = self.get_next_line(lines, num_line)
        line_objective = []
        
        # Collect objective lines
        while lines[num_line].strip():
            line_objective += lines[num_line].split()
            num_line += 1
        
        # Remove first element 'obj'
        line_objective = line_objective[1:]
        
        sign = 1
        coefficient = 1
        section_quadratic = False
        first_variable = ""
        second_variable = ""
        
        # Process elements in objective
        for element in line_objective:
            if element == "+":
                sign = 1
            elif element == "-":
                sign = -1
            elif element == "[":
                section_quadratic = True
            elif element == "]":
                section_quadratic = False
            elif element == "]/2":
                section_quadratic = False
                for vars_quad in self.instance_data.coefficients_quad_objective:
                    self.instance_data.coefficients_quad_objective[vars_quad] /= 2                
            elif element == "*":
                if section_quadratic == False or first_variable == "":
                    self.raise_input_format_exception("objective", "Asterisk in wrong position.")    
            elif self.is_number(element):
                coefficient = float(element)
            else:
                # Add new variable
                if section_quadratic and (element[-2:] == "^2"): 
                    new_variable = element[:-2]
                else:
                    new_variable = element
                
                if new_variable not in self.instance_data.variables:
                    self.instance_data.variables.append(new_variable)  
                
                # Store corresponding coefficient                    
                if section_quadratic:
                    if element[-2:] == "^2":
                        first_variable = element[:-2]
                        second_variable = first_variable
                        
                        if coefficient != ZERO:
                            self.instance_data.coefficients_quad_objective[(first_variable, second_variable)] = negate_objective * sign * coefficient
                            self.add_variables_to_quadratic_variables_and_terms(first_variable, second_variable)
                        first_variable = ""
                        second_variable = ""
                        coefficient = 1
                    elif first_variable == "":
                        first_variable = element
                    else:
                        second_variable = element
                        
                        if coefficient != ZERO:
                            # Add the coefficient to the term in reverse order if it already exists.
                            if (second_variable, first_variable) in self.instance_data.coefficients_quad_objective:
                                self.instance_data.coefficients_quad_objective[(second_variable, first_variable)] += negate_objective * sign * coefficient
                            else:
                                self.instance_data.coefficients_quad_objective[(first_variable, second_variable)] = negate_objective * sign * coefficient
                                self.add_variables_to_quadratic_variables_and_terms(first_variable, second_variable)
                        first_variable = ""
                        second_variable = ""
                        coefficient = 1
                else:
                    if coefficient != ZERO:
                        self.instance_data.coefficients_objective[element] = negate_objective * sign * coefficient
                    coefficient = 1  
        
        # Read constraint section heading           
        num_line = self.get_next_line(lines, num_line)
        if lines[num_line].strip() != "Subject To":
            self.raise_input_format_exception("line " + str(num_line + 1), "No constraint section heading is given.")        
        
        # Read coefficients of constraints
        num_line += 1
        num_line = self.get_next_line(lines, num_line)
        while lines[num_line].strip() not in ["Bounds", "End"]:
            
            line_constraint = lines[num_line].split()
            num_line += 1
            
            # Collect constraint lines
            while lines[num_line].strip() and lines[num_line].split()[0][-1:] != ":":
                line_constraint += lines[num_line].split()
                num_line += 1
            
            num_line = self.get_next_line(lines, num_line)
            
            if line_constraint[0][-1:] != ":":
                self.raise_input_format_exception("line " + str(num_line + 1), "Wrong constraint format.") 
            name_constraint = line_constraint[0][:-1]
            
            # Remove name of constraint
            line_constraint = line_constraint[1:]             

            # Initialize coefficients of quadratic terms
            self.instance_data.coefficients_quad[name_constraint] = {}
            
            # Initialize coefficients of linear terms
            self.instance_data.coefficients[name_constraint] = {}
             
            sign = 1
            coefficient = 1
            section_rhs = False
            section_quadratic = False
            first_variable = ""
            second_variable = ""
            
            # Process elements in constraint 
            for element in line_constraint:
                if element == "+":
                    sign = 1
                elif element == "-":
                    sign = -1
                elif element == "=":
                    self.instance_data.constraints.append(name_constraint)
                    self.instance_data.constraints_eq.append(name_constraint)
                    section_rhs = True
                elif element == ">=":
                    self.instance_data.constraints.append(name_constraint)
                    self.instance_data.constraints_ge.append(name_constraint)
                    section_rhs = True
                elif element == "<=":
                    self.instance_data.constraints.append(name_constraint)
                    self.instance_data.constraints_le.append(name_constraint)                        
                    section_rhs = True
                elif element == "[":
                    section_quadratic = True
                elif element == "]":
                    section_quadratic = False
                elif element == "*":
                    if section_quadratic == False or first_variable == "":
                        self.raise_input_format_exception("equation " + name_constraint, "Asterisk in wrong position.")    
                elif self.is_number(element):
                    if section_rhs:
                        self.instance_data.rhs[name_constraint] = float(element)
                    else:
                        coefficient = float(element)
                else:
                    # Store coefficient corresponding to current variable
                    if section_quadratic:
                        if element[-2:] == "^2":
                            first_variable = element[:-2]
                            second_variable = first_variable
                            
                            if coefficient != ZERO:
                                self.instance_data.coefficients_quad[name_constraint][(first_variable, second_variable)] = sign * coefficient
                                self.add_variables_to_quadratic_variables_and_terms(first_variable, second_variable)
                            first_variable = ""
                            second_variable = ""
                            coefficient = 1
                        elif first_variable == "":
                            first_variable = element
                        else:
                            # Remove trailing closing bracket if present
                            if element[-1:] == "]":
                                element = element[:-1]
                                section_quadratic = False
                            second_variable = element
                           
                            if coefficient != ZERO: 
                                # Add the coefficient to the term in reverse order if it already exists.
                                if (second_variable, first_variable) in self.instance_data.coefficients_quad[name_constraint]:
                                    self.instance_data.coefficients_quad[name_constraint][(second_variable, first_variable)] += sign * coefficient
                                else:
                                    self.instance_data.coefficients_quad[name_constraint][(first_variable, second_variable)] = sign * coefficient
                                    self.add_variables_to_quadratic_variables_and_terms(first_variable, second_variable)
                            first_variable = ""
                            second_variable = ""
                            coefficient = 1
                    else:
                        if coefficient != ZERO:
                            self.instance_data.coefficients[name_constraint][element] = sign * coefficient
                        coefficient = 1
                        
            if section_rhs == False:
                self.raise_input_format_exception("line " + str(num_line + 1), "No right hand side of constraint is given.")  
            if section_quadratic == True:
                self.raise_input_format_exception("line " + str(num_line + 1), "Inconsistent section of quadratic terms.")
 
        self.instance_data.quadratic_non_squared_variables = ([var for var in self.instance_data.quadratic_variables 
                                                                if var not in self.instance_data.squared_variables])
       
        if len(self.instance_data.variables) != self.instance_data.num_variables:
            self.raise_input_format_exception("number of variables", "Number in Header and number of variables do not match.")
        if len(self.instance_data.constraints_eq) != self.instance_data.num_constraints_eq:
            self.raise_input_format_exception("number of equation constraints", "Number in Header and number of constraints do not match.") 
        if len(self.instance_data.constraints_ge) != self.instance_data.num_constraints_ge:
            self.raise_input_format_exception("number of greater or equal constraints", "Number in Header and number of constraints do not match.")
        if len(self.instance_data.constraints_le) != self.instance_data.num_constraints_le:
            self.raise_input_format_exception("number of less or equal constraints", "Number in Header and number of constraints do not match.")            

        # Set default bounds
        for variable in self.instance_data.variables:
            self.instance_data.lower_bounds[variable] = ZERO
            self.instance_data.upper_bounds[variable] = INFINITY    
               
        # Read bound section heading           
        num_line = self.get_next_line(lines, num_line)
        if lines[num_line].strip() == "Bounds":

            # Read lower and upper bounds
            num_line += 1
            error_in_bound_section = False
            
            while lines[num_line].strip():
                line_curr = lines[num_line].split()
    
                # Lower and upper bound
                if len(line_curr) == 5:
                    if line_curr[2] in self.instance_data.variables:
                        variable = line_curr[2]
                        if line_curr[1] != "<=" or line_curr[3] != "<=":
                            error_in_bound_section = True
                        if self.is_number(line_curr[0]):
                            lower_bound = float(line_curr[0])
                            self.instance_data.lower_bounds[variable] = lower_bound
                        elif line_curr[0] == "-inf":
                            self.instance_data.lower_bounds[variable] = -INFINITY
                        else:
                            error_in_bound_section = True 
                        if self.is_number(line_curr[4]):
                            upper_bound = float(line_curr[4])
                            self.instance_data.upper_bounds[variable] = upper_bound
                        elif line_curr[4] == "inf":
                            self.instance_data.upper_bounds[variable] = INFINITY                               
                        else:
                            error_in_bound_section = True                                             
                    else:
                        error_in_bound_section = True                    
                        
                # Single lower or single upper bound or fixed variables
                elif len(line_curr) == 3:
                    # Upper bound
                    if line_curr[0] in self.instance_data.variables:
                        variable = line_curr[0]
                        if line_curr[1] == "<=":
                            self.instance_data.lower_bounds[variable] = ZERO
                            if self.is_number(line_curr[2]):
                                upper_bound = float(line_curr[2])
                                self.instance_data.upper_bounds[variable] = upper_bound
                            elif line_curr[2] == "inf":
                                self.instance_data.upper_bounds[variable] = INFINITY                            
                            else:
                                error_in_bound_section = True
                        elif line_curr[1] == "=":
                            if self.is_number(line_curr[2]):
                                fixed_value = float(line_curr[2])
                                self.instance_data.lower_bounds[variable] = fixed_value
                                self.instance_data.upper_bounds[variable] = fixed_value
                            else:
                                error_in_bound_section = True                            
                        else:
                            error_in_bound_section = True
                    # Lower bound
                    elif line_curr[2] in self.instance_data.variables:
                        variable = line_curr[2]
                        self.instance_data.upper_bounds[variable] = INFINITY
                        if line_curr[1] != "<=":
                            error_in_bound_section = True
                        if self.is_number(line_curr[0]):
                            lower_bound = float(line_curr[0])
                            self.instance_data.lower_bounds[variable] = lower_bound
                        elif line_curr[0] == "-inf":
                            self.instance_data.lower_bounds[variable] = -INFINITY                            
                        else:
                            error_in_bound_section = True
                    else:
                        error_in_bound_section = True
                
                # Free variables        
                elif len(line_curr) == 2:
                    if line_curr[0] in self.instance_data.variables:
                        variable = line_curr[0]
                        if line_curr[1] == "Free":
                            self.instance_data.lower_bounds[variable] = -INFINITY
                            self.instance_data.upper_bounds[variable] = INFINITY
                        else:
                            error_in_bound_section = True
                    else:
                        error_in_bound_section = True                    
                else:
                    error_in_bound_section = True
            
                if error_in_bound_section:
                    self.raise_input_format_exception("line " + str(num_line + 1), "Bounds are inconsistent.")
    
                num_line += 1
            
        # Read end of file
        num_line = self.get_next_line(lines, num_line)
        if lines[num_line].strip() != "End":
            self.raise_input_format_exception("line " + str(num_line + 1), "No end of file symbol.")
        
    
    def add_remaining_data(self):
        """Adds remaining data that has to be calculated from the input data."""
        
        disc_size = self.algorithm_data.disc_size
        algorithm = self.algorithm_data.algorithm

        # Add indices of discretization        
        if algorithm == DISCRETIZATION:
            self.algorithm_data.disc_indices = []
            for n in range(disc_size):
                self.algorithm_data.disc_indices.append(str(n))

    
    def add_variables_to_quadratic_variables_and_terms(self, first_variable, second_variable):
        """Adds the two variables to the corresponding sets containing the quadratic variables and terms."""
        
        if first_variable not in self.instance_data.quadratic_variables:
            self.instance_data.quadratic_variables.append(first_variable)
        if second_variable not in self.instance_data.quadratic_variables:    
            self.instance_data.quadratic_variables.append(second_variable)
        if first_variable == second_variable:
            if first_variable not in self.instance_data.squared_variables:
                self.instance_data.squared_variables.append(first_variable)                                    
        else:
            if (first_variable, second_variable) not in self.instance_data.bilinear_terms:                            
                self.instance_data.bilinear_terms.append((first_variable, second_variable))

            
    def open_input_file(self):
        """Tries to open the input file and raises an exception otherwise."""
        
        try:
            with open(self.path_of_instance, 'r') as input_file:
                return input_file.readlines()
        except EnvironmentError:
            print("Cannot not open instance file.")
            sys.exit()
            
        
    def raise_input_format_exception(self, position, message):
        """Raises an input format exception with information about the line of the error and the error type."""
        
        try:
            raise InputFormatException("Error in input file. Wrong input format in " + position + ". " + message)
        except InputFormatException as exception:
            print(exception)
            sys.exit()  
            
            
    def get_next_line(self, lines, num_line):
        """Returns the number of the next non-empty line."""

        while not lines[num_line].strip():
            num_line += 1
        return num_line
    
        
    def is_number(self, element):
        """Returns true if element is an integer or a float."""
        
        # Remove minus
        if element[0] == "-":
            element = element[1:]

        # Remove dot   
        element = element.replace('.','',1) 
        
        # Remove scientific writing   
        element = element.replace('e-','',1) 
           
        return element.isdigit()
        
