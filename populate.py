import os

# List of counties and their largest school districts
counties = ['King', 'Pierce', 'Snohomish', 'Spokane', 'Clark']
school_districts = [
    ['Seattle Public Schools', 'Bellevue School District', 'Kent School District'],
    ['Tacoma Public Schools', 'Puyallup School District', 'Bethel School District'],
    ['Everett Public Schools', 'Mukilteo School District', 'Edmonds School District'],
    ['Spokane Public Schools', 'Central Valley School District', 'Mead School District'],
    ['Vancouver Public Schools', 'Evergreen School District', 'Battle Ground Public Schools']
]

# Define the base directory
base_directory = 'Washington'

# Function to convert names to folder-friendly format
def format_for_folder(name):
    return name.replace(" ", "_")

# Create the Washington directory if it doesn't exist
if not os.path.exists(base_directory):
    os.mkdir(base_directory)

# Create the folder structure for counties and school districts
for county, district_list in zip(counties, school_districts):
    county_directory = os.path.join(base_directory, format_for_folder(county))
    os.mkdir(county_directory)

    # Create an HTML file for the list of school districts in each county
    with open(os.path.join(county_directory, 'index.html'), 'w') as f:
        f.write("<!DOCTYPE html>\n")
        f.write("<html>\n")
        f.write("<head>\n")
        f.write("    <title>{0} School Districts</title>\n".format(county))
        f.write("    <link rel=\"stylesheet\" type=\"text/css\" href=\"/style.css\">\n")
        f.write("</head>\n")
        f.write("<body>\n")
        f.write("    <header>\n")
        f.write("        <h1>Find a Teacher</h1>\n")
        f.write("    </header>\n")
        f.write("    <nav>\n")
        f.write("        <ul>\n")
        f.write("            <li><a href=\"/index.html\">Home</a></li>\n")
        f.write("            <li><a href=\"/about.html\">About</a></li>\n")
        f.write("            <li><a href=\"/contact.html\">Contact</a></li>\n")
        f.write("        </ul>\n")
        f.write("    </nav>\n")
        f.write("    <main>\n")
        f.write(f"        <h1>List of {county} School Districts</h1>\n")
        f.write("        <ul>\n")
        for district in district_list:
            district_name = format_for_folder(district)
            f.write(f"            <li><a href=\"{district_name}/index.html\">{district}</a></li>\n")
        f.write("        </ul>\n")
        f.write("    </main>\n")
        f.write("</body>\n")
        f.write("</html>\n")

    # Create an HTML file for each school district
    for district in district_list:
        district_directory = os.path.join(county_directory, format_for_folder(district))
        os.mkdir(district_directory)
        with open(os.path.join(district_directory, 'index.html'), 'w') as district_file:
            district_file.write("<!DOCTYPE html>\n")
            district_file.write("<html>\n")
            district_file.write("<head>\n")
            district_file.write(f"    <title>Schools in {district}</title>\n")
            district_file.write("    <link rel=\"stylesheet\" type=\"text/css\" href=\"/style.css\">\n")
            district_file.write("</head>\n")
            district_file.write("<body>\n")
            district_file.write("    <header>\n")
            district_file.write(f"        <h1>Find a Teacher</h1>\n")
            district_file.write("    </header>\n")
            district_file.write("    <nav>\n")
            district_file.write("        <ul>\n")
            district_file.write("            <li><a href=\"/index.html\">Home</a></li>\n")
            district_file.write("            <li><a href=\"/about.html\">About</a></li>\n")
            district_file.write("            <li><a href=\"/contact.html\">Contact</a></li>\n")
            district_file.write("        </ul>\n")
            district_file.write("    </nav>\n")
            district_file.write("    <main>\n")
            district_file.write(f"        <h1>Schools in {district} </h1>\n")
            # Add school names or other information for the district here.
            district_file.write("    </main>\n")
            district_file.write("</body>\n")
            district_file.write("</html>\n")

# Create the main HTML file for Washington counties
with open(os.path.join(base_directory, 'index.html'), 'w') as f:
    f.write("<!DOCTYPE html>\n")
    f.write("<html>\n")
    f.write("<head>\n")
    f.write("    <title>Washington Counties</title>\n")
    f.write("    <link rel=\"stylesheet\" type=\"text/css\" href=\"/style.css\">\n")
    f.write("</head>\n")
    f.write("<body>\n")
    f.write("    <header>\n")
    f.write("        <h1>Find a Teacher</h1>\n")
    f.write("    </header>\n")
    f.write("    <nav>\n")
    f.write("        <ul>\n")
    f.write("            <li><a href=\"/index.html\">Home</a></li>\n")
    f.write("            <li><a href=\"/about.html\">About</a></li>\n")
    f.write("            <li><a href=\"/contact.html\">Contact</a></li>\n")
    f.write("        </ul>\n")
    f.write("    </nav>\n")
    f.write("    <main>\n")
    f.write("        <h1>List of Washington Counties</h1>\n")
    f.write("        <ul>\n")
    for county in counties:
        county_name = format_for_folder(county)
        f.write(f"            <li><a href=\"{county_name}/index.html\">{county}</a></li>\n")
    f.write("        </ul>\n")
    f.write("    </main>\n")
    f.write("</body>\n")
    f.write("</html>\n")


print("Folder structure, HTML files created successfully.")
