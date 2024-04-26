#!/bin/bash
#
# Author: Sascha Kuhnke
# Created: 19.03.2020


# Use parameters given by the arguments
use_slurm="$1"
formulation="$2"
algorithm="$3"
disc_type="$4"
disc_variant="$5"
qcp_solver="$6"
disc_sizes="$7"


# Set memory for slurm
memory=14000


# Set discretization sizes to zero for non-discretization algorithms
if [ "$algorithm" == "qcp-solver" ]; then
	disc_sizes=("0")
fi


# Collect instance names
instance_names=()

# Check if instance directory contains .dat instances
if ls input/instances/*.dat &>/dev/null 2>&1 
then
        # Iterate over all instance files in the input folder
        for path_instance in input/instances/*.dat;
        do
                instance_name=$(basename "$path_instance" .dat)
                instance_names+=($instance_name)
        done   
# Terminate if instance directory is empty
else
        echo "No .dat instances in input folder."
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
		dir_output="output/${formulation}_${algorithm}_${disc_type}_${disc_variant}_${disc_size}"
	elif [ "$algorithm" == "qcp-solver" ]; then
		dir_output="output/${formulation}_${algorithm}_${qcp_solver}"
	fi
	mkdir -p "${dir_output}"
	
	# Solve instances
	for instance_name in ${instance_names[@]}
	do
		mkdir -p "${dir_output}/${instance_name}"
		
		if [ "$use_slurm" == 1 ]; then
		        sbatch --mem=$memory solve_instance.sh "$instance_name" "$formulation" "$algorithm" "$disc_type" "$disc_variant" "$qcp_solver" "$disc_size"
		else
		        ./solve_instance.sh "$instance_name" "$formulation" "$algorithm" "$disc_type" "$disc_variant" "$qcp_solver" "$disc_size"
		fi
	done
done

