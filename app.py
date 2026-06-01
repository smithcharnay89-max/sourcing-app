import streamlit as st
import gspread
import json
from google.oauth2.service_account import Credentials

# Define the scopes
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Load the file directly from the repo
# Since we uploaded the file to the same folder, this will work
with open("service_account.json") as f:
    creds_dict = json.load(f)

# Authorize using the credentials from the file
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

st.title("🏛️ Design Source Pro")
st.success("Successfully connected to Google Drive!")
