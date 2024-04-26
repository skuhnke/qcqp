#!/bin/bash
#
# Author: Sascha Kuhnke
# Created: 29.07.2020
#
#SBATCH --job-name=qcp
#SBATCH --output=output_slurm/%j.txt
#
#SBATCH --cpus-per-task=2
#SBATCH --time=08:00:00
#
#SBATCH --mail-type=NONE
#SBATCH --mail-user=kuhnke@math2.rwth-aachen.de
 

# Use parameters given by the arguments
instance_name="$1"
algorithm="$2"
disc_type="$3"
disc_quad_variables="$4"
qcp_solver="$5"
disc_size="$6"


# Get algorithm output directory
if [ "$algorithm" == "disc" ]; then
	dir_output="output/${algorithm}_${disc_type}_${disc_quad_variables}_${disc_size}"
elif [ "$algorithm" == "qcp-solver" ]; then
	dir_output="output/${algorithm}_${qcp_solver}"
fi

# Solve instance
(time -p python3.6 src/main.py "$instance_name" "$algorithm" "$disc_type" "$disc_quad_variables" "$qcp_solver" "$disc_size") 2> "${dir_output}/${instance_name}.time"

# Store CPU time
python3.6 src/input_output/main_add_cpu_time.py $instance_name $dir_output
rm -f "${dir_output}/${instance_name}.time"

# Delete GAMS workspaces
rm -rf "${dir_output}/${instance_name}/gams_workspaces"
