import os
import zipfile
from datetime import datetime

def create_project_zip():
    """Create a ZIP file of the entire project for download."""
    # Define exclusion patterns
    exclude_dirs = ['.git', '__pycache__', '.upm', '.cache', '.config']
    exclude_extensions = ['.pyc', '.bak']
    exclude_files = ['uv.lock', 'create_zip.py', 'railway_ticket_system.zip']
    
    # Get current timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"railway_ticket_system.zip"
    
    # Create a new ZIP file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through all files and directories
        for root, dirs, files in os.walk('.'):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            # Process files
            for file in files:
                # Skip excluded files and extensions
                if (file in exclude_files or 
                    any(file.endswith(ext) for ext in exclude_extensions)):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Add file to the ZIP (without the leading './' in the archive path)
                archive_path = file_path[2:] if file_path.startswith('./') else file_path
                zipf.write(file_path, archive_path)
    
    print(f"Created ZIP file: {zip_filename}")
    return zip_filename

if __name__ == "__main__":
    create_project_zip()