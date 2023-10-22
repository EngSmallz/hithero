import os

# Get user input
state = input("Enter state: ")
county = input("Enter county: ")
school_district = input("Enter school district: ")
school = input("Enter school: ")
name = input("Enter name: ")

# Define the base directory where the user profiles will be created
base_directory = "user_profiles"

# Create directory structure if it doesn't exist
if not os.path.exists(base_directory):
    os.makedirs(base_directory)

# Create the folder structure for the user profile
user_profile_path = os.path.join(base_directory, state, county, school_district, school, name)
os.makedirs(user_profile_path, exist_ok=True)

# Create the teacher's HTML file
teacher_page_filename = os.path.join(user_profile_path, f"{name}.html")

# You can replace the placeholders in the HTML template with actual values
html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Teacher Profile - Hometown Heroes</title>
    <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
    <header>
        <h1>Teacher Profile</h1>
    </header>

    <nav>
        <ul>
            <li><a href="index.html">Home</a></li>
            <li><a href="about.html">About</a></li>
            <li><a href="contact.html">Contact</a></li>
        </ul>
    </nav>

    <main>
        <section class="profile">
            <div class="teacher-info">
                <img src="{teacher_image_url}" alt="Teacher Profile Picture">
                <h2>{teacher_name}</h2>
                <p>School: {school_name}</p>
                <p>Location: {city_state}</p>
            </div>

            <div class="wishlist">
                <h2>Amazon Wishlist</h2>
                <p>Here is my Amazon wishlist where you can help support my classroom:</p>
                <a href="{amazon_wishlist_link}" class="btn" target="_blank">View Wishlist</a>
            </div>
        </section>

        <section class="about-me">
            <h2>About Me</h2>
            <p>{about_me_text}</p>
        </section>
    </main>

    <footer>
        <p>&copy; {teacher_name}'s Profile - 2023 Hometown Heroes</p>
    </footer>
</body>
</html>
"""

# # Replace the placeholders in the HTML template with actual values
# html_content = html_template.format(
#     teacher_image_url="teacher_image.jpg",
#     teacher_name=name,
#     school_name=school,
#     city_state=f"{county}, {state}",
#     amazon_wishlist_link="https://www.amazon.com/wishlist/your-wishlist-link",
#     about_me_text="This is a brief description of the teacher."
# )

# Write the HTML content to the teacher's HTML file
with open(teacher_page_filename, "w") as html_file:
    html_file.write(html_content)

print(f"User profile created at: {user_profile_path}")
print(f"Teacher's page created at: {teacher_page_filename}")
