#!/bin/bash
#
# Author: Sascha Kuhnke
# Created: 19.03.2020
#
#SBATCH --job-name=pooling
#SBATCH --output=output_slurm/%j.txt
#
#SBATCH --cpus-per-task=2
#SBATCH --time=08:00:00
#
#SBATCH --mail-type=NONE
#SBATCH --mail-user=kuhnke@math2.rwth-aachen.de


# Use parameters given by the arguments 
instance_name="$1"
formulation="$2"
algorithm="$3"
disc_type="$4"
disc_variant="$5"
qcp_solver="$6"
disc_size="$7"


# Get algorithm output directory
if [ "$algorithm" == "disc" ]; then
	dir_output="output/${formulation}_${algorithm}_${disc_type}_${disc_variant}_${disc_size}"
elif [ "$algorithm" == "qcp-solver" ]; then
	dir_output="output/${formulation}_${algorithm}_${qcp_solver}"
fi

# Solve instance
(time -p python3.6 src/main.py "$instance_name" "$formulation" "$algorithm" "$disc_type" "$disc_variant" "$qcp_solver" "$disc_size") 2> "${dir_output}/${instance_name}.time"

# Store CPU time
python3.6 src/input_output/main_add_cpu_time.py $instance_name $dir_output
rm -f "${dir_output}/${instance_name}.time"

# Delete GAMS workspaces
rm -rf "${dir_output}/${instance_name}/gams_workspaces"
