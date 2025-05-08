import os
import numpy as np
import pandas as pd
from scipy.spatial import KDTree
from scipy.optimize import minimize
import concurrent.futures
cutoff1 = 2.0 # O - O  half
cutoff2 = 3.3  # O - Ce 1 shell
cutoff3 = 3.55  # O - O  1 shell

def process_directory(dir_path):
    """
    This function reads gulp.res and VO.txt from the specified directory,
    corrects VO data by exchanging corresponding atomic information with records from O.txt,
    and then performs in-memory optimisation of the corrected coordinates.
    Finally, it overwrites both VO.txt and O.txt with the final data.
    """

    # Step 1: Read gulp.res to extract oxygen coordinates
    gulp_file_path = os.path.join(dir_path, "gulp.res")
    cartesian_lines = []
    reading_cartesian = False

    with open(gulp_file_path, 'r') as file:
        for line in file:
            if "cartesian" in line.lower():
                reading_cartesian = True
                continue
            if reading_cartesian:
                parts = line.strip().split()
                # Each line should have at least 5 columns: Element, Type, X, Y, Z
                if len(parts) >= 5 and "core" in parts[1].lower():
                    cartesian_lines.append(parts[:5])
                else:
                    break

    gulp_data = pd.DataFrame(cartesian_lines, columns=['Element', 'Type', 'X', 'Y', 'Z'])
    gulp_data[['X', 'Y', 'Z']] = gulp_data[['X', 'Y', 'Z']].astype(float)

    # Collect all oxygen coordinates for reference
    all_oxygen = gulp_data[gulp_data['Element'] == 'O']
    all_oxygen_coords = all_oxygen[['X', 'Y', 'Z']].values.astype(float)

    # Step 2: Load VO.txt
    vo_file_path = os.path.join(dir_path, "VO.txt")
    vo_data = pd.read_csv(vo_file_path, sep=r'\s+', header=None)
    # Assume the original columns are: Element, X, Y, Z, D, CN, Type, ...
    extended_cols = ['Element', 'X', 'Y', 'Z', 'D', 'CN', 'Type']
    if vo_data.shape[1] > len(extended_cols):
        extended_cols += list(range(len(extended_cols), vo_data.shape[1]))
    vo_data.columns = extended_cols
    vo_data = vo_data[vo_data['Element'] == 'O'].reset_index(drop=True)

    # Build a KDTree from all oxygen to search for nearest neighbours
    oxygen_tree = KDTree(all_oxygen_coords)
    vo_coords = vo_data[['X', 'Y', 'Z']].values.astype(float)

    # For each VO site, compute distances to check for implausible positions
    nn_dists = []
    for point in vo_coords:
        indices = oxygen_tree.query_ball_point(point, cutoff2)
        distances = np.linalg.norm(all_oxygen_coords[indices] - point, axis=1)
        nn_dists.append(sorted(distances)[:5])

    # Identify sites with any distance less than 1.5 as implausible
    unreasonable_indices = [i for i, dists in enumerate(nn_dists) if any(dist < cutoff1 for dist in dists)]
    unreasonable_vo_sites = vo_data.iloc[unreasonable_indices]

    # Step 3: Load O.txt to find candidate replacements
    o_file_path = os.path.join(dir_path, "O.txt")
    o_data = pd.read_csv(o_file_path, sep=r'\s+', header=None)
    extended_cols_o = ['Element', 'X', 'Y', 'Z', 'D', 'CN', 'Type']
    if o_data.shape[1] > len(extended_cols_o):
        extended_cols_o += list(range(len(extended_cols_o), o_data.shape[1]))
    o_data.columns = extended_cols_o
    o_data = o_data[o_data['Element'] == 'O'].reset_index(drop=True)
    o_coords = o_data[['X', 'Y', 'Z']].values.astype(float)

    def find_replacement_index(unreasonable_vo_df, all_oxy_coords, o_candidates, cutoff3=3.55):
        replacements = []
        o_tree = KDTree(o_candidates[['X', 'Y', 'Z']].values)  # 构建 KDTree 加速搜索
    
        for i, vo_site in unreasonable_vo_df.iterrows():
            vo_position = vo_site[['X', 'Y', 'Z']].values.astype(float)
            
            # 在 cutoff3 半径内找到所有可能的 O²⁻ 位置
            nearby_indices = o_tree.query_ball_point(vo_position, cutoff3)
            nearby_positions = o_candidates[['X', 'Y', 'Z']].values[nearby_indices]
    
            valid_candidates = []
            for j, candidate_position in enumerate(nearby_positions):
                # 计算候选氧原子到所有其他氧原子的最小距离
                distances = np.linalg.norm(all_oxy_coords - candidate_position, axis=1)
                min_distance_to_others = np.min(distances)  # 找到最小的 O-O 距离
                
                # 计算候选氧原子到 VO 位置的距离
                distance_to_vo = np.linalg.norm(candidate_position - vo_position)
    
                valid_candidates.append({
                    'Index': nearby_indices[j],  # 候选氧原子的索引
                    'Min_Distance': min_distance_to_others,  # 该位置到最近氧原子的最小距离
                    'Distance_to_VO': distance_to_vo  # 该位置到 VO 位置的距离
                })
    
            # 选择具有最大 Min_Distance 的候选氧原子
            if valid_candidates:
                best_candidate = max(valid_candidates, key=lambda x: x['Min_Distance'])
                replacements.append({
                    'VO_Index': vo_site.name,
                    'Replacement_Index': best_candidate['Index']
                })
    
        return replacements

    replacements = find_replacement_index(
        unreasonable_vo_sites, all_oxygen_coords, o_data, cutoff=cutoff3)

    # Exchange corresponding atomic information between VO.txt and O.txt,
    # including 'Element', 'X', 'Y', 'Z', 'D', 'CN', 'Type'
    for swap in replacements:
        vo_idx = int(swap['VO_Index'])
        o_idx = int(swap['Replacement_Index'])
        # Save original VO data
        original_vo = vo_data.loc[vo_idx, ['Element', 'X', 'Y', 'Z', 'D', 'CN', 'Type']].copy()
        # Save candidate record from O.txt
        candidate_o = o_data.loc[o_idx, ['Element', 'X', 'Y', 'Z', 'D', 'CN', 'Type']].copy()

        # Perform the exchange
        vo_data.loc[vo_idx, ['Element', 'X', 'Y', 'Z', 'D', 'CN', 'Type']] = candidate_o
        o_data.loc[o_idx, ['Element', 'X', 'Y', 'Z', 'D', 'CN', 'Type']] = original_vo

    # Step 4: In-memory optimisation
    # Extract cation records from gulp_data
    cation_data = gulp_data[gulp_data['Element'].isin(['Ce', 'La'])]
    cation_coords = cation_data[['X', 'Y', 'Z']].values
    cation_tree = KDTree(cation_coords)

    def count_cation_neighbour(shifted_vo):
        indices = cation_tree.query_ball_point(shifted_vo, cutoff2)
        return len(indices)

    # Build a complete oxygen KDTree to compute distances
    oxygen_coords = all_oxygen[['X', 'Y', 'Z']].values
    oxygen_tree_full = KDTree(oxygen_coords)

    def objective_function(shifted_vo, coord_num):
        if np.any(np.isnan(shifted_vo)) or np.any(np.isinf(shifted_vo)):
            return -np.inf

        cation_dists, _ = cation_tree.query(shifted_vo, k=6)
        o_dists, _ = oxygen_tree_full.query(shifted_vo, k=6)

        if coord_num == 4:
            return np.mean(cation_dists)
        else:
            avg_cation_dist = abs(np.mean(cation_dists) - 2.4)
            max_o_dist = np.max(o_dists)
            return -avg_cation_dist + max_o_dist

    def optimise_vo_position(initial_pos):
        cnum = count_cation_neighbour(initial_pos)
        bounds = [(initial_pos[i] - 1, initial_pos[i] + 1) for i in range(3)]
        result = minimize(
            lambda pos: -objective_function(pos, cnum),
            initial_pos,
            bounds=bounds,
            method='L-BFGS-B',
            options={'eps': 1e-3}
        )
        if result.success:
            return result.x
        else:
            return initial_pos

    # Optimise each VO site
    vo_coords_final = []
    for vo in vo_data[['X', 'Y', 'Z']].values:
        vo_coords_final.append(optimise_vo_position(vo))
    vo_coords_final = np.array(vo_coords_final)

    # Update coordinates in VO data
    vo_data[['X', 'Y', 'Z']] = vo_coords_final

    # Step 5: Overwrite the updated VO.txt and O.txt with final data
    vo_data.to_csv(vo_file_path, sep=' ', index=False, header=False)
    o_data.to_csv(o_file_path, sep=' ', index=False, header=False)

    return dir_path

if __name__ == "__main__":
    base_path = "."  # Or specify another path
    all_dirs = [d for d in os.listdir(base_path) if os.path.isdir(d) and d.startswith("A")]
    total = len(all_dirs)

    with concurrent.futures.ProcessPoolExecutor(max_workers=128) as executor:
        futures = {executor.submit(process_directory, d): d for d in all_dirs}
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            progress = (completed / total) * 100
            print(f"Completed {futures[future]}: {progress:.2f}% processed")
