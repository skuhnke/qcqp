'''
Created on Feb 12, 2019

@author: Sascha Kuhnke
'''
import os
import pathlib
import sys

from data.data import AlgorithmData
from misc.exceptions import InputFormatException


# Constants
ONE = 1.0
ZERO = 0.0

# Algorithm data
DISCRETIZATION = AlgorithmData.DISCRETIZATION


class InputReader():
    """Class to read the instance data from a file in .dat format."""

    def __init__(self, data):
        
        self.instance_data = data.instance_data
        self.algorithm_data = data.algorithm_data
        name_of_instance = data.instance_data.name
                
        # Change to the main working directory
        path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
        os.chdir(os.path.join(path_working_directory, "..", "..")) 
        
        self.path_of_instance = os.path.join("input", "instances", name_of_instance + ".dat")


    def read_input(self):
        """Reads the input file in .dat format and stores the data."""
        
        self.read_input_dat_file()
        self.add_remaining_data()


    def read_input_dat_file(self):
        """Reads the input from a .dat file."""
        
        lines = self.open_input_file()
    
        # Water Sources
        line_curr = lines[2].split()
        n_ws = len(line_curr) - 4
        for i in range(n_ws):
            self.instance_data.water_sources.append(line_curr[i + 3])

        # Water Demands
        line_curr = lines[4].split()
        n_wd = len(line_curr) - 4
        for i in range(n_wd):
            self.instance_data.water_demands.append(line_curr[i + 3])

        # Pools
        line_curr = lines[6].split()
        n_pl = len(line_curr) - 4
        for i in range(n_pl):
            self.instance_data.pools.append(line_curr[i + 3])
            
        # Contaminants
        line_curr = lines[8].split()
        n_co = len(line_curr) - 4
        for i in range(n_co):
            self.instance_data.contaminants.append(line_curr[i + 3])

        # Water Source Characteristics
        for i in range(n_ws):
            line_curr = lines[11 + i].split()
            ws_curr = line_curr[0]
            self.instance_data.fl_max_un[ws_curr] = float(line_curr[1])
            self.instance_data.cost_ws[ws_curr] = float(line_curr[2])

        # Pool Characteristics
        for i in range(n_pl):
            line_curr = lines[11 + n_ws + i].split()
            pl_curr = line_curr[0]
            self.instance_data.fl_max_un[pl_curr] = float(line_curr[1])
            
        # Water Demand Characteristics
        for i in range(n_wd):
            line_curr = lines[11 + n_ws + n_pl + i].split()
            wd_curr = line_curr[0]
            self.instance_data.fl_max_un[wd_curr] = float(line_curr[1])
            self.instance_data.revenue_wd[wd_curr] = float(line_curr[3])

        # Existing Pipes into Pools
        line_curr = lines[11 + n_ws + n_pl + n_wd + 1].split()
        n_inpoolarcs = int((len(line_curr) - 3) / 2)
        for i in range(n_inpoolarcs):
            arc_curr = line_curr[2 * i + 3]
            arc_curr = arc_curr[1:-1]
            arc_curr = arc_curr.split(',')
            un_out_curr = arc_curr[0]
            un_in_curr = arc_curr[1]
            self.instance_data.pipe_exists[(un_out_curr, un_in_curr)] = True
        
        # Existing Pipes out of Pools
        line_curr = lines[11 + n_ws + n_pl + n_wd + 3].split()
        n_outpoolarcs = int((len(line_curr) - 3) / 2)
        for i in range(n_outpoolarcs):
            arc_curr = line_curr[2 * i + 3]
            arc_curr = arc_curr[1:-1]
            arc_curr = arc_curr.split(',')
            un_out_curr = arc_curr[0]
            un_in_curr = arc_curr[1]
            self.instance_data.pipe_exists[(un_out_curr, un_in_curr)] = True
        
        # Existing Pipes from Sources to Demands
        line_curr = lines[11 + n_ws + n_pl + n_wd + 5].split()
        n_inoutarcs = int((len(line_curr) - 3) / 2)
        for i in range(n_inoutarcs):
            arc_curr = line_curr[2 * i + 3]
            arc_curr = arc_curr[1:-1]
            arc_curr = arc_curr.split(',')
            un_out_curr = arc_curr[0]
            un_in_curr = arc_curr[1]
            self.instance_data.pipe_exists[(un_out_curr, un_in_curr)] = True

        # Water Source Concentrations
        for i in range(n_ws):
            line_curr = lines[11 + n_ws + n_pl + n_wd + 9 + i].split()
            ws_curr = line_curr[0]
            for j in range(n_co):
                co_curr = self.instance_data.contaminants[j]
                po_curr = float(line_curr[j + 1])
                self.instance_data.po_ws[(ws_curr, co_curr)] = po_curr

        # Water Demand Minimum Concentrations
        for i in range(n_wd):
            line_curr = lines[11 + n_ws + n_pl + n_wd + 9 + n_ws + 3 + i].split()
            wd_curr = line_curr[0]
            for j in range(n_co):
                co_curr = self.instance_data.contaminants[j]
                po_curr = float(line_curr[j + 1])
                self.instance_data.po_min_wd[(wd_curr, co_curr)] = po_curr

        # Water Demand Maximum Concentrations
        for i in range(n_wd):
            line_curr = lines[11 + n_ws + n_pl + n_wd + 9 + n_ws + n_wd + 6 + i].split()
            wd_curr = line_curr[0]
            for j in range(n_co):
                co_curr = self.instance_data.contaminants[j]
                po_curr = float(line_curr[j + 1])
                self.instance_data.po_max_wd[(wd_curr, co_curr)] = po_curr
                

    def add_remaining_data(self):
        """Adds remaining data that has to be calculated from the input data."""
        
        disc_size = self.algorithm_data.disc_size
        algorithm = self.algorithm_data.algorithm
        
        self.instance_data.units = self.instance_data.water_sources + self.instance_data.pools + self.instance_data.water_demands
        self.instance_data.units_out = self.instance_data.water_sources + self.instance_data.pools
        self.instance_data.units_in = self.instance_data.pools + self.instance_data.water_demands
        
        # Add indices of discretization
        self.algorithm_data.disc_indices = []

        if algorithm == DISCRETIZATION:
            for i in range(disc_size):
                self.algorithm_data.disc_indices.append(str(i))
        
        # Complete Existing Pipes
        for un_out in self.instance_data.units_out:
            for un_in in self.instance_data.units_in:
                if (un_out, un_in) not in self.instance_data.pipe_exists:
                    self.instance_data.pipe_exists[(un_out, un_in)] = False
        
        # Calculate Maximum Capacities at Pipes
        for un_out in self.instance_data.units_out:
            for un_in in self.instance_data.units_in:
                if self.instance_data.pipe_exists[(un_out, un_in)]:
                    fl_max_curr = min(self.instance_data.fl_max_un[un_out], self.instance_data.fl_max_un[un_in])
                else:
                    fl_max_curr = ZERO 
                self.instance_data.fl_max[(un_out, un_in)] = fl_max_curr
                
        # Reduce Maximum Capacities   
        for un_out in self.instance_data.units_out:
            fl_max_un_curr = ZERO
            for un_in in self.instance_data.units_in:
                fl_max_un_curr += self.instance_data.fl_max[(un_out, un_in)]
            if fl_max_un_curr < self.instance_data.fl_max_un[un_out]:
                self.instance_data.fl_max_un[un_out] = fl_max_un_curr

        for un_in in self.instance_data.units_in:
            fl_max_un_curr = ZERO
            for un_out in self.instance_data.units_out:
                fl_max_un_curr += self.instance_data.fl_max[(un_out, un_in)]
            if fl_max_un_curr < self.instance_data.fl_max_un[un_in]:
                self.instance_data.fl_max_un[un_in] = fl_max_un_curr
                
        # Calculate Cost on Pipes
        for un_out in self.instance_data.units_out:
            for un_in in self.instance_data.units_in:
                if self.instance_data.pipe_exists[(un_out, un_in)]:
                    if (un_out in self.instance_data.water_sources) and (un_in in self.instance_data.pools):
                        cost_curr = -1 * self.instance_data.cost_ws[un_out]
                    elif (un_out in self.instance_data.water_sources) and (un_in in self.instance_data.water_demands):
                        cost_curr = self.instance_data.revenue_wd[un_in] - self.instance_data.cost_ws[un_out] 
                    elif (un_out in self.instance_data.pools) and (un_in in self.instance_data.water_demands):
                        cost_curr = self.instance_data.revenue_wd[un_in]
                else:
                    cost_curr = ZERO
                self.instance_data.cost[(un_out, un_in)] = cost_curr
                
        # Preprocessing
        for wd in self.instance_data.water_demands:
            for co in self.instance_data.contaminants:
                self.instance_data.is_active_min[(wd, co)] = ONE
                self.instance_data.is_active_max[(wd, co)] = ONE


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

