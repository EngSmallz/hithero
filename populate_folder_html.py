import os

# List of folder names you want to create
folder_names = [
    "Katrina Boyd",
    "Sierra Breidenbach",
    "Jessica Chadwick",
    "Karen Coins",
    "Michael Constantine",
    "Nancy Cote",
    "Clif Davis",
    "Stephanie Dormaier",
    "Lisa Dunlop",
    "Grace Fragomeni",
    "Wendy Gilbert",
    "Danielle Griffis",
    "Courtney Haase",
    "Lori Koellen, RN",
    "Gail Madsen",
    "Tommi Melcher",
    "Marilyn Musselwhite",
    "Jamie Myers",
    "Julie Pielop",
    "Amanda (Mandi) Potter",
    "Terri Remendowski",
    "Tammy Simmons",
    "Cheryl Spilker",
    "Lacey Swegle",
    "Nancy Warnecke",
    "Angela Williams"
]

# Directory location where you want to create the folders
base_directory = "states/Washington/Spokane County/Medical Lake/Hallet Elementary"
next_level = 'None'

# Ensure the base directory exists
if not os.path.exists(base_directory):
    os.mkdir(base_directory)

if next_level != 'None':
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
                {list2}
            </ul>
        </main>
    </body>
    </html>
    """
else:
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Teacher Profile - Hometown Heroes</title>
    <link rel="stylesheet" type="text/css" href="/style.css">
</head>
<body>
    <header>
        <h1>Teacher Profile</h1>
    </header>

    <nav>
        <ul>
            <li><a href="/index.html">Home</a></li>
            <li><a href="/about.html">About</a></li>
            <li><a href="/contact.html">Contact</a></li>
        </ul>
    </nav>

    <main>
        <section class="profile">
            <div class="teacher-info">
                <img src="teacher-profile-pic.jpg" alt="Teacher Profile Picture">
                <h2>Teacher Name</h2>
                <p>School: School Name</p>
                <p>Location: City, State</p>
            </div>

            <div class="wishlist">
                <h2>Amazon Wishlist</h2>
                <p>Here is my Amazon wishlist where you can help support my classroom:</p>
                <a href="amazon-wishlist-link" class="btn" target="_blank">View Wishlist</a>
            </div>
        </section>

        <section class="about-me">
            <h2>About Me</h2>
            <p>Share a personal message, your teaching philosophy, and classroom needs here. Tell potential supporters about your goals and the impact their help can make.</p>
        </section>
    </main>

    <footer>
        <p>&copy; 2023 Hometown Heroes</p>
    </footer>
</body>
</html>
    """

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


if next_level != 'Counties':
    base_html_filename = os.path.join(base_directory, "index.html")

    # Read the existing content of the file
    with open(base_html_filename, "r") as base_html_file:
        existing_content = base_html_file.read()

    # Replace the {list2} placeholder with ul_content
    ul_content = "\n\t\t\t".join([f'<li><a href="{item}/index.html">{item}</a></li>' for item in folder_names])
    updated_content = existing_content.replace("{list2}", ul_content)

    # Write the updated content back to the file
    with open(base_html_filename, "w") as base_html_file:
        base_html_file.write(updated_content)

    print(f"Updated base HTML file: {base_html_filename}")