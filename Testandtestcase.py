import os
import re

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
    affected_tests = set()
    test_case_names = set()
    for root, _, files in os.walk(test_folder_path):
        for file in files:
            if file.endswith('.test'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for func_name in caller_functions:
                        pattern = r'\b' + re.escape(func_name) + r'\b'
                        if re.search(pattern, content):
                            affected_tests.add(file_path)
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
                                            test_case_names.add(test_case_name)
    return affected_tests, test_case_names

# Define paths
test_folder = r'.\PartRepo\HDMTOS\Validation\iVal'

# Read function names from a text file
with open("affected_functions.txt", "r") as f:
    function_names = [line.strip() for line in f.readlines()]

all_affected_tests = set()
all_test_case_names = set()

for target_function in function_names:
    # Find caller functions in the test folder
    print(f"\nFinding caller functions for {target_function} in the test folder...")
    caller_functions = find_function_callers(test_folder, target_function)
    print(f"Caller functions: {caller_functions}")

    # Find affected test files and test case names
    print(f"\nFinding affected test files and test case names for {target_function}...")
    affected_tests, test_case_names = find_function_usages_in_test_files(test_folder, caller_functions)

    # Collect results
    all_affected_tests.update(affected_tests)
    all_test_case_names.update(test_case_names)

# Print affected test files
print("\nAffected test files:")
for test_file in all_affected_tests:
    print(test_file)

# Print test case names
print("\nTest case names:")
for test_case in all_test_case_names:
    print(test_case)

# Write affected test files to a .txt file
with open("affected_tests.txt", "w") as f:
    for test_file in all_affected_tests:
        f.write(test_file + "\n")

# Write test case names to a separate .txt file
with open("test_case_names.txt", "w") as f:
    for test_case in all_test_case_names:
        f.write(test_case + "\n")