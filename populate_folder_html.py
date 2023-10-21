import os
### to use this, input a list of the folders you want to create
###change the next_level to what is past the list
### example: state -> county -> school disctrict -> school -> teachers
###choose the right location to create
### after creating, the list of next level needs to be populated


# List of folder names you want to create
folder_names = [
    "Adams County",
    "Asotin County",
    "Benton County",
    "Chelan County",
    "Clallam County",
    "Clark County",
    "Columbia County",
    "Cowlitz County",
    "Douglas County",
    "Ferry County",
    "Franklin County",
    "Garfield County",
    "Grant County",
    "Grays Harbor County",
    "Island County",
    "Jefferson County",
    "King County",
    "Kitsap County",
    "Kittitas County",
    "Klickitat County",
    "Lewis County",
    "Lincoln County",
    "Mason County",
    "Okanogan County",
    "Pacific County",
    "Pend Oreille County",
    "Pierce County",
    "San Juan County",
    "Skagit County",
    "Skamania County",
    "Snohomish County",
    "Spokane County",
    "Stevens County",
    "Thurston County",
    "Wahkiakum County",
    "Walla Walla County",
    "Whatcom County",
    "Whitman County",
    "Yakima County"
]


# Directory location where you want to create the folders
base_directory = "states/Washington"
next_level = 'School Districts'
# HTML content template
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Hometown Heroes - Support Teachers</title>
    <link rel="stylesheet" type="text/css" href="\style.css">
</head>
<body>
    <header>
        <h1>Find a Teacher</h1>
    </header>

    <nav>
        <ul>
            <li><a href="\index.html">Home</a></li>
            <li><a href="\about.html">About</a></li>
            <li><a href="\contact.html">Contact</a></li>
            <!-- Add links to other pages here -->
        </ul>
    </nav>
    <main>
        <h1>{list}</h1>
        <ul>
            <li><a href="temp/index.html">temp</a></li>
        </ul>
    </main>
</body>
</html>
"""



# Ensure the base directory exists
if not os.path.exists(base_directory):
    os.mkdir(base_directory)

# Create folders in the chosen directory location and generate HTML files
for folder_name in folder_names:
    folder_path = os.path.join(base_directory, folder_name)
    
    # Check if the folder already exists to avoid overwriting
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
        print(f"Created folder: {folder_path}")

        # Create an HTML file in the folder
        html_filename = os.path.join(folder_path, "index.html")
        with open(html_filename, "w") as html_file:
            list_name = "List of " + next_level + " in " + folder_name
            html_content_with_list = html_content.replace("{list}", list_name)
            html_file.write(html_content_with_list)
        print(f"Created HTML file: {html_filename}")
    else:
        print(f"Folder already exists: {folder_path}")
