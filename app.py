import streamlit as st
import gspread

# 1. Load the secrets dict
creds_dict = st.secrets["gcp_service_account"]

# 2. Let gspread handle the authentication directly from the dictionary
client = gspread.service_account_from_dict(creds_dict)

# 3. Open your sheet
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8"
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

# Test to see if it worked
st.write("Successfully connected to Google Sheets!")
