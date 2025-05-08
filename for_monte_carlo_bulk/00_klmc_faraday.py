import os
import subprocess
import re

def modify_files(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".gin"):
                filepath = os.path.join(root, filename)
                with open(filepath, 'r') as file:
                    file_content = file.read()

                # Modify content
                file_content = file_content.replace("0  1  0  1  1", "0 1 0 1 1 1")
                file_content = re.sub(r'output xyz\n', '', file_content)

                with open(filepath, 'w') as file:
                    file.write(file_content)

                if filename.endswith(".out"):
                    os.remove(os.path.join(root, filename))

def main():
    for i in range(58, 59):
        dir_name = f"VO_{i}"
        os.chdir(dir_name)

        print(os.getcwd())
        subprocess.run(["/home/fonz/bin_tmp/klmc_new"])

        modify_files("run")

        # Change directory back to parent
        os.chdir("..")

if __name__ == "__main__":
    main()