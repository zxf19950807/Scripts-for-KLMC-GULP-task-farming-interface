import os
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

def classify_distance(distance):
    """Classifies the distance between a vacancy and a lanthanum atom into coordination categories."""
    if distance < 3:
        return '2N'
    elif 3 <= distance <= 5:
        return '3N'
    else:
        return 'fN'

def classify_vo_distance(distance):
    """Classifies the nearest vacancy-vacancy (VO-VO) distance into predefined categories."""
    if distance < 3.3:
        return 'VO_100'
    elif 3.3 <= distance < 4.2:
        return 'VO_110'
    elif 4.2 <= distance < 5.1:
        return 'VO_111'
    else:
        return 'VO_far'

def classify_la_distance(distance):
    """Classifies the nearest lanthanum-lanthanum (La-La) distance into predefined categories."""
    if distance < 4.6:
        return 'La_1N'
    elif 4.6 <= distance < 6:
        return 'La_2N'
    else:
        return 'La_far'

def process_folder(folder):
    """Processes a folder containing VO.txt and La.txt files. Computes distances and updates classifications."""
    
    # Define file paths for vacancy and lanthanum data
    vo_path = os.path.join(folder, 'VO.txt')
    la_path = os.path.join(folder, 'La.txt')

    # Read vacancy (VO) and lanthanum (La) atomic coordinates
    vo_data = pd.read_csv(vo_path, sep=r'\s+', header=None, usecols=[1, 2, 3])
    la_data = pd.read_csv(la_path, sep=r'\s+', header=None, usecols=[1, 2, 3])

    # Compute pairwise distances between VO and La atoms
    distances_vo_la = np.sqrt(np.sum((vo_data.values[:, np.newaxis, :] - la_data.values) ** 2, axis=2))
    sorted_distances_vo_la = np.sort(distances_vo_la, axis=1)
    d1_d2 = sorted_distances_vo_la[:, :2]  # Select the closest and second closest La atoms

    # Compute pairwise distances between VO atoms
    distances_vo_vo = np.sqrt(np.sum((vo_data.values[:, np.newaxis, :] - vo_data.values) ** 2, axis=2))
    np.fill_diagonal(distances_vo_vo, np.inf)  # Exclude self-distance
    d3 = np.min(distances_vo_vo, axis=1)  # Minimum VO-VO distance

    # Compute pairwise distances between La atoms
    distances_la_la = np.sqrt(np.sum((la_data.values[:, np.newaxis, :] - la_data.values) ** 2, axis=2))
    np.fill_diagonal(distances_la_la, np.inf)  # Exclude self-distance
    d4 = np.min(distances_la_la, axis=1)  # Minimum La-La distance

    # Classify distances based on predefined criteria
    n1_n2 = np.vectorize(classify_distance)(d1_d2)
    d3_labels = np.vectorize(classify_vo_distance)(d3)
    d4_labels = np.vectorize(classify_la_distance)(d4)

    # Update VO.txt with computed distances and classifications
    vo_full = pd.read_csv(vo_path, sep=r'\s+', header=None)
    vo_full['d1'] = d1_d2[:, 0]
    vo_full['d2'] = d1_d2[:, 1]
    vo_full['N1'] = n1_n2[:, 0]
    vo_full['N2'] = n1_n2[:, 1]
    vo_full['d3'] = d3
    vo_full['VO_Class'] = d3_labels
    vo_full.to_csv(vo_path, sep=' ', index=False, header=False)  # Overwrite original file

    # Update La.txt with computed distances and classifications
    la_full = pd.read_csv(la_path, sep=r'\s+', header=None)
    la_full['d4'] = d4
    la_full['La_Class'] = d4_labels
    la_full.to_csv(la_path, sep=' ', index=False, header=False)  # Overwrite original file

    return folder

def main():
    """Processes all folders starting with 'A' in parallel using multiple processes."""
    
    # Identify directories that start with 'A'
    folders = [f for f in os.listdir('.') if os.path.isdir(f) and f.startswith('A')]
    count = 0
    total = len(folders)

    # Use parallel processing to speed up folder processing
    with ProcessPoolExecutor(max_workers=128) as executor:
        futures = [executor.submit(process_folder, folder) for folder in folders]
        for future in futures:
            future.result()  # Wait for each task to complete
            count += 1
            print(f"Progress: {count}/{total} folders processed ({(count / total) * 100:.2f}%)")

if __name__ == '__main__':
    main()