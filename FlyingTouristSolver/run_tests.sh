#!/bin/bash

# Folders
input_folder="proj1_public_instances"
output_folder="out"

# Create output folder if it doesn't exist
mkdir -p "$output_folder"

# Loop through the test cases from 01 to 16
for i in {01..16}; do
    input_file="$input_folder/t$i.ttp"
    output_file="$output_folder/t$i.out"
    expected_output_file="$input_folder/t$i.out"

    # Run the python script and redirect the output
    python3 proj1.py < "$input_file" > "$output_file"

    # Compare the generated output with the expected output
    echo "Comparing t$i.out..."
    diff "$expected_output_file" "$output_file"

    # Check if diff found differences
    if [ $? -eq 0 ]; then
        echo "Test t$i: Passed"
    else
        echo "Test t$i: Failed"
    fi

    echo
done
