import os
import shutil
import glob
from concurrent.futures import ProcessPoolExecutor

max_workers=64

def report_progress(message):
    print(f"[Progress Report] {message}")

def process_directory(name, num_jobs, i):
    name = name.strip()
    os.chdir(name)
    report_progress(f"Processing {i+1}/{num_jobs} - {os.getcwd()}")
    with open("gulp.res", "r") as f_check:
        lines = f_check.readlines()
    totalenergy_line = next((i for i, line in enumerate(lines) if "totalenergy" in line), None)
    if totalenergy_line is not None:
        with open(f"{name}.gin", "w") as f:
            f.writelines(lines[:totalenergy_line])
    else:
        species_line = next((i for i, line in enumerate(lines) if "species" in line), None)
        if species_line is not None:
            with open(f"{name}.gin", "w") as f:
                f.writelines(lines[:species_line])
        else:
            shutil.copy("gulp.res", f"{name}.gin")
    with open("../../shell_model_potential_rfo.txt", "r") as f_src, open(f"{name}.gin", "a") as f_dest:
        f_dest.write(f_src.read())
    with open(f"{name}.gin", "r") as f:
        content = f.read().replace("opti ", "opti conp comp prop phonon pot")
    with open(f"{name}.gin", "w") as f:
        f.write(content)
    shutil.copy(f"{name}.gin", "../../run")
    os.chdir("..")

def main():
    report_progress("Starting conversion...")

    # Step 1: Create directory and move files
    os.makedirs("_data_shell_conv", exist_ok=True)
    for file in glob.glob("A*"):
        shutil.move(file, "_data_shell_conv/")
    for dir in glob.glob("workgroup*"):
        shutil.rmtree(dir, ignore_errors=True)
    shutil.rmtree("run", ignore_errors=True)
    os.makedirs("run", exist_ok=True)
    report_progress("Step 1: ok")

    os.chdir("_data_shell_conv")

    dir_names = [d for d in os.listdir(".") if os.path.isdir(d) and d.startswith('A')]
    with open("name.log", "w") as name_log:
        for name in dir_names:
            name_log.write(name + "\n")

    line = len(dir_names)
    report_progress(f"number of jobs: {line}")

    # Step 2: prepare new files (renamed from Step 3 to Step 2 since we deleted the original Step 2)
    tasks = [(name, line, i) for i, name in enumerate(dir_names)]
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(process_directory, *zip(*tasks)))

    report_progress("Step 2: ok")
    report_progress("...done")

if __name__ == "__main__":
    main()

# Function to find empty files in a directory
def find_empty_files(directory):
    # List to store names of empty files
    empty_files = []

    # Check if the directory exists
    if not os.path.exists(directory):
        return f"Directory {directory} does not exist."

    # Check each file in the directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        # Check if it is a file and not a directory
        if os.path.isfile(file_path):
            # Check if the file is empty
            if os.path.getsize(file_path) == 0:
                empty_files.append(filename)

    return empty_files if empty_files else "No empty files found."

# Setting the directory to check as the 'run/' subdirectory in the current working directory
directory_to_check = os.path.join(os.getcwd(), '../run/')
print(find_empty_files(directory_to_check))