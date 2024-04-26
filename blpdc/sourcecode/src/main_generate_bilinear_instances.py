'''
Created on Nov 19, 2020

@author: Sascha Kuhnke
'''

from gams.workspace import GamsExceptionExecution
import math
import os
import pathlib
import random
import numpy

from main_generate_lp_bounds import get_data, BoundTightener
from algorithms.gams_api import EnvironmentGAMS         


# Constants
ONE = 1.0
ZERO = 0.0


class BilinearProgram(object):
    """Represents a bilinear program based on several kernel programs."""

    NUM_TOLERANCE = pow(10, -10)

    def __init__(self, kappa_1, kappa_2, delta, rho, denominator_householder_vector):

        # Global parameters
        self.kappa_1 = kappa_1
        self.kappa_2 = kappa_2
        self.delta = delta
        self.rho = rho
        self.denominator_householder_vector = denominator_householder_vector

        # Original problem
        self.variables_x = []
        self.variables_y = []
        self.c = None
        self.d = None
        self.Q = None
        self.A = None
        self.a = None
        self.B = None
        self.b = None
        
        # Transformed problem
        self.c_transformed = None
        self.d_transformed = None
        self.Q_transformed = None
        self.A_transformed = None
        self.B_transformed = None
        
        # Transformation parameters
        self.n_x = 2 * self.kappa_2
        self.n_y = self.kappa_1 + self.kappa_2
        self.H_x = None
        self.H_y = None
        self.D_x = None
        self.D_y = None
        self.M_x = None
        self.M_y = None
        self.W_x = None
        self.W_y = None
        
        self.generate_bilinear_program()
        self.generate_transformation_matrices()
        self.transform_bilinear_program()
        

    def generate_bilinear_program(self):
        """Initializes the data for the bilinear program."""
    
        # Iterate through all kernel programs 1.
        for i in range(self.kappa_1):
            kernel_program_1 = KernelProgram1(i + 1, self.delta, self.rho)
            
            # Append variables, constraints, and objective to the bilinear program.
            self.variables_x.extend(kernel_program_1.variables_x)
            self.variables_y.extend(kernel_program_1.variables_y)

            self.c = self.concatenate_matrices(self.c, kernel_program_1.c)
            self.d = self.concatenate_matrices(self.d, kernel_program_1.d)
            self.Q = self.concatenate_diagonal_matrices(self.Q, kernel_program_1.Q)
            self.A = self.concatenate_diagonal_matrices(self.A, kernel_program_1.A)
            self.a = self.concatenate_matrices(self.a, kernel_program_1.a)
            self.B = self.concatenate_diagonal_matrices(self.B, kernel_program_1.B)
            self.b = self.concatenate_matrices(self.b, kernel_program_1.b)
            
        
        # Iterate through all kernel programs 2.    
        for i in range(self.kappa_1, self.kappa_2):
            kernel_program_2 = KernelProgram2(i + 1)
            
            # Append variables, constraints, and objective to the bilinear program.
            self.variables_x.extend(kernel_program_2.variables_x)
            self.variables_y.extend(kernel_program_2.variables_y)
            
            self.c = self.concatenate_matrices(self.c, kernel_program_2.c)
            self.d = self.concatenate_matrices(self.d, kernel_program_2.d)
            self.Q = self.concatenate_diagonal_matrices(self.Q, kernel_program_2.Q)
            self.A = self.concatenate_diagonal_matrices(self.A, kernel_program_2.A)
            self.a = self.concatenate_matrices(self.a, kernel_program_2.a)
            self.B = self.concatenate_diagonal_matrices(self.B, kernel_program_2.B)
            self.b = self.concatenate_matrices(self.b, kernel_program_2.b)
            
            
    def concatenate_matrices(self, matrix_a, matrix_b):
        """Concatenate the two matrices."""
        
        if matrix_a is None:
            matrix = matrix_b
        else:
            matrix = numpy.concatenate((matrix_a, matrix_b))

        return matrix 
    
    
    def concatenate_diagonal_matrices(self, matrix_a, matrix_b):
        """Concatenate the two diagonal matrices."""
        
        if matrix_a is None:
            matrix = matrix_b
        else:
            zeros_left = numpy.zeros((matrix_b.shape[0], matrix_a.shape[1]))
            zeros_right = numpy.zeros((matrix_a.shape[0], matrix_b.shape[1]))
            matrix = numpy.asarray(numpy.bmat([[matrix_a, zeros_right], [zeros_left, matrix_b]]))
            
        return matrix 

            
    def generate_transformation_matrices(self):
        """Generates two transformation matrices based on Householder and positive diagonal matrices."""
        
        self.generate_random_Householder_matrices()
        self.generate_random_positive_definite_diagonal_matrices()
        
        self.M_x = numpy.dot(self.D_x, self.H_x) 
        self.M_y = numpy.dot(self.D_y, self.H_y)
        
        self.W_x = numpy.dot(self.H_x, numpy.linalg.inv(self.D_x))
        self.W_y = numpy.dot(self.H_y, numpy.linalg.inv(self.D_y))
        
        
    def transform_bilinear_program(self):
        """Transforms the original bilinear program to an equivalent random bilinear program."""
        
        self.c_transformed = numpy.dot(numpy.transpose(self.M_x), self.c)
        self.d_transformed = numpy.dot(numpy.transpose(self.M_y), self.d)
        self.Q_transformed = numpy.linalg.multi_dot([numpy.transpose(self.M_x), self.Q, self.M_y])
        self.A_transformed = numpy.dot(self.A, self.M_x)
        self.B_transformed = numpy.dot(self.B, self.M_y)
        
            
    def generate_random_Householder_matrices(self):
        """Generate two random Householder matrices based on random unit vectors."""
        
        unit_vector_x = self.get_random_unit_vector(self.n_x)
        unit_vector_y = self.get_random_unit_vector(self.n_y)
        
        self.H_x = numpy.identity(self.n_x) - 2 * numpy.outer(unit_vector_x, unit_vector_x)
        self.H_y = numpy.identity(self.n_y) - 2 * numpy.outer(unit_vector_y, unit_vector_y)
    
    
    def generate_random_positive_definite_diagonal_matrices(self):
        """Generate two random positive definite diagonal matrices."""
        
        self.D_x = numpy.zeros([self.n_x, self.n_x])
        self.D_y = numpy.zeros([self.n_y, self.n_y])
        
        for i in range(self.n_x):
            self.D_x[i][i] = ONE
        
        for i in range(self.n_y):
            self.D_y[i][i] = ONE            
        
    
    def get_random_unit_vector(self, size):
        """Returns a random unit vector of the given size."""
        
        denominator = self.denominator_householder_vector
        
        # Create random permutation        
        permutation = numpy.random.permutation(list(range(size)))
        
        # Determine each entry randomly
        squared_denominator = pow(denominator, 2)
        sum_of_squared_numerators = ZERO 
        while sum_of_squared_numerators != squared_denominator:
            
            # Initialize unit vector
            unit_vector = [ZERO] * size

            sum_of_squared_numerators = ZERO
            for i in permutation:
                # Determine a new numerator until it fits into the unit vector
                possible_numerator = math.floor(random.random() * denominator)
                while sum_of_squared_numerators + pow(possible_numerator, 2) > squared_denominator:
                    possible_numerator = math.floor(random.random() * denominator)
                
                sum_of_squared_numerators += pow(possible_numerator, 2)  
                  
                unit_vector[i] = possible_numerator / denominator
                
        # Set the sign of each entry randomly
        for i in range(size):
            if random.random() < 0.5 and unit_vector[i] != ZERO:
                unit_vector[i] *= -ONE
        
        return unit_vector
        
        
class KernelProgram1(object):
    """Represents a Kernel program 1."""

    def __init__(self, k, delta, rho):

        self.k = k
        self.delta = delta
        self.rho = rho
        
        self.variables_x = []
        self.variables_y = []
        self.c = None
        self.d = None
        self.Q = None
        self.A = None
        self.a = None
        self.B = None
        self.b = None
        
        self.generate_kernel_program()


    def generate_kernel_program(self):
        """Initializes the data for the kernel program 1."""
    
        self.initialize_variables()
        self.initialize_objective()
        self.initialize_constraints()
        
        
    def initialize_variables(self):
        """Initializes the four variables of the kernel program 1."""
        
        self.variables_x.append("x_" + str(self.k) + "_1")
        self.variables_x.append("x_" + str(self.k) + "_2")
        self.variables_y.append("y_" + str(self.k) + "_1")
        self.variables_y.append("y_" + str(self.k) + "_2")
        
        
    def initialize_objective(self):
        """Initializes the coefficients of the objective of the kernel program 1."""
        
        self.Q = numpy.array([[1, 0], [0, 1]])
        
        self.c = numpy.array([-1, -1])
        self.d = numpy.array([-1, -1])
        

    def initialize_constraints(self):
        """Initializes the coefficients of the constraints of the kernel program 1."""
        
        self.A = numpy.array([[0, 1], [-2, -1], [2, -1]])
        self.a = numpy.array([2, -2, 2])

        self.B = numpy.array([[0, 1], [0, 1], [0, -2]])
        self.B[0, 0] = -1 * self.delta
        self.B[1, 0] = self.delta - self.rho
        self.B[2, 0] = self.rho
        self.b = numpy.array([0, 0, 0])
        self.b[1] = 2 * self.delta - self.rho
        
        
class KernelProgram2(object):
    """Represents a Kernel program 2."""

    def __init__(self, k):

        self.k = k
        
        self.variables_x = []
        self.variables_y = []
        self.c = None
        self.d = None
        self.Q = None
        self.A = None
        self.a = None
        self.B = None
        self.b = None
        
        self.generate_kernel_program()


    def generate_kernel_program(self):
        """Initializes the data for the kernel program 2."""
    
        self.initialize_variables()
        self.initialize_objective()
        self.initialize_constraints()
        
        
    def initialize_variables(self):
        """Initializes the four variables of the kernel program 2."""
        
        self.variables_x.append("x_" + str(self.k) + "_1")
        self.variables_x.append("x_" + str(self.k) + "_2")
        self.variables_y.append("y_" + str(self.k) + "_1")
        
        
    def initialize_objective(self):
        """Initializes the coefficients of the objective of the kernel program 2."""
        
        self.Q = numpy.array([[1], [1]])
        
        self.c = numpy.array([-1, -1])
        self.d = numpy.array([-2])
        

    def initialize_constraints(self):
        """Initializes the coefficients of the constraints of the kernel program 2."""
        
        self.A = numpy.array([[0, 1], [-2, -1], [2, -1]])  
        self.a = numpy.array([2, -2, 2])      
        
        self.B = numpy.array([[1], [-1]])
        self.b = numpy.array([2, -1])
        

class BilinearInstanceGenerator(object):
    """Instance generator for disjointly constrained bilinear programs."""

    def __init__(self, num_kernel_1, num_kernel_2, delta, rho, denominator_householder_vector, number_of_instance, include_tightening):
        
        self.num_kernel_1 = num_kernel_1
        self.num_kernel_2 = num_kernel_2
        self.delta = delta
        self.rho = rho
        self.denominator_householder_vector = denominator_householder_vector
        self.number_of_instance = number_of_instance
        self.include_tightening = include_tightening
        
        self.lower_bounds_tightened_x_transformed = None
        self.upper_bounds_tightened_x_transformed = None
        self.lower_bounds_tightened_y_transformed = None
        self.upper_bounds_tightened_y_transformed = None
        
        self.default_bound = float(pow(10, 9))
        self.time_limit_tighten_bounds_minmax = 60.0
        
        # Generate only if at least one kernel problem exists
        if num_kernel_1 > 0 or num_kernel_2 > 0:
            self.generate_bilinear_program()
            self.write_original_instance()
            self.generate_lp_bounds_for_original_instance()
            self.transform_bounds()
            self.write_bilinear_instance()
             
             
    def generate_bilinear_program(self):
        """Generates the data for the bilinear program."""

        num_kernel_1 = self.num_kernel_1
        num_kernel_2 = self.num_kernel_2
        delta = self.delta
        rho = self.rho
        denominator_householder_vector = self.denominator_householder_vector
        number_of_instance = self.number_of_instance
         
        # Set random seed
        seed = int(num_kernel_1 + num_kernel_2 + delta + rho + number_of_instance)
        random.seed(seed)
        numpy.random.seed(seed)
        
        # Generate the bilinear program 
        self.bilinear_program = BilinearProgram(num_kernel_1, num_kernel_1 + num_kernel_2, delta, rho, denominator_householder_vector) 


    def write_original_instance(self):
        """Writes the original untransformed disjointly bilinear instance into an lp file."""
        
        num_kernel_1 = self.num_kernel_1
        num_kernel_2 = self.num_kernel_2
        delta = self.delta
        rho = self.rho
        number_of_instance = self.number_of_instance
        bilinear_program = self.bilinear_program
        default_bound = self.default_bound
        
        # Change to the main working directory
        path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
        os.chdir(os.path.join(path_working_directory, "..")) 
        
        # Open the instance output file 
        path_output = os.path.join("input", "instances")  
        if not os.path.exists(path_output):
            os.makedirs(path_output)  
        self.name_original_instance = ("bil_" + str(num_kernel_1) + "_" + str(num_kernel_2) + "_" + 
                                                            str(delta) + "_" + str(rho) + "_" + str(number_of_instance))
        path_bilinear_instance = os.path.join(path_output, self.name_original_instance + ".lp")
        bilinear_instance_file = open(path_bilinear_instance, 'w')
        
        num_variables = len(bilinear_program.variables_x) + len(bilinear_program.variables_y)
        num_equations_eq = 0
        num_equations_ge = 0
        num_equations_le = bilinear_program.A.shape[0] + bilinear_program.B.shape[0]
    
    
        # Write the objective function 
        string_objective = "Minimize\n"
        string_objective += " obj: "
         
        # Write quadratic part of objective function.
        string_objective += "["
        Q_nonzeroes = numpy.nonzero(bilinear_program.Q)
        for (var_a, var_b) in zip(*Q_nonzeroes):
            if bilinear_program.Q[(var_a, var_b)] < 0:
                coefficient = " - " + str(-1 * bilinear_program.Q[(var_a, var_b)])
            else:
                coefficient = " + " + str(bilinear_program.Q[(var_a, var_b)])
            string_objective += (coefficient + " " + bilinear_program.variables_x[var_a] + " * " + bilinear_program.variables_y[var_b])
        string_objective += " ]"
        
        # Write linear part of objective function.
        for var in range(len(bilinear_program.variables_x)):
            if bilinear_program.c[var] < 0:
                coefficient = " - " + str(-1 * bilinear_program.c[var])
            else:
                coefficient = " + " + str(bilinear_program.c[var])
            string_objective += coefficient + " " + bilinear_program.variables_x[var]
        for var in range(len(bilinear_program.variables_y)):
            if bilinear_program.d[var] < 0:
                coefficient = " - " + str(-1 * bilinear_program.d[var])
            else:
                coefficient = " + " + str(bilinear_program.d[var])            
            string_objective += coefficient + " " + bilinear_program.variables_y[var]
          
          
        # Write the constraints
        string_constraints = "Subject To\n"
        num_constraint = 2
        
        for line in range(bilinear_program.A.shape[0]):
            string_constraints += " e" + str(num_constraint) + ":"
            A_line_nonzeroes = numpy.nonzero(bilinear_program.A[line])[0]
            for column in A_line_nonzeroes:
                if bilinear_program.A[line, column] < 0:
                    coefficient = " - " + str(-1 * bilinear_program.A[line, column])
                else:
                    coefficient = " + " + str(bilinear_program.A[line, column])                   
                string_constraints += coefficient + " " + bilinear_program.variables_x[column]
    
            string_constraints += " <= "
            string_constraints += str(bilinear_program.a[line])
            string_constraints += "\n"    
    
            num_constraint += 1
            
        for line in range(bilinear_program.B.shape[0]):
            string_constraints += " e" + str(num_constraint) + ":"
            B_line_nonzeroes = numpy.nonzero(bilinear_program.B[line])[0]
            for column in B_line_nonzeroes:
                if bilinear_program.B[line, column] < 0:
                    coefficient = " - " + str(-1 * bilinear_program.B[line, column])
                else:
                    coefficient = " + " + str(bilinear_program.B[line, column])                 
                string_constraints += coefficient + " " + bilinear_program.variables_y[column]
    
            string_constraints += " <= "
            string_constraints += str(bilinear_program.b[line])
            string_constraints += "\n"    
    
            num_constraint += 1   
            

        # Write bounds
        string_bounds = "Bounds\n"
        for var in range(len(bilinear_program.variables_x)):
            string_bounds += " " + str(-1 * default_bound) + " <= " + bilinear_program.variables_x[var] + " <= " + str(default_bound) +" \n"
        for var in range(len(bilinear_program.variables_y)):
            string_bounds += " " + str(-1 * default_bound) + " <= " + bilinear_program.variables_y[var] + " <= " + str(default_bound) +" \n"
    
        
        bilinear_instance_file.write("\ Equation counts\n")
        bilinear_instance_file.write("\     Total        E        G        L        N        X        C        B\n")
        bilinear_instance_file.write("\\\t" + str(num_equations_eq + num_equations_le + num_equations_ge) + "\t" + 
                                            str(num_equations_eq) + "\t" + str(num_equations_ge) + "\t" + str(num_equations_le) + "\n")                    
        bilinear_instance_file.write("\\\n") 
        bilinear_instance_file.write("\ Variable counts\n")
        bilinear_instance_file.write("\                  x        b        i      s1s      s2s       sc       si\n")
        bilinear_instance_file.write("\     Total     cont   binary  integer     sos1     sos2    scont     sint\n")
        bilinear_instance_file.write("\\\t" + str(num_variables) + "\t" + str(num_variables) + "\n")
        bilinear_instance_file.write("\n")
        bilinear_instance_file.write("\ Nonzero counts\n")
        bilinear_instance_file.write("\     Total    const       NL      DLL\n")
        bilinear_instance_file.write("\\\n")
        bilinear_instance_file.write("\\\n")
        bilinear_instance_file.write(string_objective)
        bilinear_instance_file.write("\n\n")
        bilinear_instance_file.write(string_constraints)
        bilinear_instance_file.write("\n")
        bilinear_instance_file.write(string_bounds)
        bilinear_instance_file.write("\n")    
        bilinear_instance_file.write("End")
        bilinear_instance_file.close() 
        
    
    def write_bilinear_instance(self):
        """Writes the transformed disjointly bilinear instance into an lp file."""
        
        bilinear_program = self.bilinear_program
        default_bound = self.default_bound
        
        # Change to the main working directory
        path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
        os.chdir(os.path.join(path_working_directory, "..")) 
        
        # Open the instance output file 
        path_output = os.path.join("output", "bilinear_instances")  
        if not os.path.exists(path_output):
            os.makedirs(path_output)  
        instance_name = self.name_original_instance + "_tr"
        self.path_bilinear_instance = os.path.join(path_output, instance_name + ".lp")
        bilinear_instance_file = open(self.path_bilinear_instance, 'w')
        
        num_variables = len(bilinear_program.variables_x) + len(bilinear_program.variables_y)
        num_equations_eq = 0
        num_equations_ge = 0
        num_equations_le = bilinear_program.A_transformed.shape[0] + bilinear_program.B_transformed.shape[0]
        
        
        # Write the objective function 
        string_objective = "Minimize\n"
        string_objective += " obj: "
         
        # Write quadratic part of objective function.
        string_objective += "["
        Q_nonzeroes = numpy.nonzero(bilinear_program.Q_transformed)
        for (var_a, var_b) in zip(*Q_nonzeroes):
            if bilinear_program.Q_transformed[(var_a, var_b)] < 0:
                coefficient = " - " + str(-1 * bilinear_program.Q_transformed[(var_a, var_b)])
            else:
                coefficient = " + " + str(bilinear_program.Q_transformed[(var_a, var_b)])            
            string_objective += (coefficient + " " + bilinear_program.variables_x[var_a] + " * " + bilinear_program.variables_y[var_b])
        string_objective += " ]"
        
        # Write linear part of objective function.
        for var in range(len(bilinear_program.variables_x)):
            if bilinear_program.c_transformed[var] < 0:
                coefficient = " - " + str(-1 * bilinear_program.c_transformed[var])
            else:
                coefficient = " + " + str(bilinear_program.c_transformed[var])            
            string_objective += coefficient + " " + bilinear_program.variables_x[var]
        for var in range(len(bilinear_program.variables_y)):
            if bilinear_program.d_transformed[var] < 0:
                coefficient = " - " + str(-1 * bilinear_program.d_transformed[var])
            else:
                coefficient = " + " + str(bilinear_program.d_transformed[var])              
            string_objective += coefficient + " " + bilinear_program.variables_y[var]
          
          
        # Write the constraints
        string_constraints = "Subject To\n"
        num_constraint = 2
        
        for line in range(bilinear_program.A_transformed.shape[0]):
            string_constraints += " e" + str(num_constraint) + ":"
            A_line_nonzeroes = numpy.nonzero(bilinear_program.A_transformed[line])[0]
            for column in A_line_nonzeroes:
                if bilinear_program.A_transformed[line, column] < 0:
                    coefficient = " - " + str(-1 * bilinear_program.A_transformed[line, column])
                else:
                    coefficient = " + " + str(bilinear_program.A_transformed[line, column])                      
                string_constraints += coefficient + " " + bilinear_program.variables_x[column]
    
            string_constraints += " <= "
            string_constraints += str(bilinear_program.a[line])
            string_constraints += "\n"    
    
            num_constraint += 1
            
        for line in range(bilinear_program.B_transformed.shape[0]):
            string_constraints += " e" + str(num_constraint) + ":"
            B_line_nonzeroes = numpy.nonzero(bilinear_program.B_transformed[line])[0]
            for column in B_line_nonzeroes:
                if bilinear_program.B_transformed[line, column] < 0:
                    coefficient = " - " + str(-1 * bilinear_program.B_transformed[line, column])
                else:
                    coefficient = " + " + str(bilinear_program.B_transformed[line, column])                 
                string_constraints += coefficient + " " + bilinear_program.variables_y[column]
    
            string_constraints += " <= "
            string_constraints += str(bilinear_program.b[line])
            string_constraints += "\n"    
    
            num_constraint += 1   
            

        # Write bounds
        string_bounds = "Bounds\n"
        if include_tightening:    
            for var in bilinear_program.variables_x:
                string_bounds += " " + str(self.lower_bounds_tightened_box[var]) + " <= " + var + " <= " + str(self.upper_bounds_tightened_box[var]) +" \n"
            for var in bilinear_program.variables_y:
                string_bounds += " " + str(self.lower_bounds_tightened_box[var]) + " <= " + var + " <= " + str(self.upper_bounds_tightened_box[var]) +" \n"
        else:
            for var in range(len(bilinear_program.variables_x)):
                string_bounds += " " + str(-1 * default_bound) + " <= " + bilinear_program.variables_x[var] + " <= " + str(default_bound) +" \n"
            for var in range(len(bilinear_program.variables_y)):
                string_bounds += " " + str(-1 * default_bound) + " <= " + bilinear_program.variables_y[var] + " <= " + str(default_bound) +" \n"
    
        
        bilinear_instance_file.write("\ Equation counts\n")
        bilinear_instance_file.write("\     Total        E        G        L        N        X        C        B\n")
        bilinear_instance_file.write("\\\t" + str(num_equations_eq + num_equations_le + num_equations_ge) + "\t" + 
                                            str(num_equations_eq) + "\t" + str(num_equations_ge) + "\t" + str(num_equations_le) + "\n")                    
        bilinear_instance_file.write("\\\n") 
        bilinear_instance_file.write("\ Variable counts\n")
        bilinear_instance_file.write("\                  x        b        i      s1s      s2s       sc       si\n")
        bilinear_instance_file.write("\     Total     cont   binary  integer     sos1     sos2    scont     sint\n")
        bilinear_instance_file.write("\\\t" + str(num_variables) + "\t" + str(num_variables) + "\n")
        bilinear_instance_file.write("\n")
        bilinear_instance_file.write("\ Nonzero counts\n")
        bilinear_instance_file.write("\     Total    const       NL      DLL\n")
        bilinear_instance_file.write("\\\n")
        bilinear_instance_file.write("\\\n")
        bilinear_instance_file.write(string_objective)
        bilinear_instance_file.write("\n\n")
        bilinear_instance_file.write(string_constraints)
        bilinear_instance_file.write("\n")
        bilinear_instance_file.write(string_bounds)
        bilinear_instance_file.write("\n")    
        bilinear_instance_file.write("End")
        bilinear_instance_file.close() 
            

    def generate_lp_bounds_for_original_instance(self):
        """Generate LP based bounds from the original disjointly constrained bilinear instance."""        
    
        name_of_instance = self.name_original_instance
        time_limit_tighten_bounds_minmax = self.time_limit_tighten_bounds_minmax
        default_bound = self.default_bound
    
        data, output_writer = get_data(name_of_instance, time_limit_tighten_bounds_minmax, default_bound)
        
        write_tightened_instance = False
        bound_tightener = BoundTightener(data, output_writer, write_tightened_instance)
        bound_tightener.start()
        
        self.lower_bounds_tightened = bound_tightener.instance_data.lower_bounds_tightened
        self.upper_bounds_tightened = bound_tightener.instance_data.upper_bounds_tightened
        self.data = data
        self.output_writer = output_writer
      
      
    def transform_bounds(self):
        """Adapts the LP based bounds of the original problem for the transformed problem."""        
    
        num_kernel_1 = self.num_kernel_1
        num_kernel_2 = self.num_kernel_2
    
        # Separate original bounds to x and y variables
        self.lower_bounds_tightened_x = []
        self.lower_bounds_tightened_y = []
        self.upper_bounds_tightened_x = []
        self.upper_bounds_tightened_y = []
        
        # Initialize transformed bounds
        self.lower_bounds_tightened_box = {}
        self.upper_bounds_tightened_box = {}
        
        # Write lower bounds into a list
        for i in range(1, num_kernel_1 + num_kernel_2 + 1):
            for j in [1, 2]:
                var = "x_" + str(i) + "_" + str(j)
                self.lower_bounds_tightened_x.append(self.lower_bounds_tightened[var])
        for i in range(1, num_kernel_1 + 1):
            for j in [1, 2]:
                var = "y_" + str(i) + "_" + str(j)
                self.lower_bounds_tightened_y.append(self.lower_bounds_tightened[var])    
        for i in range(num_kernel_1 + 1, num_kernel_1 + num_kernel_2 + 1):
            var = "y_" + str(i) + "_1"
            self.lower_bounds_tightened_y.append(self.lower_bounds_tightened[var])                            
        
        # Write upper bounds into a list
        for i in range(1, num_kernel_1 + num_kernel_2 + 1):
            for j in [1, 2]:
                var = "x_" + str(i) + "_" + str(j)
                self.upper_bounds_tightened_x.append(self.upper_bounds_tightened[var])
        for i in range(1, num_kernel_1 + 1):
            for j in [1, 2]:
                var = "y_" + str(i) + "_" + str(j)
                self.upper_bounds_tightened_y.append(self.upper_bounds_tightened[var])    
        for i in range(num_kernel_1 + 1, num_kernel_1 + num_kernel_2 + 1):
            var = "y_" + str(i) + "_1"
            self.upper_bounds_tightened_y.append(self.upper_bounds_tightened[var])  
            
        # Tighten x variables
        self.tighten_bounds_box(self.bilinear_program.variables_x, self.bilinear_program.M_x, self.lower_bounds_tightened_x, self.upper_bounds_tightened_x)
        
        # Tighten y variables
        self.tighten_bounds_box(self.bilinear_program.variables_y, self.bilinear_program.M_y, self.lower_bounds_tightened_y, self.upper_bounds_tightened_y)


    def tighten_bounds_box(self, variables, matrix, lower_bounds, upper_bounds):
        """Determines the bounds for the transformed problem by min/max LPs using the bounds for the original problem.""" 

        # Set up GAMS environment
        name_gams_workspace = "GAMS_workspace_BoundTightenerBox"
        gams_file = "qcp_tighten_bounds_box.gms"
        model_name = "QCP_TIGHTEN_BOUNDS_BOX"
        model_type = "QCP"         
        gams_environment = EnvironmentGAMSTightenBoundsBox(self.data, self.output_writer, name_gams_workspace, 
                                                        gams_file, model_name, model_type, variables, matrix, lower_bounds, upper_bounds)
        
        time_limit_tighten_bounds_minmax = self.time_limit_tighten_bounds_minmax
        default_bound = self.default_bound
        
        self.num_bounds_tightened = 0 
        
        # Tighten bounds
        for var in variables:
            
            # Tighten lower bound
            gams_environment.initialize_lower_bound_tightening(var)
            gams_environment.solve_tighten_bounds_box(time_limit_tighten_bounds_minmax)
            
            lower_bound_tightened = gams_environment.get_dual_bound(16)
            if lower_bound_tightened != ZERO:
                lower_bound_tightened = -ONE * lower_bound_tightened            
            
            self.lower_bounds_tightened_box[var] = lower_bound_tightened
            
            if self.lower_bounds_tightened_box[var] > -1e+40:
                print("Tightened lower bound of " + var + " to " + str(self.lower_bounds_tightened_box[var]))
                self.num_bounds_tightened += 1
            else:
                self.lower_bounds_tightened_box[var] = -ONE * default_bound
                
            # Tighten upper bound
            gams_environment.initialize_upper_bound_tightening(var)
            gams_environment.solve_tighten_bounds_box(time_limit_tighten_bounds_minmax)
            
            upper_bound_tightened = gams_environment.get_dual_bound(16)
            
            self.upper_bounds_tightened_box[var] = upper_bound_tightened 
            
            if self.upper_bounds_tightened_box[var] < 1e+40:
                print("Tightened upper bound of " + var + " to " + str(self.upper_bounds_tightened_box[var]))
                self.num_bounds_tightened += 1
            else:
                self.upper_bounds_tightened_box[var] = default_bound
                                
            # Clean GAMS workspace to save memory    
            self.output_writer.clean_gams_workspace_folder()
        
        print("\nTightened " + str(self.num_bounds_tightened) + " bounds.\n\n")        


class EnvironmentGAMSTightenBoundsBox(EnvironmentGAMS):
    """GAMS environment for tighten the bounds of the transformed problem using the bounds from the original problem."""
    
    def __init__(self, data, output_writer, name_gams_workspace, gams_file, model_name, model_type, variables, matrix, lower_bounds, upper_bounds):

        self.algorithm_data = data.algorithm_data
        self.variables = variables
        self.matrix = matrix
        self.lower_bounds = lower_bounds
        self.upper_bounds = upper_bounds
        
        self.fixed_variables = ""
        self.output_writer = output_writer

        super().__init__(data, output_writer, name_gams_workspace, gams_file, model_name, model_type)
                

    def choose_solver(self):
        """Chooses the solver for the optimization problem."""

        self.option_solver = self.gams_workspace.add_options()
        self.option_solver.lp = "CPLEX"
        
    
    def write_data_to_gams_db(self):
        """Writes the instance data from Python data structures into a GAMS database."""
        
        gams_database = self.gams_database
        algorithm_data = self.algorithm_data
        
        feasibility_tolerance = algorithm_data.feasibility_tolerance
        
        num_lines = self.matrix.shape[0]
        
        # Sets
        db_i = gams_database.add_set("I", 1, "")
        
        for var in self.variables:
            db_i.add_record(var)
            
        db_k = gams_database.add_set("K", 1, "")
        
        for line in range(num_lines):
            db_k.add_record(str(line))            

        # Parameters
        db_coeff = gams_database.add_parameter_dc("COEFF", [db_k, db_i], "")
        for line in range(num_lines):
            for column in range(len(self.variables)):
                db_coeff.add_record((str(line), self.variables[column])).value = self.matrix[line, column]

        db_lower = gams_database.add_parameter_dc("LOWER", [db_k], "")
        for line in range(num_lines):
            db_lower.add_record(str(line)).value = self.lower_bounds[line]

        db_upper = gams_database.add_parameter_dc("UPPER", [db_k], "")
        for line in range(num_lines):
            db_upper.add_record(str(line)).value = self.upper_bounds[line]
                    
                    
        # Feasibility tolerance
        db_feas_tolerance = gams_database.add_parameter("FEAS_TOLERANCE", 0, "")
        db_feas_tolerance.add_record().value = feasibility_tolerance   
            
            
    def solve_tighten_bounds_box(self, time_limit):
        """Solves the LP."""
        
        gams_workspace = self.gams_workspace
        checkpoint = self.checkpoint
        option_solver = self.option_solver
        model_name = self.model_name
        
        fixed_variables = self.fixed_variables
        options = self.get_options(time_limit)
        
        job = gams_workspace.add_job_from_string(fixed_variables + options, checkpoint)
        log_file = self.output_writer.open_log_file(model_name, "")
                
        try: 
            job.run(option_solver, output=log_file)
        except GamsExceptionExecution:
            pass
             
        self.output_writer.close_log_file(log_file)
        self.job = job          
 

    def initialize_lower_bound_tightening(self, var):
        """Set variable coefficient in the objective function to tighten lower bound."""
        
        self.fixed_variables = ""
        self.fixed_variables += self.set_gams_parameter("COEFF_OBJ_TIGHTEN_BOUNDS", var, -ONE) 
        
        
    def initialize_upper_bound_tightening(self, var):
        """Set variable coefficient in the objective function to tighten upper bound."""
        
        self.fixed_variables = ""
        self.fixed_variables += self.set_gams_parameter("COEFF_OBJ_TIGHTEN_BOUNDS", var, ONE) 
        
    
if __name__ == '__main__':

    number_of_instances_per_size = 10
    delta = 2.5
    rho = 1.5
    denominator_householder_vector = 1000.0
    include_tightening = True
    
    for (num_kernel_1, num_kernel_2) in [(50, 50), (100, 100), (150, 150), (200, 200), (300, 300), (400, 400)]:
        for num in range(number_of_instances_per_size):
            BilinearInstanceGenerator(num_kernel_1, num_kernel_2, delta, rho, denominator_householder_vector, num, include_tightening)

