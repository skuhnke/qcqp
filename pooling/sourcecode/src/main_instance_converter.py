'''
Created on Feb 12, 2019

@author: Sascha Kuhnke
'''
import os
import pathlib
import sys


def convert_instance_into_standard_format():
    """Converts the .dat instances of Alfaki and Haugland into .dat instances in standard format."""

    name_of_instance = sys.argv[1]
#     name_of_instance = "stdAsmall"
    
    path_working_directory = pathlib.Path(os.path.realpath(__file__)).parent
    os.chdir(os.path.join(path_working_directory, "..")) 
    
    
    path_of_instance = os.path.join("input", "Alfaki_and_Haugland", name_of_instance + ".dat")
    with open(path_of_instance, 'r') as input_file:
        lines = input_file.readlines()
    input_file.close()
    
    path_output = os.path.join("output", "converted_instances")
    
    # Create directory    
    if not os.path.exists(path_output):
        os.makedirs(path_output)
                
    path_output_instance = os.path.join("output", "converted_instances", name_of_instance + ".dat")
    output_file = open(path_output_instance, 'w')
    
    water_sources = []
    pools = []
    water_demands = []
    contaminants = []
    cost_ws = {}
    revenue_wd = {}   
    fl_max_un = {}
    pipe_exists = {}
    
    # READ INPUT
    # Water Sources
    line_curr = lines[1].split()
    n_ws = len(line_curr) - 4
    for i in range(n_ws):
        water_sources.append(line_curr[i + 3])

    # Water Demands
    line_curr = lines[2].split()
    n_wd = len(line_curr) - 4
    for i in range(n_wd):
        water_demands.append(line_curr[i + 3])

    # Pools
    line_curr = lines[4].split()
    n_pl = len(line_curr) - 4
    for i in range(n_pl):
        pools.append(line_curr[i + 3])
        
    # Contaminants
    line_curr = lines[3].split()
    n_co = len(line_curr) - 4
    for i in range(n_co):
        contaminants.append(line_curr[i + 3])
        
    # Water Source Characteristics
    for i in range(n_ws):
        line_curr = lines[7 + i].split()
        ws_curr = line_curr[0]
        cost_ws[ws_curr] = line_curr[1]

    # Water Demand Characteristics
    for i in range(n_wd):
        line_curr = lines[7 + n_ws + 2 + i].split()
        wd_curr = line_curr[0]
        revenue_wd[wd_curr] = line_curr[1]
    
    # Capacities
    for i in range(n_ws):
        line_curr = lines[7 + n_ws + n_wd + 4 + i].split()
        ws_curr = line_curr[0]
        fl_max_un[ws_curr] = line_curr[1]
    for i in range(n_pl):
        line_curr = lines[7 + n_ws + n_wd + n_ws + 4 + i].split()
        pl_curr = line_curr[0]
        fl_max_un[pl_curr] = line_curr[1]
    for i in range(n_wd):
        line_curr = lines[7 + n_ws + n_wd + n_ws + n_pl + 4 + i].split()
        wd_curr = line_curr[0]            
        fl_max_un[wd_curr] = line_curr[1]
        
    # Existing Pipes into Pools
    for i in range(n_ws):
        line_curr = lines[7 + n_ws + n_wd + n_ws + n_pl + n_wd + 6 + i].split()
        ws_curr = line_curr[0]
        for j in range(n_pl):
            pl_curr = pools[j]
            arc_curr = line_curr[1 + j]
            if arc_curr == "+":
                pipe_exists[(ws_curr, pl_curr)] = True

    # Existing Pipes from Sources to Demands
    for i in range(n_ws):
        line_curr = lines[7 + n_ws + n_wd + n_ws + n_pl + n_wd + n_ws + 8 + i].split()
        ws_curr = line_curr[0]
        for j in range(n_wd):
            wd_curr = water_demands[j]
            arc_curr = line_curr[1 + j]
            if arc_curr == "+":
                pipe_exists[(ws_curr, wd_curr)] = True
    
    # Existing Pipes out of Pools
    for i in range(n_pl):
        line_curr = lines[7 + n_ws + n_wd + n_ws + n_pl + n_wd + n_ws + n_ws + 10 + i].split()
        pl_curr = line_curr[0]
        for j in range(n_wd):
            wd_curr = water_demands[j]
            arc_curr = line_curr[1 + j]
            if arc_curr == "+":
                pipe_exists[(pl_curr, wd_curr)] = True  
    
    # Complete Existing Pipes        
    for un_out in water_sources + pools:
        for un_in in pools + water_demands:
            if (un_out, un_in) not in pipe_exists:
                pipe_exists[(un_out, un_in)] = False                             

    # WRITE OUTPUT
    
    output_file.write(lines[0])
    output_file.write("\n")
    output_file.write(lines[1])
    output_file.write("\n")
    output_file.write(lines[2])
    output_file.write("\n")
    output_file.write(lines[4])
    output_file.write("\n")
    output_file.write(lines[3])
    output_file.write("\n")
    
    output_file.write("param:\t\tcapacity\tvarcost\t\trevenue\t\t:=\n")
    for ws in water_sources:
        output_file.write(ws + "\t\t" + fl_max_un[ws] + "\t\t" + cost_ws[ws] + "\t\t" + "." + "\n")
    for pl in pools:
        output_file.write(pl + "\t\t" + fl_max_un[pl] + "\t\t" + "." + "\t\t" + "." + "\n")
    for wd in water_demands:
        if wd == water_demands[-1]:
            semicolon = "\t\t;"
        else:
            semicolon = ""
        output_file.write(wd + "\t\t" + fl_max_un[wd] + "\t\t" + "." + "\t\t" + revenue_wd[wd] + semicolon + "\n")
    output_file.write("\n")
    
    inpoolarcs = " set INPOOLARCS := "
    for ws in water_sources:
        for pl in pools:
            if pipe_exists[(ws, pl)]:
                inpoolarcs += "(" + ws + "," + pl + ")" + " , "
    inpoolarcs = inpoolarcs[:-2]
    inpoolarcs += " ;\n\n"
    
    outpoolarcs = " set OUTPOOLARCS := "
    for pl in pools:
        for wd in water_demands:
            if pipe_exists[(pl, wd)]:
                outpoolarcs += "(" + pl + "," + wd + ")" + " , "
    outpoolarcs = outpoolarcs[:-2]
    outpoolarcs += " ;\n\n"    
    
    inoutarcs = " set OUTPOOLARCS := "
    for ws in water_sources:
        for wd in water_demands:
            if pipe_exists[(ws, wd)]:
                inoutarcs += "(" + ws + "," + wd + ")" + " , "
    inoutarcs = inoutarcs[:-2]
    inoutarcs += " ;\n\n"        
    
    output_file.write(inpoolarcs)
    output_file.write(outpoolarcs)
    output_file.write(inoutarcs)
    
    output_file.writelines(lines[7 + n_ws + n_wd + n_ws + n_pl + n_wd + n_ws + n_ws + n_pl + 11:
                            7 + n_ws + n_wd + n_ws + n_pl + n_wd + n_ws + n_ws + n_pl + 11 + n_ws + 2 * n_wd + 8])
    
    output_file.close()    
    

if __name__ == '__main__':

    convert_instance_into_standard_format()

    
