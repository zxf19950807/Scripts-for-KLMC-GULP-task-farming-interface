import os
import shutil
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed

max_workers=64

def report_progress(message):
    print(f"[Progress Report] {message}")

def process_error_file(file):
    errors = []
    with open(file, "r") as f_check:
        if "ERROR" in f_check.read():
            errors.append(file.replace("/gulp_klmc.gout", ""))
    return errors

def process_energy_file(file):
    energies = []
    with open(file, "r") as f_check:
        for line in f_check.readlines():
            if "Final energy" in line:
                energies.append(line)
    return energies

def process_name_log(dir):
    if os.path.isdir(dir):
        return dir.replace("./", "")
    return None

def prepare_files(name, num_jobs, i):
    name = name.strip()
    
    # check if restart file exist
    if not os.path.exists(os.path.join(name, "gulp.res")):
        report_progress(f"Skipping {name} - gulp.res not found.")
        return

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
    with open("../../shell_model_potential.txt", "r") as f_src, open(f"{name}.gin", "a") as f_dest:
        f_dest.write(f_src.read())
    shutil.copy(f"{name}.gin", "../../run")
    os.chdir("..")

def main():
    report_progress("Starting conversion...")

    # Step 1: Create directory and move files
    if not os.path.exists("_data_rigid"):
        os.mkdir("_data_rigid")
    for file in glob.glob("A*"):
        shutil.move(file, "_data_rigid/")
    for dir in glob.glob("workgroup*"):
        shutil.rmtree(dir, ignore_errors=True)
    shutil.rmtree("run", ignore_errors=True)
    os.mkdir("run")
    report_progress("Step 1: ok")

    os.chdir("_data_rigid")

    # Step 2: Find error calcs, report previous energy and update name.log
    files = glob.glob("A*/gulp_klmc.gout")

    # Parallel processing for error.txt
    errors = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for result in executor.map(process_error_file, files):
            errors.extend(result)
    with open("error.txt", "w") as f:
        f.writelines("\n".join(errors))

    # Parallel processing for energy.txt
    energies = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for result in executor.map(process_energy_file, files):
            energies.extend(result)
    with open("energy.txt", "w") as f:
        f.writelines(energies)

    dirs = glob.glob("A*")
    names = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for result in executor.map(process_name_log, dirs):
            if result:
                names.append(result)
    with open("name.log", "w") as f:
        f.writelines("\n".join(names))
    
    with open("error.txt", "r") as f1, open("name.log", "r") as f2:
        error_lines = f1.readlines()
        name_lines = f2.readlines()
    with open("name.log_temp", "w") as f:
        for line in name_lines:
            if line not in error_lines:
                f.write(line)
    os.rename("name.log_temp", "name.log")

    num_jobs = sum(1 for line in open("name.log"))
    report_progress(f"number of jobs: {num_jobs}")
    report_progress("Step 2: ok")

    # Step 3: prepare new files
    with open("name.log", "r") as f:
        names = f.readlines()
    tasks = [(name, num_jobs, i) for i, name in enumerate(names)]
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(prepare_files, *zip(*tasks)))

    report_progress("Step 3: ok")
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