import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Define the scopes needed for Google Sheets and Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit Secrets
# This matches the [gcp_service_account] section in your Secrets box
if "gcp_service_account" in st.secrets:
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    st.title("🏛️ Design Source Pro")
    st.success("Successfully connected to Google Drive!")
    
    # Example usage:
    # folder_id = st.secrets["GDRIVE_FOLDER_ID"]
    # files = client.list_spreadsheet_files(folder_id=folder_id)
    # st.write(files)
else:
    st.error("GCP credentials not found in Streamlit Secrets. Please check your settings.")
