import os
import re
import glob
from concurrent.futures import ProcessPoolExecutor

max_workers = 64

def check_gulp_res(directory):
    return directory if not os.path.isfile(os.path.join(directory, 'a.xyz')) else None

def check_for_error(gout_path):
    with open(gout_path, 'r') as file:
        for line in file:
            if "ERROR" in line:
                return gout_path
    return None

def grep_energy(res_path):
    with open(res_path, 'r') as file:
        for line in file:
            if "totalenergy" in line:
                return line.strip()
    return None
    
def sort_key_func(x):
    nums = re.findall(r'\d+', x)
    if nums:
        return int(nums[0])
    else:
        return 0  # or any other fallback value

# Step 1: Find unfinished calculations without gulp.res and generate restart list
directories = sorted(glob.glob('A*/'))

with ProcessPoolExecutor(max_workers=max_workers) as executor:
    restart_list = list(filter(None, executor.map(check_gulp_res, directories)))

with open('restart_list.txt', 'w') as file:
    file.write('\n'.join(restart_list))

if restart_list:
    num_start = int(re.findall(r'\d+', restart_list[0])[0])
    print(f"Restart from No.: {num_start}")
else:
    print("No restart is needed.")
print("Step 1: Check Restart : ok")

# Step 2: Find error calculations and generate error list
gout_paths = glob.glob('A*/*.gout')

with ProcessPoolExecutor(max_workers=max_workers) as executor:
    error_list = list(filter(None, executor.map(check_for_error, gout_paths)))

with open('error.txt', 'w') as file:
    file.write('\n'.join(error_list))

print("Step 2: ok")
print("Content of error.txt:")
with open('error.txt', 'r') as file:
    print(file.read())

# Step 3: Grep energy
res_paths = sorted(glob.glob('*/gulp.res'), key=sort_key_func)

with ProcessPoolExecutor(max_workers=max_workers) as executor:
    energy_data = list(filter(None, executor.map(grep_energy, res_paths)))

with open('energy.txt', 'w') as file:
    file.write('\n'.join(energy_data))

print("Step 3: Grep Energy : ok")
print("...done")
