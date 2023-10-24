import os

def create_index_html(folder_path, current_depth=0):
    file_name = "index.html"
    file_path = os.path.join(folder_path, file_name)

    if os.path.exists(file_path):
        print(f"The file '{file_name}' already exists in '{folder_path}'.")
    else:
        # File doesn't exist; create it
        try:
            # Define a mapping of depth to list names
            list_names = {
                0: "List of Counties",
                1: "List of School Districts",
                2: "List of Schools",
                3: "List of Teachers"
            }

            # Determine the appropriate list name based on the current depth
            list_name = list_names.get(current_depth, "List")

            with open(file_path, 'w') as index_file:
                # Write the HTML content to the file with dynamic list_name
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
        <h1>{list_name} in {folder_path}</h1>
        <ul>
            <!-- Add links to future pages -->
        </ul>
    </main>
</body>
</html>''')
                print(f"Created a new '{file_name}' in '{folder_path}'.")
        except Exception as e:
            print(f"An error occurred while creating the file: {e}")

# Example usage:
folder_path = "states\\"
create_index_html(folder_path, current_depth=0)
