import os
import shutil

def create_index_html_if_not_exists(folder_path, current_depth=0, max_depth=4):
    if current_depth > max_depth:
        return

    file_name = "index.html"
    file_path = os.path.join(folder_path, file_name)

    if not os.path.exists(file_path):
        try:
            # Get the name of the current folder
            current_folder_name = os.path.basename(folder_path)

            # Define a mapping of depth to list names
            list_names = {
                0: "List of States",
                1: "List of Counties",
                2: "List of School Districts",
                3: "List of Schools",
                4: "List of Teachers"
            }

            # Determine the appropriate list name based on the current depth
            list_name = list_names.get(current_depth, "List")

            # Copy the template index.html file to the folder
            template_file = "templates/index.html"
            shutil.copy2(template_file, file_path)

            # Replace placeholders in the copied file
            with open(file_path, 'r') as index_file:
                content = index_file.read()
                content = content.replace("{list_name}", list_name)
                content = content.replace("{current_folder_name}", current_folder_name)

            with open(file_path, 'w') as index_file:
                index_file.write(content)

            print(f"Created a new '{file_name}' in '{folder_path}'.")
        except Exception as e:
            print(f"An error occurred while creating or copying the '{file_name}' file: {e}")

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        if os.path.isdir(item_path):
            # If it's a directory, search it recursively
            create_index_html_if_not_exists(item_path, current_depth + 1, max_depth)

# Example usage:
root_folder = "pages/states/"
create_index_html_if_not_exists(root_folder)
