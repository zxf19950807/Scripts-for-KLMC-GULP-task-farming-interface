import os
import glob
import concurrent.futures
import numpy as np
import shutil
import pandas as pd

max_workers = 100

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

# File paths for output
energy_origin_path = "energy_origin.txt"
energy_filtered_path = "energy_filtered.txt"

# Headers for the output files
header = "Energy Gnorm a b c alpha beta gamma V Density Static_xx Static_yy Static_zz ε0 HighFreq_xx HighFreq_yy HighFreq_zz ε∞ Bulk0 Shear0 Young0 C11 C12 C44 V_O_min V_O_max V_O_avg V_La_min V_La_max V_La_avg V_Ce_min V_Ce_max V_Ce_avg taskid"

# Get a list of all directories starting with 'A'
dirs = sorted(glob.glob("A*/"))
total_dirs = len(dirs)

# Write headers to the output files
data_string = ""
with open(energy_origin_path, "w") as origin_file, open(energy_filtered_path, "w") as filtered_file:
    origin_file.write(data_string + '\n')
    filtered_file.write(header + "\n")

# Labels and corresponding markers
markers = {
    "dE/de1(xx)": None,
    "dE/de2(yy)": None,
    "dE/de3(zz)": None,
    "dE/de4(yz)": None,
    "dE/de5(xz)": None,
    "dE/de6(xy)": None
}

def convert_to_csv_and_sort(txt_file_path, output_csv_path):
    # Load the data from a text file
    data = pd.read_csv(txt_file_path, delim_whitespace=True)
    
    # Sorting the data by the 'Energy' column
    sorted_data = data.sort_values(by='Energy')
    
    # Writing the sorted data to a CSV file
    sorted_data.to_csv(output_csv_path, index=False)

def extract_and_process_electrostatics(lines):
    data = {"La": [], "Ce": [], "O": []}
    
    # Extracting data
    electrostatic_section = False
    for line in lines:
        if "Electrostatic potential at atomic positions" in line:
            electrostatic_section = True
        if electrostatic_section:
            if 'La    c' in line:
                data["La"].append(float(line.split()[3]))
            elif 'Ce    c' in line:
                data["Ce"].append(float(line.split()[3]))
            elif 'O     c' in line:
                data["O"].append(float(line.split()[3]))

    # Returning the results directly for each requested atom
    results = {}
    for atom in data:
        if data[atom]:  # Check if there is data for the atom
            avg = sum(data[atom]) / len(data[atom])
            max_value = max(data[atom])
            min_value = min(data[atom])
            results[atom] = (avg, max_value, min_value)
        else:
            results[atom] = (0, 0, 0)
    
    return results

def process_directory(dir_path):
    # Variables used inside the loop
    file_path = os.path.join(dir_path, "gulp_klmc.gout")
    taskid = dir_path[1:-1]
    data_string = None
    final_energy = None
    final_gnorm = None
    static_xx = None
    static_yy = None
    static_zz = None
    high_freq_xx = None
    high_freq_yy = None
    high_freq_zz = None
    Volume = None
    Density = None
    epsilon_0 = None
    epsilon_infinity = None
    Bulk0 = None
    Shear0 = None
    Young0 = None
    C11 = None
    C12 = None
    C44 = None
    V_La_avg = None
    V_Ce_avg = None
    V_O_avg = None
    V_La_max = None
    V_Ce_max = None
    V_O_max = None
    V_La_min = None
    V_Ce_min = None
    V_O_min = None

    if os.path.isfile(file_path):
        # Reset markers values
        for key in markers:
            markers[key] = None

        # Read the file line by line
        with open(file_path, "r") as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                try:
                    if "Final energy" in line:
                        final_energy = line.split()[3]
                    elif "Final Gnorm" in line:
                        final_gnorm = line.split()[-1]
                    elif "Non-primitive cell volume =" in line:
                        Volume = line.split()[4]
                    elif "Density of cell = " in line:
                        Density = line.split()[4]
                    elif "Static dielectric constant tensor" in line:
                        static_xx = lines[i+5].split()[1] if is_float(lines[i+5].split()[1]) else None
                        static_yy = lines[i+6].split()[2] if is_float(lines[i+6].split()[2]) else None
                        static_zz = lines[i+7].split()[3] if is_float(lines[i+7].split()[3]) else None
                    elif "High frequency dielectric constant tensor" in line:
                        high_freq_xx = lines[i+5].split()[1] if is_float(lines[i+5].split()[1]) else None
                        high_freq_yy = lines[i+6].split()[2] if is_float(lines[i+6].split()[2]) else None
                        high_freq_zz = lines[i+7].split()[3] if is_float(lines[i+7].split()[3]) else None
                    elif "Bulk  Modulus (GPa)     =" in line:
                        Bulk0 = lines[i].split()[4]
                    elif "Shear Modulus (GPa)     =" in line:
                        Shear0 = lines[i].split()[4]
                    elif "Youngs Moduli (GPa)     =" in line:
                        Young0 = lines[i].split()[4]
                    elif "Elastic Constant Matrix: (Units=GPa)" in line:
                        C11 = lines[i+5].split()[1] if is_float(lines[i+5].split()[1]) else None
                        C12 = lines[i+5].split()[2] if is_float(lines[i+5].split()[2]) else None
                        C44 = lines[i+8].split()[4] if is_float(lines[i+8].split()[4]) else None
                    else:
                        for key in markers:
                            if key in line:
                                markers[key] = line.split()[1]

                except (IndexError, ValueError) as e:
                    print(f"Error processing file {file_path} at line {i+1}: {e}")
                    continue

        # Grep Electrostatics
        start_index = next((i for i, line in enumerate(lines) if "Electrostatic potential at atomic positions" in line), None)
        
        if start_index is not None:
            results = extract_and_process_electrostatics(lines)
            V_La_avg, V_La_max, V_La_min = results["La"]
            V_Ce_avg, V_Ce_max, V_Ce_min = results["Ce"]
            V_O_avg, V_O_max, V_O_min = results["O"]

            # Calculating averages for ε0 and ε∞
            epsilon_0 = sum([float(val) for val in [static_xx, static_yy, static_zz] if val]) / 3
            epsilon_infinity = sum([float(val) for val in [high_freq_xx, high_freq_yy, high_freq_zz] if val]) / 3

# Write to files if the required values are found
    if final_energy and final_gnorm:
        # Constructing the data string
        data_values = [final_energy, final_gnorm] + [str(markers[key]) for key in markers]
        data_string = ' '.join(data_values)
        # Adding Static, High Frequency, and average potential values
        additional_values = [Volume, Density, static_xx, static_yy, static_zz, epsilon_0, high_freq_xx, high_freq_yy, high_freq_zz, epsilon_infinity, Bulk0, Shear0, Young0, C11, C12, C44, V_O_min, V_O_max, V_O_avg, V_La_min, V_La_max, V_La_avg, V_Ce_max, V_Ce_max, V_Ce_avg, taskid]
        data_string += ' ' + ' '.join(map(str, additional_values))
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
for result in results:
    # Check if any value in the result is None
    if "None" not in result:
        with open(energy_origin_path, "a") as origin_file:
            origin_file.write(result + "\n")
    
        if float(result.split()[1]) < 0.001:  # Here, result.split()[2] refers to final_gnorm
            with open(energy_filtered_path, "a") as filtered_file:
                filtered_file.write(result + "\n")

# print("Calculating Partition Function:")
# 
# # Reading the file to check its content
# with open(energy_filtered_path, "r") as file:
#     lines = file.readlines()
# 
# # Extracting energy values from the file (Skipping the header)
# energies = [float(line.split()[1]) for line in lines[1:]]
# 
# # Calculating Weight based on the provided formula
# k_boltzmann = 8.617333262145e-5  # Boltzmann constant in eV/K
# temperature = 300  # Given temperature in K
# 
# min_energy = min(energies)
# weights = np.exp(-(np.array(energies) - min_energy)/ (k_boltzmann * temperature))
# 
# # Calculating Wi
# total_weight = sum(weights)
# wi_values = weights / total_weight
# 
# weights, wi_values
# # Adding the new columns to the existing data
# updated_lines = [lines[0].strip() + " Weight Wi\n"]  # Updating the header
# 
# for index, line in enumerate(lines[1:]):
#     updated_line = line.strip() + f" {weights[index]} {wi_values[index]}\n"
#     updated_lines.append(updated_line)
# 
# # Saving the updated data to a new file
# output_filename = energy_filtered_path
# with open(output_filename, "w") as file:
#     file.writelines(updated_lines)
# output_filename
# 
# # Print contents of energy_origin.txt
# with open(energy_filtered_path, "r") as file:
#     print(file.read())
# 
# print("Done")

# Additional code to copy energy_filtered_path to the specified directory and rename it
energy_txt_path = 'energy_filtered.txt'  
output_csv_path = 'summary.csv'  
convert_to_csv_and_sort(energy_txt_path, output_csv_path)

current_directory_name = os.getcwd().split('/')[-1]
destination_path = f"/mnt/lustre/a2fs-work2/work/e05/e05/uccahaq/klmc/_data/_energy/E_{current_directory_name}_.csv"
shutil.copy2(output_csv_path, destination_path)