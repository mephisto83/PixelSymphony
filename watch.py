import os
import zipfile
import time

def get_all_file_paths(directory):
    """Get all file paths in the directory and subdirectories"""
    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths

def get_latest_modification_time(file_paths):
    """Get the latest modification time among all files"""
    latest_mod_time = 0
    for file_path in file_paths:
        mod_time = os.path.getmtime(file_path)
        if mod_time > latest_mod_time:
            latest_mod_time = mod_time
    return latest_mod_time

def zip_files(file_paths, zip_filename):
    """Create a zip file from provided file paths"""
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in file_paths:
            zipf.write(file, os.path.relpath(file, start=plugins_dir))

plugins_dir = "./pixel_orchestra"
zip_filename = "pixel_orchestra.zip"
last_zip_mod_time = 0
count  = 0
while True:
    current_file_paths = get_all_file_paths(plugins_dir)
    current_latest_mod_time = get_latest_modification_time(current_file_paths)

    if current_latest_mod_time > last_zip_mod_time:
        zip_files(current_file_paths, zip_filename)
        print(f"Updated {zip_filename} - {count}")
        count = count + 1
        last_zip_mod_time = current_latest_mod_time

    time.sleep(10)  # Check for updates every 10 seconds
