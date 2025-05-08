import os
import glob
import csv
import concurrent.futures
import numpy as np
import pandas as pd
import shutil

max_workers = 128

# File paths for output
energy_origin_path = "energy_origin.txt"
energy_filtered_path = "energy_filtered.txt"
header = "task Energy Gnorm d_La_avg d_VO_avg La_25 La_50 La_75 VO_25 VO_50 VO_75 VO_bulk VO_surface Ce_bulk Ce_surface O_bulk O_surface La_bulk La_surface ratio_VO_bulk ratio_La_bulk ratio_VO_surface ratio_La_surface ratio_bulk ratio_surface d_VO_La1_bulk d_VO_La1_surface d_VO_La1_total d_VO_La2_bulk d_VO_La2_surface d_VO_La2_total d_VO_VO_bulk d_VO_VO_surface d_VO_VO_total d_La_La_bulk d_La_La_surface d_La_La_total n_2N_bulk n_2N_surface n_3N_bulk n_3N_surface n_fN_bulk n_fN_surface n2_2N_bulk n2_2N_surface n2_3N_bulk n2_3N_surface n2_fN_bulk n2_fN_surface n_VO_100_bulk n_VO_100_surface n_VO_110_bulk n_VO_110_surface n_VO_111_bulk n_VO_111_surface n_VO_far_bulk n_VO_far_surface n_La_1N_bulk n_La_1N_surface n_La_2N_bulk n_La_2N_surface n_La_far_bulk n_La_far_surface taskid"

# Update the directories list
dirs = sorted(glob.glob("A*/"))
total_dirs = len(dirs)

# Write headers to the output files
with open(energy_origin_path, "w") as origin_file, open(energy_filtered_path, "w") as filtered_file:
    origin_file.write(header + "\n")
    filtered_file.write(header + "\n")

def count_types(file_path):
    try:
        with open(file_path, "r") as file:
            content = file.read()
        bulk_count = content.count("bulk")
        surface_count = content.count("surface")
        return bulk_count, surface_count
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, 0

def read_and_compute_statistics(file_path):
    try:
        data = pd.read_csv(file_path, sep=r'\s+', header=None)
        percentiles = np.percentile(data[4], [25, 50, 75])  # Calculate percentiles
        avg_value = data[4].mean()

        bulk_mask = data[6] == "bulk"
        surface_mask = data[6] == "surface"

        if 'VO.txt' in file_path:
            d_VO_La1_bulk = data.loc[bulk_mask, 7].mean()
            d_VO_La1_surface = data.loc[surface_mask, 7].mean()
            d_VO_La1_total = data[7].mean()
            d_VO_La2_bulk = data.loc[bulk_mask, 8].mean()
            d_VO_La2_surface = data.loc[surface_mask, 8].mean()
            d_VO_La2_total = data[8].mean()
            d_VO_VO_bulk = data.loc[bulk_mask, 11].mean()
            d_VO_VO_surface = data.loc[surface_mask, 11].mean()
            d_VO_VO_total = data[11].mean()
            
            n_2N_bulk = data.loc[bulk_mask, 9].sum().count('2N')
            n_2N_surface = data.loc[surface_mask, 9].sum().count('2N')
            n_3N_bulk = data.loc[bulk_mask, 9].sum().count('3N')
            n_3N_surface = data.loc[surface_mask, 9].sum().count('3N')
            n_fN_bulk = data.loc[bulk_mask, 9].sum().count('fN')
            n_fN_surface = data.loc[surface_mask, 9].sum().count('fN')
            n2_2N_bulk = data.loc[bulk_mask, 10].sum().count('2N')
            n2_2N_surface = data.loc[surface_mask, 10].sum().count('2N')
            n2_3N_bulk = data.loc[bulk_mask, 10].sum().count('3N')
            n2_3N_surface = data.loc[surface_mask, 10].sum().count('3N')
            n2_fN_bulk = data.loc[bulk_mask, 10].sum().count('fN')
            n2_fN_surface = data.loc[surface_mask, 10].sum().count('fN')
            n_VO_100_bulk = data.loc[bulk_mask, 12].sum().count('VO_100')
            n_VO_100_surface = data.loc[surface_mask, 12].sum().count('VO_100')
            n_VO_110_bulk = data.loc[bulk_mask, 12].sum().count('VO_110')
            n_VO_110_surface = data.loc[surface_mask, 12].sum().count('VO_110')
            n_VO_111_bulk = data.loc[bulk_mask, 12].sum().count('VO_111')
            n_VO_111_surface = data.loc[surface_mask, 12].sum().count('VO_111')
            n_VO_far_bulk = data.loc[bulk_mask, 12].sum().count('VO_far')
            n_VO_far_surface = data.loc[surface_mask, 12].sum().count('VO_far')  
            
            return avg_value, percentiles, d_VO_La1_bulk, d_VO_La1_surface, d_VO_La1_total, d_VO_La2_bulk, d_VO_La2_surface, d_VO_La2_total, d_VO_VO_bulk, d_VO_VO_surface, d_VO_VO_total, n_2N_bulk, n_2N_surface, n_3N_bulk, n_3N_surface, n_fN_bulk, n_fN_surface, n2_2N_bulk, n2_2N_surface, n2_3N_bulk, n2_3N_surface, n2_fN_bulk, n2_fN_surface, n_VO_100_bulk, n_VO_100_surface, n_VO_110_bulk, n_VO_110_surface, n_VO_111_bulk, n_VO_111_surface, n_VO_far_bulk, n_VO_far_surface

        elif 'La.txt' in file_path:
            d_La_La_bulk = data.loc[bulk_mask, 7].mean()
            d_La_La_surface = data.loc[surface_mask, 7].mean()
            d_La_La_total = data[7].mean()
            n_La_1N_bulk = data.loc[bulk_mask, 8].sum().count('La_1N')
            n_La_1N_surface = data.loc[surface_mask, 8].sum().count('La_1N')
            n_La_2N_bulk = data.loc[bulk_mask, 8].sum().count('La_2N')
            n_La_2N_surface = data.loc[surface_mask, 8].sum().count('La_2N')
            n_La_far_bulk = data.loc[bulk_mask, 8].sum().count('La_far')
            n_La_far_surface = data.loc[surface_mask, 8].sum().count('La_far')
            
            return avg_value, percentiles, d_La_La_bulk, d_La_La_surface, d_La_La_total, n_La_1N_bulk, n_La_1N_surface, n_La_2N_bulk, n_La_2N_surface, n_La_far_bulk, n_La_far_surface

        return avg_value, percentiles, None

    except Exception as e:
        print(f"Failed to read or process {file_path}: {e}")
        return None, None, None

def convert_to_csv_and_sort(txt_file_path, output_csv_path):
    try:
        data = pd.read_csv(txt_file_path, sep=r'\s+')
        sorted_data = data.sort_values(by='Energy')
        sorted_data.to_csv(output_csv_path, index=False)
    except Exception as e:
        print(f"Error in converting and sorting file {txt_file_path}: {e}")

def process_directory(dir_path):
    file_path = os.path.join(dir_path, "gulp_klmc.gout")
    gin_file_path = os.path.join(dir_path, "gulp_klmc.gin")
    taskid = dir_path[1:-1]
    final_energy = None
    final_gnorm = None
    
    la_file_path = os.path.join(dir_path, "La.txt")
    d_La_avg, la_percentiles, d_La_La_bulk, d_La_La_surface, d_La_La_total, n_La_1N_bulk, n_La_1N_surface, n_La_2N_bulk, n_La_2N_surface, n_La_far_bulk, n_La_far_surface = read_and_compute_statistics(la_file_path)
    La_bulk, La_surface = count_types(la_file_path)
    
    vo_file_path = os.path.join(dir_path, "VO.txt")
    d_VO_avg, vo_percentiles, d_VO_La1_bulk, d_VO_La1_surface, d_VO_La1_total, d_VO_La2_bulk, d_VO_La2_surface, d_VO_La2_total, d_VO_VO_bulk, d_VO_VO_surface, d_VO_VO_total, n_2N_bulk, n_2N_surface, n_3N_bulk, n_3N_surface, n_fN_bulk, n_fN_surface, n2_2N_bulk, n2_2N_surface, n2_3N_bulk, n2_3N_surface, n2_fN_bulk, n2_fN_surface, n_VO_100_bulk, n_VO_100_surface, n_VO_110_bulk, n_VO_110_surface, n_VO_111_bulk, n_VO_111_surface, n_VO_far_bulk, n_VO_far_surface = read_and_compute_statistics(vo_file_path)
    VO_bulk, VO_surface = count_types(vo_file_path)

    ce_file_path = os.path.join(dir_path, "Ce.txt")
    Ce_bulk, Ce_surface = count_types(ce_file_path)

    o_file_path = os.path.join(dir_path, "O.txt")
    O_bulk, O_surface = count_types(o_file_path)
    
    if os.path.isfile(file_path) and os.path.isfile(gin_file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if "Final energy" in line:
                    final_energy = line.split()[-2]
                elif "Final Gnorm" in line:
                    final_gnorm = line.split()[-1]
                
    # Calculate the new ratios
    ratio_VO_bulk = VO_bulk / (VO_bulk + O_bulk) if (VO_bulk + O_bulk) != 0 else 0
    ratio_La_bulk = La_bulk / (La_bulk + Ce_bulk) if (La_bulk + Ce_bulk) != 0 else 0
    ratio_VO_surface = VO_surface / (VO_surface + O_surface) if (VO_surface + O_surface) != 0 else 0
    ratio_La_surface = La_surface / (La_surface + Ce_surface) if (La_surface + Ce_surface) != 0 else 0
    ratio_bulk = ratio_La_bulk / ratio_VO_bulk / 2 if ratio_VO_bulk != 0 else 0
    ratio_surface = ratio_La_surface / ratio_VO_surface / 2 if ratio_VO_surface != 0 else 0
    
    if final_energy and final_gnorm and d_La_avg is not None and d_VO_avg is not None:
        data_string = f"{taskid} {final_energy} {final_gnorm} {d_La_avg:.2f} {d_VO_avg:.2f} {la_percentiles[0]:.2f} {la_percentiles[1]:.2f} {la_percentiles[2]:.2f} {vo_percentiles[0]:.2f} {vo_percentiles[1]:.2f} {vo_percentiles[2]:.2f} {VO_bulk} {VO_surface} {Ce_bulk} {Ce_surface} {O_bulk} {O_surface} {La_bulk} {La_surface} {ratio_VO_bulk:.4f} {ratio_La_bulk:.4f} {ratio_VO_surface:.4f} {ratio_La_surface:.4f} {ratio_bulk:.4f} {ratio_surface:.4f} {d_VO_La1_bulk:.4f} {d_VO_La1_surface:.4f} {d_VO_La1_total:.4f} {d_VO_La2_bulk:.4f} {d_VO_La2_surface:.4f} {d_VO_La2_total:.4f} {d_VO_VO_bulk:.4f} {d_VO_VO_surface:.4f} {d_VO_VO_total:.4f} {d_La_La_bulk:.4f} {d_La_La_surface:.4f} {d_La_La_total:.4f} {n_2N_bulk} {n_2N_surface} {n_3N_bulk} {n_3N_surface} {n_fN_bulk} {n_fN_surface} {n2_2N_bulk} {n2_2N_surface} {n2_3N_bulk} {n2_3N_surface} {n2_fN_bulk} {n2_fN_surface} {n_VO_100_bulk} {n_VO_100_surface} {n_VO_110_bulk} {n_VO_110_surface} {n_VO_111_bulk} {n_VO_111_surface} {n_VO_far_bulk} {n_VO_far_surface} {n_La_1N_bulk} {n_La_1N_surface} {n_La_2N_bulk} {n_La_2N_surface} {n_La_far_bulk} {n_La_far_surface} {taskid}"
        return data_string
    return None

# Process directories and handle exceptions
results = []
retained_count = 0  # Counter for retained entries

with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
    future_to_dir = {executor.submit(process_directory, dir): dir for dir in dirs}
    for future in concurrent.futures.as_completed(future_to_dir):
        dir = future_to_dir[future]
        try:
            result = future.result()
            if result:
                results.append(result)
                print(f"Processed directory {dir} ({len(results)} out of {total_dirs} directories, {len(results) / total_dirs * 100:.2f}% complete).")
        except Exception as exc:
            print(f"{dir} generated an exception: {exc}")

# Write results to the files and handle final operations
for result in results:
    if "None" not in result:
        with open(energy_origin_path, "a") as origin_file:
            origin_file.write(result + "\n")
    
        if float(result.split()[2]) < 0.001:  # Gnorm check
            with open(energy_filtered_path, "a") as filtered_file:
                filtered_file.write(result + "\n")
            retained_count += 1

# Print the number of retained entries
print(f"Total number of retained entries after Gnorm check: {retained_count}")

convert_to_csv_and_sort(energy_filtered_path, 'summary.csv')
shutil.copy2('summary.csv', f"/mnt/lustre/a2fs-work2/work/e05/e05/uccahaq/klmc/_data_NP/_energy_data/E_{os.getcwd().split('/')[-1]}_.csv")

