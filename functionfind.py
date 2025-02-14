import os
import re
import ast

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
        print('here', file_path)
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

def parse_python_functions(file_path):
    functions = {}
    try:
        with open(file_path, 'r', encoding="utf-8", errors="ignore") as file:
            tree = ast.parse(file.read(), filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions[node.name] = node
    except (SyntaxError, IndentationError) as e:
        print(f"Error parsing file {file_path}: {e}")
    return functions

def get_changed_files(base_folder, new_folder):
    changed_files = []
    for root, _, files in os.walk(new_folder):
        for file in files:
            new_file_path = os.path.join(root, file)
            base_file_path = os.path.join(base_folder, os.path.relpath(new_file_path, new_folder))
            if not os.path.exists(base_file_path):
                changed_files.append(new_file_path)
            else:
                with open(base_file_path, 'r', encoding="utf-8", errors="ignore") as base_file, open(new_file_path, 'r', encoding="utf-8", errors="ignore") as new_file:
                    base_content = base_file.readlines()
                    new_content = new_file.readlines()
                    if base_content != new_content:
                        changed_files.append(new_file_path)
    return changed_files

def get_changed_functions(file_path, base_file_path, language):
    changed_functions = set()
    if language == 'python' and file_path.endswith('.py'):
        new_functions = parse_python_functions(file_path)
        base_functions = parse_python_functions(base_file_path)
        for func_name, new_func in new_functions.items():
            if func_name not in base_functions or ast.dump(new_func) != ast.dump(base_functions[func_name]):
                changed_functions.add(func_name)
    elif language in ['c', 'cpp'] and (file_path.endswith('.c') or file_path.endswith('.cpp') or file_path.endswith('.h')):
        new_functions = func_name_extract(file_path)
        base_functions = func_name_extract(base_file_path)
        
        for func_name, (new_start, new_end) in new_functions.items():
            if func_name not in base_functions:
                changed_functions.add(func_name)
            else:
                base_start, base_end = base_functions[func_name]
                with open(file_path, 'r', encoding="utf-8", errors="ignore") as new_file, open(base_file_path, 'r', encoding="utf-8", errors="ignore") as base_file:
                    new_content = new_file.readlines()[new_start:new_end+1]
                    base_content = base_file.readlines()[base_start:base_end+1]
                    if new_content != base_content:
                        changed_functions.add(func_name)
    return changed_functions

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

base_folder = r'.\PartRepo\HDMTOS\I2L'
new_folder = r'.\tempOldFiles\I2L'
development_folders = [r'.\PartRepo\HDMTOS\I2L', r'.\PartRepo\HDMTOS\HAL', r'.\PartRepo\HDMTOS\TAL']

# Get changed files and functions
print("Getting changed files...")

changed_files=list()
with open('.\changedFileName.txt', 'r') as changedFiles:
    for file in changedFiles:
        changed_files.append('.\\PartRepo\\HDMTOS\\'+file.strip().replace('/','\\'))
        print(file)

print(f"Changed files: {changed_files}")

changed_functions = set()
file_to_folder_map = {}

for file_path in changed_files:
    base_file_path = file_path.replace('PartRepo\\HDMTOS','tempOldFiles')
    if file_path.endswith('.py'):
        print(f"Extracting changed functions from Python file: {file_path}", base_file_path)
        changed_functions.update(get_changed_functions(file_path, base_file_path, 'python'))
    elif file_path.endswith('.c') or file_path.endswith('.cpp') or file_path.endswith('.h'):
        print(f"Extracting changed functions from C/C++ file: {file_path}", base_file_path)
        changed_functions.update(get_changed_functions(file_path, base_file_path, 'cpp'))
    
    # Map the file to its corresponding folder
    for folder in development_folders:
        if folder in file_path:
            file_to_folder_map[file_path] = folder
            break

# Print changed functions
print("Changed functions:")
for func in changed_functions:
    print(func)

# Print file to folder mapping
print("\nFile to folder mapping:")
for file_path, folder in file_to_folder_map.items():
    print(f"{file_path} -> {folder}")

# Function to find the folder a function belongs to
def find_function_folder(func_name):
    for folder in development_folders:
        for root, _, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.py'):
                    functions = parse_python_functions(file_path)
                elif file.endswith('.c') or file.endswith('.cpp') or file.endswith('.h'):
                    functions = func_name_extract(file_path)
                else:
                    continue
                if func_name in functions:
                    return folder
    return None

# Traverse through development folders and find affected functions
affected_functions = set()

def traverse_and_find_functions(start_folder, func):
    print(f"Traversing folder '{start_folder}' for function '{func}'")
    caller_functions = find_function_callers(start_folder, func)
    print(f"Caller functions in '{start_folder}': {caller_functions}")
    
    if start_folder == development_folders[0]:  # 'a'
        next_folder = development_folders[1]  # 'b'
    elif start_folder == development_folders[1]:  # 'b'
        next_folder = development_folders[2]  # 'c'
    else:  # 'c'
        return caller_functions
    
    affected_functions_c = set()
    for caller_func in caller_functions:
        functions = traverse_and_find_functions(next_folder, caller_func)
        affected_functions_c.update(functions)
    return affected_functions_c

for func in changed_functions:
    folder = find_function_folder(func)
    if folder:
        print(f"Function '{func}' belongs to folder '{folder}'")
        if folder == development_folders[2]:  # 'c'
            affected_functions.add(func)
        else:
            functions = traverse_and_find_functions(folder, func)
            affected_functions.update(functions)

# Print affected functions
print("\nAffected functions:")
for func in affected_functions:
    print(func)

# Write affected functions to a .txt file
with open("affected_functions.txt", "w") as f:
    for func in affected_functions:
        f.write(func + "\n")