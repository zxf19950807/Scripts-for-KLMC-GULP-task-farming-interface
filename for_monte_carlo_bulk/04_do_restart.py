import os
import re

# Step 1: Remove specific files and directories
directories_to_remove = ["std*", "workgroup*"]
file_to_remove = "master.log"

for directory in directories_to_remove:
    for dirpath in [d for d in os.listdir() if re.match(directory, d)]:
        os.system(f"rm -r {dirpath}")

if os.path.exists(file_to_remove):
    os.remove(file_to_remove)

print("Step 1: ok")

# Step 2: Find unfinished calculations without gulp.res
restart_list = []

for dirpath, dirnames, filenames in os.walk("."):
    for dirname in dirnames:
        if dirname.startswith('A') and not os.path.exists(os.path.join(dirpath, dirname, 'gulp.res')):
            restart_list.append(os.path.join(dirpath, dirname))

restart_list.sort()

# Output directories without gulp.res
print("Directories without gulp.res:")
for item in restart_list:
    print(item)

with open("restart_list.txt", "w") as f:
    for item in restart_list:
        f.write(f"{item}\n")

# Find restart number
min_restart_num = min([int(re.search(r'A(\d+)', path).group(1)) for path in restart_list if re.search(r'A(\d+)', path)])
max_restart_num = max([int(re.search(r'A(\d+)', path).group(1)) for path in restart_list if re.search(r'A(\d+)', path)])
print(f"Restart from No.: {min_restart_num}")
print(f"Restart to No.: {max_restart_num}")
print("Step 2: ok")

# Step 3: Remove directories from Amin_restart_num to Amax
for num in range(min_restart_num, max_restart_num + 1):
    dir_to_remove = os.path.join('A' + str(num))
    if os.path.exists(dir_to_remove):
        os.system(f"rm -r {dir_to_remove}")

print("Step 3: ok")

# Step 4: Prepare new files
with open("taskfarm.config", "r") as f:
    content = f.read()

content = re.sub(r"task_start.*", f"task_start {min_restart_num}", content)
# content = re.sub(r"task_end.*", f"task_end {max_restart_num}", content)

with open("taskfarm.config", "w") as f:
    f.write(content)

print("Step 4: ok")
print("...done")
