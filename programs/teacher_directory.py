import os
import shutil

# Get user input
state = input("Enter state: ")
county = input("Enter county: ")
school_district = input("Enter school district: ")
school = input("Enter school: ")
name = input("Enter name: ")

# Define the base directory where the user profiles will be created
base_directory = "pages/states/" + state + "/"

# Create directory structure if it doesn't exist
if not os.path.exists(base_directory):
    os.makedirs(base_directory)

# Create the folder structure for the user profile
user_profile_path = os.path.join(base_directory, county, school_district, school, name)
os.makedirs(user_profile_path, exist_ok=True)

# Specify the source file and destination directory
firstname, lastname = name.split()  # Split the full name into first and last name
source_file = "templates/teacher.html"
new_file_name = f"index.html"

# Combine the destination directory and the new file name
destination_path = os.path.join(user_profile_path, new_file_name)

# Use shutil.copy to copy the file to the new location and rename it
shutil.copy(source_file, destination_path)

print(f"User profile created at: {user_profile_path}")
