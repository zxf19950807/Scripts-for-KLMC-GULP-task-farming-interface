import os
import glob
import concurrent.futures
import numpy as np
import shutil
import pandas as pd

max_workers = 128

# File paths for output
energy_origin_path = "energy_origin.txt"
energy_filtered_path = "energy_filtered.txt"

# Headers for the output files
header = "Energy Gnorm first_freq V_O_min V_O_max V_O_avg V_Gd_min V_Gd_max V_Gd_avg V_Ce_min V_Ce_max V_Ce_avg d1x d1y d1z d2x d2y d2z d3x d3y d3z d4x d4y d4z max_displacement taskid"
dirs = sorted(glob.glob("A*/"))
total_dirs = len(dirs)

# Write headers to the output files
data_string = ""
with open(energy_origin_path, "w") as origin_file, open(energy_filtered_path, "w") as filtered_file:
    origin_file.write(data_string + '\n')
    filtered_file.write(header + "\n")

def convert_to_csv_and_sort(txt_file_path, output_csv_path):
    data = pd.read_csv(txt_file_path, delim_whitespace=True)
    sorted_data = data.sort_values(by='Energy')
    sorted_data.to_csv(output_csv_path, index=False)

def extract_max_displacement(lines):
    max_displacements = []
    for i, line in enumerate(lines):
        if "Difference" in line:
            data_block = lines[i+1:i+640]
            differences = [float(line.split()[4]) for line in data_block if len(line.split()) >= 5]
            if differences:
                max_displacement = max(differences, key=abs)
                max_displacements.append(max_displacement)
     
    return max(max_displacements, key=abs) if max_displacements else None
 
def extract_and_process_electrostatics(lines):
    data = {"Gd": [], "Ce": [], "O": []}
    electrostatic_section = False
    for line in lines:
        if "Electrostatic site potentials for region 1" in line:
            electrostatic_section = True
        if electrostatic_section:
            if 'Gd    c ' in line:
                data["Gd"].append(float(line.split()[3]))
            elif 'Ce    c ' in line:
                data["Ce"].append(float(line.split()[3]))
            elif 'O     c ' in line:
                data["O"].append(float(line.split()[3]))
    results = {}
    for atom in data:
        if data[atom]: 
            avg = sum(data[atom]) / len(data[atom])
            max_value = max(data[atom])
            min_value = min(data[atom])
            results[atom] = (avg, max_value, min_value)
        else:
            results[atom] = (0, 0, 0)
    
    return results

def extract_coordinates(gin_file_path):
    coordinates = []
    with open(gin_file_path, "r") as file:
        lines = file.readlines()
        for line in lines:
            if "impurity Gd cart" in line:
                # Extracting the last three values as x, y, z
                coords = list(map(float, line.split()[-3:]))
                coordinates.extend(coords)
    return coordinates

def process_directory(dir_path):
    file_path = os.path.join(dir_path, "gulp_klmc.gout")
    gin_file_path = os.path.join(dir_path, "gulp_klmc.gin")
    taskid = dir_path.strip('/').split('/')[-1]
    data_string = ""
    final_energy = None
    final_gnorm = None
    first_freq = None
    V_Gd_avg = None
    V_Ce_avg = None
    V_O_avg = None
    V_Gd_max = None
    V_Ce_max = None
    V_O_max = None
    V_Gd_min = None
    V_Ce_min = None
    V_O_min = None
    d1x, d1y, d1z = None, None, None
    d2x, d2y, d2z = None, None, None
    d3x, d3y, d3z = None, None, None
    d4x, d4y, d4z = None, None, None
    max_displacement = 0

    if os.path.isfile(file_path) and os.path.isfile(gin_file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
            max_displacement = extract_max_displacement(lines)  # Correctly call this function
            for i, line in enumerate(lines):
                try:
                    if "Final defect energy" in line:
                        final_energy = line.split('=')[-1].strip()
                    elif "Final defect Gnorm" in line:
                        final_gnorm = line.split('=')[-1].strip()
                    elif "Frequencies (cm-1)" in line:
                        # Ensure the next line is empty and then extract the first frequency from the following line
                        if lines[i+2].strip():
                            first_freq = lines[i+2].split()[0]  # Assuming space-separated values, extract the first one
                except (IndexError, ValueError) as e:
                    print(f"Error processing file {file_path} at line {i+1}: {e}")
                    continue

        start_index = next((i for i, line in enumerate(lines) if "Electrostatic site potentials for region 1" in line), None)
        
        if start_index is not None:
            results = extract_and_process_electrostatics(lines)
            V_Gd_avg, V_Gd_max, V_Gd_min = results["Gd"]
            V_Ce_avg, V_Ce_max, V_Ce_min = results["Ce"]
            V_O_avg, V_O_max, V_O_min = results["O"]

        # Extract coordinates from the gin file
        coordinates = extract_coordinates(gin_file_path)
        if len(coordinates) == 12:  # Check if we have exactly 4 lines of coordinates
            d1x, d1y, d1z = coordinates[0:3]
            d2x, d2y, d2z = coordinates[3:6]
            d3x, d3y, d3z = coordinates[6:9]
            d4x, d4y, d4z = coordinates[9:12]

    # Write to files if the required values are found
    if final_energy and final_gnorm and len(coordinates) == 12:
        # Construct the data string
        data_string = f"{final_energy} {final_gnorm} {first_freq} {V_O_min} {V_O_max} {V_O_avg} {V_Gd_min} {V_Gd_max} {V_Gd_avg} {V_Ce_min} {V_Ce_max} {V_Ce_avg} {d1x} {d1y} {d1z} {d2x} {d2y} {d2z} {max_displacement} {taskid}"
    return data_string

# Process directories in parallel using ProcessPoolExecutor with max 128 workers
results = []
with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
    future_to_dir = {executor.submit(process_directory, dir): dir for dir in dirs}
    for future in concurrent.futures.as_completed(future_to_dir):
        dir = future_to_dir[future]
        try:
            result = future.result()
            if result:  # Check if the result is not None
                results.append(result)
                # Print progress along with the current directory name
                print(f"Processed directory {dir} ({len(results)} out of {total_dirs} directories, {len(results) / total_dirs * 100:.2f}% complete).")
        except Exception as exc:
            print(f"{dir} generated an exception: {exc}")
             
# After processing all directories, write the results to the files
passed_count = 0
failed_count = 0

for result in results:
    # Check if any value in the result is None
    if "None" not in result:
        with open(energy_origin_path, "a") as origin_file:
            origin_file.write(result + "\n")

        # Condition for the second part (energy value)
        if float(result.split()[1]) < 1E-6:
            # Try to evaluate the third part (may be a number or a non-numeric string)
            try:
                value = float(result.split()[2])
                condition = value >= 0  # Condition to check if the value is non-negative
            except ValueError:
                condition = False  # If it's a non-numeric string, fail the condition

            # Additional condition for the second last element
            second_last_value = float(result.split()[-2])
            if abs(second_last_value) > 2:
                condition = False

            # Write to filtered file if conditions are met
            if condition:
                with open(energy_filtered_path, "a") as filtered_file:
                    filtered_file.write(result + "\n")
                passed_count += 1
            else:
                failed_count += 1
        else:
            failed_count += 1
    else:
        failed_count += 1
 

# At the end of the loop, you can print or log the counts
print(f"Number of results that passed: {passed_count}")
print(f"Number of results that failed: {failed_count}")


# Convert to CSV and copy the final result to the specified directory
energy_txt_path = 'energy_filtered.txt'  
output_csv_path = 'summary.csv'  
convert_to_csv_and_sort(energy_txt_path, output_csv_path)

current_directory_name = os.getcwd().split('/')[-1]
destination_path = f"/mnt/lustre/a2fs-work2/work/e05/e05/uccahaq/klmc/_data_doped_ML_ok/_energy_data/E_{current_directory_name}_.csv"
shutil.copy2(output_csv_path, destination_path)
