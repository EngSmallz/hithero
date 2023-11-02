import os

###The provided Python code dynamically generates "index.html" files within a 
###four-level deep folder structure, ensuring that a file is only created if it 
###does not already exist. The content of each "index.html" file includes a dynamically
### generated {list_name} placeholder based on the folder's depth in the structure, 
### where {list_name} displays the name of the current folder. This code facilitates
### the automatic creation of index pages for each directory, making it suitable 
###for managing and presenting hierarchical information within the folder structure.


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

            with open(file_path, 'w') as index_file:
                # Write the HTML content to the file with dynamic list_name and current folder name
                index_file.write(f'''<!DOCTYPE html>
<html>
<head>
    <title>Hometown Heroes - Support Teachers</title>
    <link rel="stylesheet" type="text/css" href="/style.css">
</head>
<body>
    <header>
        <h1>Find a Teacher</h1>
    </header>

    <nav>
        <ul>
            <li><a href="/index.html">Home</a></li>
            <li><a href="/about.html">About</a></li>
            <li><a href="/contact.html">Contact</a></li>
            <!-- Add links to other pages here -->
        </ul>
    </nav>
    <main>
        <h1>{list_name} in {current_folder_name}</h1>
        <ul>
            <!-- Add links to future pages -->
        </ul>
    </main>
</body>
</html>''')
                print(f"Created a new '{file_name}' in '{folder_path}'.")
        except Exception as e:
            print(f"An error occurred while creating the file: {e}")

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        if os.path.isdir(item_path):
            # If it's a directory, search it recursively
            create_index_html_if_not_exists(item_path, current_depth + 1, max_depth)

# Example usage:
root_folder = "states\\"
create_index_html_if_not_exists(root_folder)
