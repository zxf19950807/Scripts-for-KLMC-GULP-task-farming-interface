import os
import math
from concurrent.futures import ProcessPoolExecutor, as_completed

def distance(coord1, coord2):
    return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2 + (coord1[2] - coord2[2])**2)

def extract_coordinates(content, atom_types):
    coordinates = {}
    for line in content:
        parts = line.strip().split()
        if len(parts) > 5 and parts[0] in atom_types:
            try:
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                CN = parts[-2]
                atom_type = parts[-1]
                coordinates.setdefault(parts[0], []).append((x, y, z, CN, atom_type))
            except ValueError:
                continue
    return coordinates

def master_mapping(content):
    mapping = {}
    for line in content:
        parts = line.strip().split()
        if len(parts) > 5:
            try:
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                CN = parts[-2]
                atom_type = parts[-1]
                mapping[(x, y, z)] = (CN, atom_type)
            except ValueError:
                continue
    return mapping

def compare_and_write(master_coords, master_map, input_directory, output_directory, reference_point):
    gulp_file_path = os.path.join(input_directory, "gulp_klmc.gin")
    
    try:
        with open(gulp_file_path, 'r') as file:
            gulp_content = file.readlines()
        
        gulp_coords = extract_coordinates(gulp_content, ['O', 'La', 'Ce'])
        
        # Determine vacancy oxygen sites
        master_oxygen_coords = set(tuple(coords[:3]) for coords in master_coords['O'])
        gulp_oxygen_coords = set(tuple(coords[:3]) for coords in gulp_coords.get('O', []))
        vacancy_oxygens = master_oxygen_coords - gulp_oxygen_coords

        # Ensure output directory exists
        os.makedirs(output_directory, exist_ok=True)

        # Write the vacancy oxygen coordinates and distances, using CN and type from master_map
        vo_file_path = os.path.join(output_directory, "VO.txt")
        with open(vo_file_path, 'w') as vo_file:
            for coords in vacancy_oxygens:
                if coords not in master_map:
                    continue
                dist = distance(coords, reference_point)
                CN, atom_type = master_map[coords]
                vo_file.write(f"O {coords[0]} {coords[1]} {coords[2]} {dist:.2f} {CN} {atom_type}\n")
                
        # Write the coordinates and distances for 'O', 'La', 'Ce', using CN and type from master_map
        for element in ['O', 'La', 'Ce']:
            file_path = os.path.join(output_directory, f"{element}.txt")
            with open(file_path, 'w') as file:
                for coords in gulp_coords.get(element, []):
                    if coords[:3] not in master_map:
                        continue
                    dist = distance(coords[:3], reference_point)
                    CN, atom_type = master_map[coords[:3]]
                    file.write(f"{element} {coords[0]} {coords[1]} {coords[2]} {dist:.2f} {CN} {atom_type}\n")
        
        return f"Completed: {input_directory}"
    except FileNotFoundError:
        return f"File not found: {gulp_file_path}"

def main():
    base_directory = os.getcwd()
    input_base = os.path.join(base_directory, "_data_rigid")  # Input directories are in ./_data_rigid/
    reference_point = (-24.261094, 24.290531, -24.284251)
    
    # Read master file
    master_gin_path = os.path.join(base_directory, "data/Master_new.gin")
    with open(master_gin_path, 'r') as file:
        master_gin_content = file.readlines()
    master_coords = extract_coordinates(master_gin_content, ['O', 'La', 'Ce'])
    master_map = master_mapping(master_gin_content)  # Create a mapping from coordinates to CN and type
    
    # Find all A* directories in ./_data_rigid/
    input_directories = [os.path.join(input_base, d) for d in os.listdir(input_base)
                         if os.path.isdir(os.path.join(input_base, d)) and d.startswith('A')]
    output_directories = [os.path.join(base_directory, os.path.basename(d)) for d in input_directories]
    
    total = len(input_directories)
    completed = 0
    with ProcessPoolExecutor(max_workers=128) as executor:
        futures = {
            executor.submit(compare_and_write, master_coords, master_map, input_dir, output_dir, reference_point): input_dir
            for input_dir, output_dir in zip(input_directories, output_directories)
        }
        for future in as_completed(futures):
            completed += 1
            result = "completed" if future.result() else "file not found"
            print(f"{result} ({completed}/{total}, {100 * completed / total:.2f}%)")

if __name__ == "__main__":
    main()