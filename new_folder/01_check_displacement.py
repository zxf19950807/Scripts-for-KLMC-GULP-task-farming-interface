import pandas as pd
import os
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
import sys

def process_file(filepath):
    max_differences = []
    with open(filepath, 'r') as file:
        lines = file.readlines()
    
    for i, line in enumerate(lines):
        if "Difference" in line:
            data_block = lines[i+1:i+640]
            differences = [float(line.split()[4]) for line in data_block if len(line.split()) >= 5]
            if differences:
                max_difference = max(differences, key=abs)
                max_differences.append(max_difference)
    
    return max(max_differences, key=abs) if max_differences else None

def process_all_folders_concurrently(root_directory, max_workers=128):
    paths = []
    for root, dirs, files in os.walk(root_directory):
        for file in files:
            if file.endswith('.gout'):
                paths.append(os.path.join(root, file))
    
    total_files = len(paths)
    print(f"Total files to process: {total_files}")

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, path): path for path in paths}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                directory_name = os.path.basename(os.path.dirname(futures[future]))
                results.append((directory_name, result))
            done = len(results)
            print(f"Progress: {done}/{total_files} files processed ({done / total_files * 100:.2f}%)")
    
    # Create a single CSV with all results
    df = pd.DataFrame(results, columns=['Directory', 'Max_Displacement'])
    summary_csv_path = os.path.join(root_directory, 'summary_max_differences.csv')
    df.to_csv(summary_csv_path, index=False)
    return summary_csv_path

# 设置根目录路径
root_directory = os.getcwd()
summary_csv_file = process_all_folders_concurrently(root_directory)
print(f"Summary CSV file created at: {summary_csv_file}")