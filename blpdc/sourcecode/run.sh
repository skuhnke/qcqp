#!/bin/bash
#
# Author: Sascha Kuhnke
# Created: 29.07.2020


# Use parameters given by the arguments
use_slurm="$1"
algorithm="$2"
disc_type="$3"
disc_quad_variables="$4"
qcp_solver="$5"
disc_sizes="$6"


# Set memory for slurm
memory=14000


# Set discretization sizes to zero for non-discretization algorithms
if [ "$algorithm" == "qcp-solver" ]; then
	disc_sizes=("0")
fi


# Collect instance names
instance_names=()

# Check if instance directory contains instances
if ls input/instances/*.lp &>/dev/null 2>&1
then
        # Iterate over all instance files in the input folder
        for path_instance in input/instances/*.lp;
        do
	        instance_name=$(basename "$path_instance" .lp)
	        instance_names+=($instance_name)
        done
# Terminate if instance directory is empty
else
        echo "No .lp instances in input folder."
        exit 1
fi


# Create output directories
mkdir -p "output"
mkdir -p "output_slurm"


# Iterate over discretization sizes
for disc_size in ${disc_sizes[@]} 
do
	# Create algorithm output directory
	if [ "$algorithm" == "disc" ]; then
		dir_output="output/${algorithm}_${disc_type}_${disc_quad_variables}_${disc_size}"
	elif [ "$algorithm" == "qcp-solver" ]; then
		dir_output="output/${algorithm}_${qcp_solver}"
	fi
	mkdir -p "${dir_output}"

	# Solve instances
	for instance_name in ${instance_names[@]}
	do
		mkdir -p "${dir_output}/${instance_name}"
		
		if [ "$use_slurm" == 1 ]; then
			sbatch --mem=$memory solve_instance.sh "$instance_name" "$algorithm" "$disc_type" "$disc_quad_variables" "$qcp_solver" "$disc_size"
		else
			./solve_instance.sh "$instance_name" "$algorithm" "$disc_type" "$disc_quad_variables" "$qcp_solver" "$disc_size"
		fi
	done
done

