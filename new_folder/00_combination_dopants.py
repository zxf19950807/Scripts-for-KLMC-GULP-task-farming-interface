import os
from itertools import combinations

def generate_all_combinations(input_filepath):
    # Read the input file
    with open(input_filepath, 'r') as file:
        lines = file.readlines()
    
    # Data lines are lines 22 to 43
    data_lines = lines[21:43]

    # Parts of the file to keep
    part_before = lines[:21]
    part_after = lines[43:]

    # Get current working directory
    current_directory = os.getcwd()
    output_folder = os.path.join(current_directory, 'run')
    
    # Ensure the output directory exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Generate files for each combination of 3 data lines
    all_combinations = list(combinations(data_lines, 4))
    print(f"Total combinations: {len(all_combinations)}")
    
    # Generate each new .gin file
    for i, combination in enumerate(all_combinations):
        filename = os.path.join(output_folder, f"A{i}.gin")
        print(i)
        
        # Write the parts before, selected lines, and parts after to a new file
        with open(filename, 'w') as new_file:
            new_file.writelines(part_before + list(combination) + part_after)

# Example usage
input_filepath = 'defect.gin'  # Update this path to the location of your defect.gin file
generate_all_combinations(input_filepath)
