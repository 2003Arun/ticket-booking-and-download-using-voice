import zipfile

# Open the ZIP file
with zipfile.ZipFile('railway_ticket_system.zip', 'r') as zip_ref:
    # List all the contents
    file_list = zip_ref.namelist()
    
    # Print the list of files
    print(f"Total files in ZIP: {len(file_list)}")
    for file in sorted(file_list):
        print(file)