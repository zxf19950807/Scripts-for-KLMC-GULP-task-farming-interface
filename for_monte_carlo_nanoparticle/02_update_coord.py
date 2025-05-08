import os
import concurrent.futures
import math

def read_gulp_res(filepath):
    """
    Reads optimised coordinates from gulp.res.
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Find the start of the cartesian coordinates
    start_idx = next(i for i, line in enumerate(lines) if line.strip().startswith('cartesian')) + 1

    # Extract coordinates until the second column is not 'core'
    coordinates = []
    for line in lines[start_idx:]:
        tokens = line.split()
        if len(tokens) < 5 or tokens[1] != 'core':
            break
        # Handle potential fractional coordinates
        coords = []
        for token in tokens[2:5]:
            if '/' in token:
                num, denom = map(float, token.split('/'))
                coords.append(num / denom)
            else:
                coords.append(float(token))
        coordinates.append((tokens[0], *coords))

    return coordinates

def calculate_distance(x, y, z, ref_point):
    """
    Calculates the Euclidean distance from a point to the reference point.
    """
    return math.sqrt((x - ref_point[0])**2 + (y - ref_point[1])**2 + (z - ref_point[2])**2)

def update_coordinates(file_path, atom_type, new_coords, ref_point):
    """
    Updates the coordinates and distance column in the given file.
    """
    updated_lines = []
    index = 0  # Tracks position in new_coords
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        tokens = line.split()
        if len(tokens) < 6 or tokens[0] != atom_type:
            updated_lines.append(line)
            continue
        
        # Update XYZ coordinates
        new_x, new_y, new_z = new_coords[index][1:]
        index += 1
        
        # Calculate new distance
        new_distance = calculate_distance(new_x, new_y, new_z, ref_point)
        
        updated_line = (
            f"{tokens[0]} {new_x:.8f} {new_y:.8f} {new_z:.8f} "
            f"{new_distance:.2f} " + " ".join(tokens[5:]) + "\n"
        )
        updated_lines.append(updated_line)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.writelines(updated_lines)

def update_vo_opt(file_path, ref_point):
    """
    Updates the distance column in VO_opt.txt.
    """
    updated_lines = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        tokens = line.split()
        if len(tokens) < 6:
            updated_lines.append(line)
            continue
        
        x, y, z = map(float, tokens[1:4])
        new_distance = calculate_distance(x, y, z, ref_point)
        
        updated_line = (
            f"{tokens[0]} {x:.8f} {y:.8f} {z:.8f} "
            f"{new_distance:.2f} " + " ".join(tokens[5:]) + "\n"
        )
        updated_lines.append(updated_line)
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.writelines(updated_lines)

def process_directory(directory, ref_point):
    """
    Processes a single directory containing gulp.res and associated text files.
    Returns the directory name for reference in main.
    """
    gulp_res_path = os.path.join(directory, 'gulp.res')
    
    if not os.path.exists(gulp_res_path):
        print(f"Warning: {gulp_res_path} not found.")
        return directory
    
    # Read new coordinates from gulp.res
    new_coords = read_gulp_res(gulp_res_path)
    
    # Distribute coordinates by atom type
    atom_coords = {'La': [], 'Ce': [], 'O': []}
    for coord in new_coords:
        if coord[0] in atom_coords:
            atom_coords[coord[0]].append(coord)
    
    # Update the respective text files
    for atom, filename in [('La', 'La.txt'), ('Ce', 'Ce.txt'), ('O', 'O.txt')]:
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            update_coordinates(file_path, atom, atom_coords[atom], ref_point)
    
    # Update VO_opt.txt if present
    vo_file = os.path.join(directory, 'VO_opt.txt')
    if os.path.exists(vo_file):
        update_vo_opt(vo_file, ref_point)
    
    return directory

def main():
    base_path = '.'
    directories = [
        d for d in os.listdir(base_path) 
        if os.path.isdir(os.path.join(base_path, d)) and d.startswith('A')
    ]
    reference_point = (-24.286268, 24.268838, -24.273662)
    
    # Multi-threaded processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=128) as executor:
        futures = [
            executor.submit(process_directory, os.path.join(base_path, d), reference_point)
            for d in directories
        ]
        
        # Provide basic progress by printing when a directory finishes
        finished_count = 0
        total = len(directories)
        
        for future in concurrent.futures.as_completed(futures):
            dir_processed = future.result()
            finished_count += 1
            print(f"Processed directory '{dir_processed}' ({finished_count}/{total})")

    print("Update complete.")

if __name__ == "__main__":
    main()
