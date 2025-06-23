import streamlit as st
import base64
import os

def get_binary_file_downloader_html(bin_file, file_label='File'):
    """
    Generate a download link for a binary file
    """
    with open(bin_file, 'rb') as f:
        data = f.read()
    
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}" style="display:inline-block; background-color:#4CAF50; color:white; padding:14px 25px; text-align:center; text-decoration:none; font-size:16px; margin:4px 2px; border-radius:8px;">Download {file_label}</a>'
    return href

st.set_page_config(
    page_title="Railway Ticket System - Download",
    page_icon="🚂",
    layout="centered"
)

st.title("🚂 Voice-Activated Railway Ticket System")
st.subheader("Project Download")

st.markdown("""
### Project Information

This is a fully voice-activated railway ticket booking system designed specifically for visually impaired users.
The system operates without button interfaces, relying on speech recognition for input and text-to-speech for output.

#### Key Features:
- Completely voice-controlled interface
- Book, modify and cancel railway tickets
- Search tickets by name or ID
- Download tickets as PDF files
- Accessibility-first design

#### Instructions:
Click the button below to download the complete project as a ZIP file.
""")

zip_file = 'railway_ticket_system.zip'
if os.path.exists(zip_file):
    file_size = round(os.path.getsize(zip_file) / (1024 * 1024), 2)
    st.success(f"ZIP file ready for download ({file_size} MB)")
    
    # Create download button
    download_button = get_binary_file_downloader_html(zip_file, 'Railway Ticket System (ZIP)')
    st.markdown(download_button, unsafe_allow_html=True)
    
    # Extra guidance
    st.info("After downloading, extract the ZIP file and run `streamlit run app.py` to start the application.")
else:
    st.error("ZIP file not found. Please create it first by running create_zip.py")