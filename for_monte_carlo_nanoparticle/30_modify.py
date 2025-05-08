import os
import glob
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm  

os.chdir('run/')

# get all X.gin files and rename them to A.gin
def rename_file(filename):
    new_filename = 'A' + filename[1:]
    os.rename(filename, new_filename)
    return new_filename

pattern_1 = re.compile(r'0\s{2}1\s{2}0\s{2}1\s{2}1')
replacement_1 = '0 1 0 1 1 1'

# replace content in gin files
def process_gin_file(gin_file):
    with open(gin_file, 'r') as file:
        file_content = file.read()

    modified_content = pattern_1.sub(replacement_1, file_content)
    modified_content = re.sub(r'^.*output xyz run.*\n?', '', modified_content, flags=re.MULTILINE)

    with open(gin_file, 'w') as file:
        file.write(modified_content)

    return gin_file

# Renaming files
with ProcessPoolExecutor(max_workers=64) as executor:
    filenames = glob.glob('X*.gin')
    renamed_files = list(tqdm(executor.map(rename_file, filenames), total=len(filenames), desc="Renaming files"))

# Processing renamed files
with ProcessPoolExecutor(max_workers=64) as executor:
    futures = {executor.submit(process_gin_file, gin_file): gin_file for gin_file in renamed_files}

    # tqdm 
    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing files"):
        future.result()

print("All files have been processed.")
