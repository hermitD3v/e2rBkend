import os
import re

def read_test_files(test_files_txt):
    with open(test_files_txt, 'r') as file:
        test_files = [line.strip() for line in file.readlines()]
    return test_files

def get_base_directory(file_path):
    return os.path.dirname(file_path)

def find_mtpl_files(test_dir):
    mtpl_files = []
    for filename in os.listdir(test_dir):
        if filename.endswith('.mtpl'):
            mtpl_files.append(filename)  # Store only the filename
    return mtpl_files

def save_mtpl_files(mtpl_files, mtpl_txt):
    with open(mtpl_txt, 'w') as file:
        for mtpl in mtpl_files:
            file.write(mtpl + '\n')

def find_stpl_files(mtpl_files):
    stpl_files = []
    for stpl_file in find_files_with_extension(root_folder, '.stpl'):
        with open(stpl_file, 'r') as f:
            content = f.read()
            for mtpl in mtpl_files:
                # Use regular expression to match the exact mtpl filename as a whole word
                if re.search(r'\b' + re.escape(mtpl) + r'\b', content):
                    stpl_files.append(stpl_file)
                    break  # Stop after finding the first match
    return stpl_files

def save_stpl_files(stpl_files, stpl_txt):
    with open(stpl_txt, 'w') as file:
        for stpl in stpl_files:
            file.write(os.path.basename(stpl) + '\n')  # Save only the basename

def find_csv_files(stpl_files):
    csv_files = []
    for stpl in stpl_files:
        stpl_basename = os.path.basename(stpl)
        for csv_file in find_files_with_extension(root_folder, '.csv'):
            with open(csv_file, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    # Use regular expression to match the exact stpl basename as a whole word
                    if re.search(r'\b' + re.escape(stpl_basename) + r'\b', line):
                        csv_files.append(csv_file)
                        break  # Stop after finding the first match
    return csv_files

def extract_csv_rows(stpl_files, csv_files, output_txt):
    extracted_lines = set()  # Use a set to avoid redundancy

    for csv_file in csv_files:
        with open(csv_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                for stpl in stpl_files:
                    # Use regular expression to match the exact stpl basename as a whole word
                    if re.search(r'\b' + re.escape(os.path.basename(stpl)) + r'\b', line):
                        extracted_lines.add(line)  # Add to set to avoid duplicates
                        break

    with open(output_txt, 'w') as output_file:  # Write mode to avoid appending duplicates
        for line in extracted_lines:
            row = line.strip().split(',')
            if row and row[0].startswith('iVal'):
                # Find the index of the last element ending with ".env"
                env_index = next((i for i, item in enumerate(row) if item.endswith('.env')), None)
                if env_index is not None:
                    # Write the row up to and including the ".env" element
                    output_file.write(','.join(row[:env_index + 1]) + '\n')
            else:
                output_file.write(line)

def find_files_with_extension(root_folder, extension):
    files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith(extension):
                files.append(os.path.join(dirpath, filename))
    return files

def main():
    test_files_txt = 'affected_tests.txt'  # Path to the .txt file containing .test file names
    global root_folder
    root_folder = r'.\PartRepo\HDMTOS\Validation\iVal' # Path to the folder containing .mtpl, .stpl, and .csv files
    mtpl_txt = 'mtpl_files.txt'  # Path to save .mtpl filenames
    stpl_txt ='stpl_files.txt'  # Path to save .stpl filenames
    output_txt = 'recipe.txt'  # Path to the output .txt file

    test_files = read_test_files(test_files_txt)
    all_mtpl_files = []
    for test_file in test_files:
        test_dir = get_base_directory(test_file)
        print(f"Processing directory: {test_dir}")
        
        mtpl_files = find_mtpl_files(test_dir)
        print(f"Found .mtpl files: {mtpl_files}")
        all_mtpl_files.extend(mtpl_files)
    
    save_mtpl_files(all_mtpl_files, mtpl_txt)
    
    if all_mtpl_files:
        stpl_files = find_stpl_files(all_mtpl_files)
        print(f"Found .stpl files: {stpl_files}")
        save_stpl_files(stpl_files, stpl_txt)
        
        if stpl_files:
            csv_files = find_csv_files(stpl_files)
            print(f"Found .csv files: {csv_files}")
            
            if csv_files:
                extract_csv_rows(stpl_files, csv_files, output_txt)
                print(f"Extracted rows from .csv files and saved to {output_txt}")

if __name__ == '__main__':
    main()