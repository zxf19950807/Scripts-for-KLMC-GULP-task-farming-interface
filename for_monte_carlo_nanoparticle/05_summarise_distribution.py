import pandas as pd
import numpy as np
import os
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed

# Define the intervals
binsize = 6
bins = np.arange(0, 30 + binsize, binsize)

def process_file(file_path):
    label = os.path.splitext(os.path.basename(file_path))[0]
    df = pd.read_csv(file_path, sep=r'\s+', header=None, names=['element', 'x', 'y', 'z', 'dist', 'CN', 'type'],usecols=range(7))
    
    # Histogram for distances
    counts, _ = np.histogram(df['dist'], bins=bins)
    index = pd.MultiIndex.from_tuples([(bins[i], bins[i+1]) for i in range(len(bins)-1)], names=['bin_start', 'bin_end'])
    count_df = pd.DataFrame({label: counts}, index=index)
    
    # Counting entries for 'bulk' and 'surface'
    bulk_count = df[df['type'] == 'bulk'].shape[0]
    surface_count = df[df['type'] == 'surface'].shape[0]
    type_df = pd.DataFrame({'Bulk': bulk_count, 'Surface': surface_count}, index=[label])
    
    return count_df, type_df

def compile_results(results, directory, filename, index_label=None):
    summary_table = pd.DataFrame()

    for result in results:
        if summary_table.empty:
            summary_table = result
        else:
            summary_table = pd.concat([summary_table, result], axis=1)

    summary_table.fillna(0, inplace=True)
    summary_table = summary_table.astype(int)
    
    output_file_path = os.path.join(directory, f'{filename}.csv')
    if index_label:
        summary_table.to_csv(output_file_path, sep=',', index_label=index_label)
    else:
        summary_table.to_csv(output_file_path, sep=',')
    return output_file_path

def process_directory(directory):
    file_paths = glob.glob(os.path.join(directory, '[OVCL]*.txt'))
    dist_results = []
    type_results = []
    
    for file in file_paths:
        dist_result, type_result = process_file(file)
        dist_results.append(dist_result)
        type_results.append(type_result)

    dist_file_path = compile_results(dist_results, directory, 'summary_dist', index_label=['bin_start', 'bin_end'])
    type_file_path = compile_results(type_results, directory, 'summary_bulk_surface')
    return dist_file_path, type_file_path

if __name__ == "__main__":
    directories = glob.glob('A*/')
    total_directories = len(directories)
    completed_directories = 0
    
    with ProcessPoolExecutor(max_workers=128) as executor:
        future_to_directory = {executor.submit(process_directory, directory): directory for directory in directories}
        
        for future in as_completed(future_to_directory):
            try:
                dist_path, type_path = future.result()
                completed_directories += 1
                percentage_completed = (completed_directories / total_directories) * 100
                print(f"Progress: {completed_directories}/{total_directories} ({percentage_completed:.2f}%) completed")
            except Exception as exc:
                print(f'Directory {future_to_directory[future]} generated an exception: {exc}')
