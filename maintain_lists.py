import os

### 

def print_directory_structure(path, indent=0):
    if os.path.exists(path):
        items = os.listdir(path)
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                # Specify the directory path
                directory_path = item_path

                # Ensure the directory path exists
                if os.path.exists(directory_path) and os.path.isdir(directory_path):
                    # Check if 'index.html' exists in the 'states/' directory
                    index_html_path = os.path.join(directory_path, 'index.html')
                    if os.path.exists(index_html_path):
                        # Read the content of 'index.html'
                        with open(index_html_path, 'r') as index_html_file:
                            index_html_content = index_html_file.read()

                        folder_list = os.listdir(directory_path)

                        # Filter only directories
                        folder_list = [f for f in folder_list if os.path.isdir(os.path.join(directory_path, f))]

                        # Generate the list items for directories not already present
                        list_items = []
                        for folder_name in folder_list:
                            folder_link = os.path.join(folder_name, 'index.html').replace(os.path.sep, '/')
                            # Check if the folder_link is already present in the HTML content
                            if folder_link not in index_html_content:
                                list_item = f'<li><a href="{folder_link}">{folder_name}</a></li>'
                                list_items.append(list_item)

                        # If there are new list items to add, update the 'index.html' content
                        if list_items:
                            placeholder = '<!-- Add links to future pages -->'
                            updated_html_content = index_html_content.replace(placeholder, f'{placeholder}\n\t\t\t' + '\n\t\t\t'.join(list_items))

                            # Write the updated HTML content back to 'index.html'
                            with open(index_html_path, 'w') as index_html_file:
                                index_html_file.write(updated_html_content)

                            print("Updated 'index.html' with the new list items.")
                        else:
                            print("No new list items to add.")
                    else:
                        print("'index.html' does not exist in the 'states/' directory.")
                else:
                    print(f"The directory path '{directory_path}' does not exist or is not a directory.")

# Example usage:
directory_path = "states/"  # Replace with your directory path
print_directory_structure(directory_path)
