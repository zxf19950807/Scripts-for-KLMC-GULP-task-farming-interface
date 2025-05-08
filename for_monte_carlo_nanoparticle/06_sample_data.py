import pandas as pd
import os

# Step 1: Read specific rows from the 'summary.csv' and extract the 'taskid' column
def read_task_ids():
    df = pd.read_csv('summary.csv')
    total_rows = len(df)
    
    # Calculate number of entries in each group, ensuring at least 1 member
    group_size = max(total_rows // 10, 1)

    # Select Top 10%
    ids_part1 = df.iloc[:group_size]['taskid'].tolist()

    # Select Mid 10%
    mid_start = max(total_rows // 2 - group_size // 2, 0)
    mid_end = min(mid_start + group_size, total_rows)
    ids_part2 = df.iloc[mid_start:mid_end]['taskid'].tolist()

    # Select Last 10%
    ids_part3 = df.iloc[-group_size:]['taskid'].tolist()

    return ids_part1, ids_part2, ids_part3


# Step 2 and 3: Function to process files in directories corresponding to taskids
def process_tasks(ids, output_file):
    if not ids:
        print(f"No task IDs available for {output_file}.")
        return
    
    sum_df = pd.DataFrame()  # Initialize an empty DataFrame

    for taskid in ids:
        dir_name = f'A{taskid}'
        file_path = os.path.join(dir_name, 'summary_dist.csv')
        if os.path.exists(file_path):
            try:
                # Read the CSV file
                data = pd.read_csv(file_path)
                # We keep 'bin_start' and 'bin_end' intact and sum only the necessary columns
                if sum_df.empty:
                    sum_df = data  # If sum_df is empty, initialize it with data
                else:
                    sum_df[['VO', 'La', 'Ce', 'O']] += data[['VO', 'La', 'Ce', 'O']]
            except Exception as e:
                print(f'Error processing {file_path}: {e}')

    if not sum_df.empty:
        sum_df.to_csv(output_file, index=False)
        print(f'Data summed and saved to {output_file}')
    else:
        print(f"No data to save for {output_file}.")

# Main function to coordinate the steps
def main():
    ids_part1, ids_part2, ids_part3 = read_task_ids()
    process_tasks(ids_part1, 'output_radius_top.csv')
    process_tasks(ids_part2, 'output_radius_mid.csv')
    process_tasks(ids_part3, 'output_radius_last.csv')

if __name__ == '__main__':
    main()
