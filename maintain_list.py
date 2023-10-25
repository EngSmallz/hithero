import os
import subprocess

# Define the directory where you want to run your script in subfolders
base_directory = "states/"

# Define the Python script you want to run in each folder
script_to_run = "populate_list.py"

# Iterate through all subdirectories in the base directory
for root, dirs, files in os.walk(base_directory):
    for directory in dirs:
        # Form the full path to the Python script
        script_path = os.path.join(root, directory, script_to_run)

        # Check if the script file exists in the current directory
        if os.path.isfile(script_path):
            try:
                # Execute the Python script using subprocess
                subprocess.run(["python", script_path])
            except Exception as e:
                print(f"Error running script in {script_path}: {str(e)}")

