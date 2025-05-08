import numpy as np

def read_xyz(file_path):
    """ Read the XYZ file and extract atom types and coordinates. """
    with open(file_path, 'r') as file:
        content = file.readlines()
    
    atoms = []
    coordinates = []
    for line in content[2:]:  # Skip the header and atom count
        parts = line.split()
        atoms.append(parts[0])
        coordinates.append(np.array(parts[1:], dtype=float))
    
    return atoms, np.array(coordinates)

def compute_coordination_numbers(atoms, coordinates, cutoff=2.7):
    """ Compute coordination numbers based on a cutoff distance, considering only interactions between Ce and O atoms. """
    num_atoms = len(atoms)
    cns = np.zeros(num_atoms, dtype=int)
    types = {'Ce': 'O', 'O': 'Ce'}  # Define interactions between different atom types
    
    for i in range(num_atoms):
        distances = np.linalg.norm(coordinates - coordinates[i], axis=1)
        for j in range(num_atoms):
            if atoms[i] != atoms[j] and distances[j] <= cutoff and atoms[j] == types[atoms[i]]:
                cns[i] += 1
    
    return cns

def classify_atoms(atoms, coordination_numbers):
    """ Classify atoms as 'surface' or 'bulk' based on coordination numbers. """
    classified_atoms = []
    for atom, cn in zip(atoms, coordination_numbers):
        if atom == 'Ce':
            category = 'surface' if cn < 8 else 'bulk' if cn >= 8'
        elif atom == 'O':
            category = 'surface' if cn < 4 else 'bulk' if cn >= 4'
        classified_atoms.append(category)
    
    return classified_atoms

def write_xyz(atoms, coordinates, coordination_numbers, classified_atoms, output_path):
    """ Write the modified data to a new XYZ file. """
    with open(output_path, 'w') as file:
        file.write(f"{len(atoms)}\n")
        file.write("Atoms with coordination numbers and classification\n")
        for atom, coord, cn, category in zip(atoms, coordinates, coordination_numbers, classified_atoms):
            line = f"{atom} {' '.join(map(str, coord))} {cn} {category}\n"
            file.write(line)

# Main execution
if __name__ == "__main__":
    input_path = 'input.xyz'
    output_path = 'output.xyz'
    
    atoms, coordinates = read_xyz(input_path)
    coordination_numbers = compute_coordination_numbers(atoms, coordinates)
    classified_atoms = classify_atoms(atoms, coordination_numbers)
    write_xyz(atoms, coordinates, coordination_numbers, classified_atoms, output_path)
    print("XYZ data processed and saved.")
