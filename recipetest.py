import os
import re
import csv
from functools import lru_cache

def is_valid_name(name):
    keyword_set = [
        'sizeof', 'int', 'char', 'float', 'double', 'bool', 'void', 'short', 'long', 'signed', 'struct',
        'uint8_t', 'uint16_t', 'uint32_t', 'int8_t', 'int16_t', 'int32_t'
    ]
    if re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", name) is None:
        return False
    if name in keyword_set:
        return False
    return True

def is_func(line):
    attribute_list = ["__attribute__((interrupt))"]
    line = line.strip()
    for attr in attribute_list:
        line = line.replace(attr, "")
    if len(line) < 2 or '=' in line or '(' not in line or line[0] in ['#', '/'] or line.endswith(';'):
        return None
    if line.startswith('static'):
        line = line[len('static'):]
    line = re.sub(r'[*&]', ' ', line)
    line = re.sub(r'\(', ' ( ', line)
    line_split = line.split()
    if len(line_split) < 2:
        return None
    bracket_num = line.count('(')
    if bracket_num == 1:
        for index in range(len(line_split)):
            if '(' in line_split[index]:
                return line_split[index - 1]
    else:
        line = re.sub(r'[()]', ' ', line)
        line_split = line.split()
        index = 0
        for one in line_split:
            if is_valid_name(one):
                index += 1
                if index == 2:
                    return one
    return None

@lru_cache(maxsize=None)
def func_name_extract(file_path):
    if not os.path.isfile(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
        file_list = fp.readlines()
    functions = {}
    i = -1
    while i < len(file_list) - 1:
        i += 1
        line = file_list[i]
        func_name = is_func(line)
        if func_name is not None:
            start_line = i
            left_brack_num = 0
            was_not_function = 1  # Initialize was_not_function
            while i < len(file_list) - 1:
                line = file_list[i].strip()
                left_brack_num += line.count('{')
                if "}" in line:
                    left_brack_num -= line.count("}")
                    if left_brack_num < 1:
                        if "};" in line:
                            was_not_function = 1
                            break
                        else:
                            was_not_function = 0
                            break
                i += 1
            end_line = i
            if was_not_function == 0:
                functions[func_name.split('::')[-1]] = (start_line, end_line)
    return functions

@lru_cache(maxsize=None)
def find_function_callers(test_folder_path, target_function):
    caller_functions = set()
    for root, _, files in os.walk(test_folder_path):
        for file in files:
            if file.endswith('.cpp') or file.endswith('.h'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    pattern = r'\b' + re.escape(target_function) + r'\b'
                    if re.search(pattern, content):
                        functions = func_name_extract(file_path)
                        for func_name, (start_line, end_line) in functions.items():
                            for i in range(start_line, end_line + 1):
                                if re.search(pattern, content.splitlines()[i]):
                                    caller_functions.add(func_name)
    return caller_functions

def find_function_usages_in_test_files(test_folder_path, caller_functions):
    test_case_to_file_map = {}
    for root, _, files in os.walk(test_folder_path):
        for file in files:
            if file.endswith('.test'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for func_name in caller_functions:
                        pattern = r'\b' + re.escape(func_name) + r'\b'
                        if re.search(pattern, content):
                            test_case_pattern = r'\btest\s+\w+\s+(\w+)\s*{'
                            matches = re.findall(test_case_pattern, content, re.IGNORECASE)
                            if matches:
                                for match in matches:
                                    # Ensure the match is the immediate test case name
                                    test_case_name = match
                                    test_case_start_pattern = r'\btest\s+\w+\s+' + re.escape(test_case_name) + r'\s*{'
                                    test_case_start_match = re.search(test_case_start_pattern, content, re.IGNORECASE)
                                    if test_case_start_match:
                                        start_pos = test_case_start_match.start()
                                        end_pos = content.find('}', start_pos)
                                        if end_pos != -1 and re.search(pattern, content[start_pos:end_pos]):
                                            test_case_to_file_map[test_case_name] = file_path
    return test_case_to_file_map

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

def find_stpl_files(mtpl_files, root_folder):
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

def find_csv_files(stpl_files, root_folder):
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

def extract_csv_rows(stpl_files, csv_files):
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

    recipes = []
    for line in extracted_lines:
        row = line.strip().split(',')
        if row and row[0].startswith('iVal'):
            # Find the index of the last element ending with ".env"
            env_index = next((i for i, item in enumerate(row) if item.endswith('.env')), None)
            if env_index is not None:
                # Write the row up to and including the ".env" element
                recipes.append(','.join(row[:env_index + 1]))
        else:
            recipes.append(line)
    return recipes

def find_files_with_extension(root_folder, extension):
    files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith(extension):
                files.append(os.path.join(dirpath, filename))
    return files

# Define paths
test_folder = r'.\PartRepo\HDMTOS\Validation\iVal'
root_folder = r'.\PartRepo\HDMTOS\Validation\iVal'

# Read function names from a text file
with open("affected_functions.txt", "r") as f:
    function_names = [line.strip() for line in f.readlines()]

test_case_to_file_map = {}

for target_function in function_names:
    # Find caller functions in the test folder
    print(f"\nFinding caller functions for {target_function} in the test folder...")
    caller_functions = find_function_callers(test_folder, target_function)
    print(f"Caller functions: {caller_functions}")

    # Find affected test files and test case names
    print(f"\nFinding affected test files and test case names for {target_function}...")
    test_case_to_file_map.update(find_function_usages_in_test_files(test_folder, caller_functions))

# Print affected test files and test case names
print("\nAffected test files and test case names:")
for test_case, test_file in test_case_to_file_map.items():
    print(f"Test Case: {test_case}, Test File: {test_file}")

# Find recipes for each test case
test_files = list(test_case_to_file_map.values())
test_case_to_recipe_map = {}

for test_file in test_files:
    test_dir = get_base_directory(test_file)
    mtpl_files = find_mtpl_files(test_dir)
    if mtpl_files:
        stpl_files = find_stpl_files(mtpl_files, root_folder)
        if stpl_files:
            csv_files = find_csv_files(stpl_files, root_folder)
            if csv_files:
                recipes = extract_csv_rows(stpl_files, csv_files)
                for test_case in test_case_to_file_map:
                    if test_case_to_file_map[test_case] == test_file:
                        test_case_to_recipe_map[test_case] = recipes

# Write affected test files, test case names, and recipes to a CSV file
with open("affected_tests_and_cases_recipe.csv", "w", newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["Test File", "Test Case Name", "Recipe"])
    for test_case, test_file in test_case_to_file_map.items():
        recipe = test_case_to_recipe_map.get(test_case, ["N/A"])
        csvwriter.writerow([test_file, test_case, "\n".join(recipe)])