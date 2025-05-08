import os
import re
import csv
import concurrent.futures

def process_directory(directory):
    """
    Process a single directory by reading its 'summary_dist.csv' file.
    The directory name is expected to be of the form 'A<number>'.
    Returns a tuple (id_str, result_dict) where id_str is the numeric part
    of the directory name, and result_dict maps each column name (e.g. 'VO_0-5')
    to the corresponding count.
    """
    base = os.path.basename(directory)
    match = re.match(r'^A(\d+)$', base)
    if match:
        id_str = match.group(1)
    else:
        # In case the directory name does not exactly match 'A<number>'
        id_str = ''.join(filter(str.isdigit, base))
    
    result = {}
    csv_path = os.path.join(directory, "summary_dist.csv")
    try:
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bin_range = f"{row['bin_start']}-{row['bin_end']}"
                # Process each species column (skip bin_start and bin_end)
                for key in row:
                    if key in ['bin_start', 'bin_end']:
                        continue
                    col_name = f"{key}_{bin_range}"
                    result[col_name] = int(row[key])
    except Exception as e:
        print(f"Error processing directory {directory}: {e}")
    
    return id_str, result

def main():
    # Find directories in the current folder whose names match 'A' followed by digits
    all_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and re.match(r'^A\d+$', d)]
    total_dirs = len(all_dirs)
    all_results = {}
    processed_count = 0

    # Process directories concurrently using 128 workers
    with concurrent.futures.ProcessPoolExecutor(max_workers=128) as executor:
        future_to_dir = {executor.submit(process_directory, d): d for d in all_dirs}
        for future in concurrent.futures.as_completed(future_to_dir):
            directory = future_to_dir[future]
            try:
                id_str, result = future.result()
                all_results[id_str] = result
            except Exception as exc:
                print(f"Directory {directory} generated an exception: {exc}")
            processed_count += 1
            print(f"Processed {processed_count}/{total_dirs} directories")

    # Compile the set of all column names across all processed directories
    columns_set = set()
    for res in all_results.values():
        columns_set.update(res.keys())
    
    # Establish the order of species as desired and sort the bin columns in ascending order
    species_order = ['VO', 'La', 'Ce', 'O']
    ordered_columns = []
    for species in species_order:
        species_cols = [col for col in columns_set if col.startswith(f"{species}_")]
        species_cols.sort(key=lambda x: int(x.split('_')[1].split('-')[0]))
        ordered_columns.extend(species_cols)
    
    header = ["ID"] + ordered_columns

    # Write the combined results into a single CSV file
    with open("summary_radius_count.csv", "w", newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(header)
        # Sort by numeric ID
        for id_str in sorted(all_results.keys(), key=lambda x: int(x)):
            row = [id_str]
            result = all_results[id_str]
            for col in ordered_columns:
                row.append(result.get(col, ""))
            writer.writerow(row)

if __name__ == "__main__":
    main()
