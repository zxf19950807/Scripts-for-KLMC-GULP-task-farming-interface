import os
import re
from concurrent.futures import ProcessPoolExecutor, as_completed

def modify_file(file_path):
    try:
        with open(file_path, 'r+') as file:
            content = file.read()

            # Replace the specified strings
            content = re.sub('lbfgs_order 2000', 'lbfgs_order 5000', content)
#            content = re.sub(r'opti pot', 'opti pot lbfgs', content)

            # Append the new line at the end
#            content += '\n' + 'lbfgs_order 2000'

            # Go back to the start of the file to overwrite
            file.seek(0)
            file.write(content)
            file.truncate()  # Truncate the file in case new content is shorter than old

        return file_path, True
    except Exception as e:
        return file_path, False

def main(directory):
    # Gather all .gin files in the specified directory
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.gin')]
    total_files = len(files)
    success_count = 0

    # Process files in parallel
    with ProcessPoolExecutor(max_workers=128) as executor:
        future_to_file = {executor.submit(modify_file, file): file for file in files}
        for future in as_completed(future_to_file):
            file, success = future.result()
            if success:
                success_count += 1
            print(f'Processed {file}: {"Success" if success else "Failed"}')
            print(f'Progress: {success_count}/{total_files} ({(success_count/total_files*100):.2f}%)')

    print('All files processed.')

if __name__ == '__main__':
    directory = '/path/to/your/gin/files'  # Update this to the path of your .gin files
    main(directory)
