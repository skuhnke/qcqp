#!/bin/bash
#
# Author: Sascha Kuhnke
# Created: 21.09.2020
#


# Choose slurm if it is installed
if ! command -v squeue &> /dev/null
then
	use_slurm=0
else
	use_slurm=1
fi


# Adaptive Discretization Proportion
./run.sh $use_slurm "tp" "disc" "adaptive" "proportion" "-" ""2" "3" "4" "5""

# Adaptive Discretization Flow
./run.sh $use_slurm "tp" "disc" "adaptive" "flow" "-" ""2" "3" "4" "5""

# Adaptive Discretization Pool
./run.sh $use_slurm "tp" "disc" "adaptive" "pool" "-" ""1" "2" "3" "4" "5""

# Non-iterative Discretization
./run.sh $use_slurm "pq" "disc" "non-iterative" "pool" "-" ""1" "2" "3" "4" "5""

# BARON
./run.sh $use_slurm "tp" "qcp-solver" "-" "-" "baron" "-"

# SCIP
./run.sh $use_slurm "tp" "qcp-solver" "-" "-" "scip" "-"

# Gurobi
./run.sh $use_slurm "tp" "qcp-solver" "-" "-" "gurobi" "-"

# IPOPT
./run.sh $use_slurm "tp" "qcp-solver" "-" "-" "ipopt" "-"

# SNOPT
./run.sh $use_slurm "tp" "qcp-solver" "-" "-" "snopt" "-"

# MINOS
./run.sh $use_slurm "tp" "qcp-solver" "-" "-" "minos" "-"
