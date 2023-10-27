import os

def update_index_html(directory_path, depth=0):
    if depth == 4:
        return  # Limit recursion depth to 4 levels

    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            index_html_path = os.path.join(item_path, 'index.html')
            if os.path.exists(index_html_path):
                with open(index_html_path, 'r') as index_html_file:
                    index_html_content = index_html_file.read()

                folder_list = [f for f in os.listdir(item_path) if os.path.isdir(os.path.join(item_path, f))]

                list_items = []
                for folder_name in folder_list:
                    folder_link = os.path.join(folder_name, 'index.html').replace(os.path.sep, '/')
                    if folder_link not in index_html_content:
                        list_item = f'<li><a href="{folder_link}">{folder_name}</a></li>'
                        list_items.append(list_item)

                if list_items:
                    placeholder = '<!-- Add links to future pages -->'
                    updated_html_content = index_html_content.replace(placeholder, f'{placeholder}\n\t\t\t' + '\n\t\t\t'.join(list_items))
                    with open(index_html_path, 'w') as index_html_file:
                        index_html_file.write(updated_html_content)
                    print(f"Updated 'index.html' in {item_path} with new list items.")
                else:
                    print(f"No new list items to add in {item_path}.")

            update_index_html(item_path, depth + 1)

# Example usage:
directory_path = "states/"  # Replace with your directory path
update_index_html(directory_path)
