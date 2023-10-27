import os

# Function to replace / with \ in a file
def replace_slash_with_backslash(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    content = content.replace('', '/a')
    with open(file_path, 'w') as file:
        file.write(content)

# Directory path where you want to make the changes
root_directory = 'states/'

# Recursive function to traverse through the directory structure
def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file == 'index.html':
                file_path = os.path.join(root, file)
                replace_slash_with_backslash(file_path)

# Start processing from the root directory
process_directory(root_directory)
