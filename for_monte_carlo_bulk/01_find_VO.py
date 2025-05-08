import glob
import re

# Path to the Master.gin file
master_file_path = "../data/Master.gin"

# Read coordinates from Master.gin file
master_coords = set()
with open(master_file_path, "r") as master_file:
    for line in master_file:
        if "0 1 0 1 1 1" in line:
            coords = tuple(line.split()[2:5])
            master_coords.add(coords)

# Get a list of all A*.gin files and sort them by the numerical part of the filename
files = sorted(glob.glob("A*.gin"), key=lambda x: int(re.findall(r'\d+', x)[0]))
total_files = len(files)

# Iterate through sorted A*.gin files
with open("VO_position.txt", "w") as output_file:
    for index, file_path in enumerate(files):
        file_coords = set()
        with open(file_path, "r") as file:
            for line in file:
                if "0 1 0 1 1 1" in line:
                    coords = tuple(line.split()[2:5])
                    file_coords.add(coords)

        # Check if coordinates from Master.gin are missing in the A*.gin file
        missing_coords = master_coords - file_coords
        for coords in missing_coords:
            # Write the name of the A*.gin file (without extension), followed by the missing coordinates
            output_file.write(f"{file_path.split('.')[0]} {' '.join(coords)}\n")

        # Print progress
        print(f"Processed {index + 1} out of {total_files} files ({(index + 1) / total_files * 100:.2f}% complete).")

print("Completed, missing atomic coordinates have been saved to VO_position.txt file.")
