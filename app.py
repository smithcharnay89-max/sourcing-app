import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Define the scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Pull the configuration from the secrets
if "gcp_service_account" in st.secrets:
    creds_dict = dict(st.secrets["gcp_service_account"])
    # Ensure the private key is a single line string
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    st.write("Connection successful!")
else:
    st.error("Secrets not found.")
