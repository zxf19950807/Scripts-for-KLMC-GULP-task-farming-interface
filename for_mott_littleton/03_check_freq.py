import os
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed
import re
import shutil

def check_frequency(folder):
    try:
        filename = os.path.join(folder, 'gulp_klmc.gout')
        with open(filename, 'r') as file:
            lines = file.readlines()
        
        # grep Gnorm
        for i, line in enumerate(lines):
            if "Final defect Gnorm" in line:
                final_gnorm = line.split('=')[-1].strip()
        # Find the line containing "Frequencies (cm-1) :"
            elif "Frequencies (cm-1) :" in line:
                # The frequencies are two lines below this line
                frequency_line = lines[i+2].strip()
                if frequency_line:
                    # Extract the first frequency value
                    first_frequency = float(frequency_line.split()[0])
                    # Check if the first frequency is negative
                    if first_frequency < 0 or float(final_gnorm) > 1E-6:
                        return folder
    except Exception as e:
        print(f"Error processing {folder}: {e}")
        return folder
    return None

def main():
    # List all folders starting with 'A' followed by any number
    folders = glob.glob('A*')
    n_folders = len(folders)
    results = []
    completed = 0
    
    # Use 64 parallel workers
    with ProcessPoolExecutor(max_workers=64) as executor:
        future_to_folder = {executor.submit(check_frequency, folder): folder for folder in folders}
        
        for future in as_completed(future_to_folder):
            result = future.result()
            if result:
                results.append(result)
            completed += 1
            print(f"Progress: {completed}/{n_folders} folders checked ({(completed/n_folders)*100:.2f}%)")
    
    # Write folders needing restart to a file
    with open('need_restart.txt', 'w') as f:
        for folder in results:
            f.write(f"{folder}\n")
            
    print(f"Total folders needing restart: {len(results)}")
    print("Completed checking all folders.")

if __name__ == "__main__":
    main()


####################
def copy_and_modify_files():
    # read restart list
    with open('need_restart.txt', 'r') as file:
        folders = [line.strip() for line in file.readlines()]

    # mkdir
    restart_folder = 'run_restart'
    if os.path.exists(restart_folder):
        shutil.rmtree(restart_folder)
    os.makedirs(restart_folder, exist_ok=True)

    # for loop to copy and paste and modify rfo
    for i, folder in enumerate(folders):
        source_file = os.path.join('run', f'{folder}.gin')
        if os.path.exists(source_file):
            destination_file = os.path.join(restart_folder, f'A{i}.gin')  # Reordered file name
            with open(source_file, 'r') as f:
                content = f.read()
            modified_content = content.replace("# switch rfo 0.001", "switch rfo 0.01")
            with open(destination_file, 'w') as f:
                f.write(modified_content)
            print(f"Copied and modified {source_file} to {destination_file}")
        else:
            print(f"File not found: {source_file}")

if __name__ == "__main__":
    copy_and_modify_files()