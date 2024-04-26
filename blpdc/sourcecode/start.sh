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


# Adaptive Discretization
./run.sh $use_slurm "disc" "adaptive" "highest-degree" "-" ""2" "3" "4" "5""

# Non-iterative Discretization
#./run.sh $use_slurm "disc" "non-iterative" "highest-degree" "-" ""2" "3" "4" "5""

# BARON
./run.sh $use_slurm "qcp-solver" "-" "-" "baron" "-"

# SCIP
#./run.sh $use_slurm "qcp-solver" "-" "-" "scip" "-"

# Gurobi
./run.sh $use_slurm "qcp-solver" "-" "-" "gurobi" "-"

# IPOPT
./run.sh $use_slurm "qcp-solver" "-" "-" "ipopt" "-"

# SNOPT
./run.sh $use_slurm "qcp-solver" "-" "-" "snopt" "-"

# MINOS
./run.sh $use_slurm "qcp-solver" "-" "-" "minos" "-"
