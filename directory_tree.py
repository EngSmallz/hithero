import os

def create_directory_tree(root_dir, output_file):
    with open(output_file, 'w') as file:
        for root, dirs, files in os.walk(root_dir):
            level = root.replace(root_dir, '').count(os.sep)
            indent = '  ' * (level)
            file.write(f'{indent}+-- {os.path.basename(root)}/\n')
            subindent = '  ' * (level + 1)
            for file_name in files:
                file.write(f'{subindent}-- {file_name}\n')

if __name__ == '__main__':
    root_directory = 'C:\\Users\jstnb\OneDrive\Desktop\Scripts\hithero'  # Replace with your directory path
    output_file = 'directory_tree.txt'  # The name of the output file

    create_directory_tree(root_directory, output_file)
    print(f"Directory tree has been written to '{output_file}'.")
