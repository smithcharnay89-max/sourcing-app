import streamlit as st
from google.oauth2 import service_account
import gspread

# We will load the dict and pass it directly to gspread's client_from_dict
creds_dict = st.secrets["gcp_service_account"]
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Create credentials object
creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scope)

# Connect directly using the credentials object
client = gspread.authorize(creds)

SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8"
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()
