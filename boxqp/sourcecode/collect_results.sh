#!/bin/bash
#
# Author: Sascha Kuhnke
# Created: 29.07.2020


# Collect instance names
instance_names=()

# Check if instance directory contains .lp instances
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
        exit 1
fi


# Collect paths of algorithm result files
path_algorithm_result_files=()

# Iterate over all directories in the output folder
for dir in output/*/
do
	dir_output=$(basename $dir)
	dir_output="output/${dir_output}"

	# Initialize algorithm results file
	path_algorithm_results="${dir_output}.ods"
	path_algorithm_result_files+=($path_algorithm_results)
	rm -f $path_algorithm_results
	sed -n 1p "${dir_output}/${instance_names[0]}/results.csv" > $path_algorithm_results

	# Collect results
	for instance_name in ${instance_names[@]}
	do
		sed -n 2p "${dir_output}/${instance_name}/results.csv" >> $path_algorithm_results
	done

	# Add averages to results file
	python3.6 src/input_output/main_add_averages.py $dir_output
done


# Create overall results file
python3.6 src/input_output/main_collect_overall_results.py ${path_algorithm_result_files[@]}
