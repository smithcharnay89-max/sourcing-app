import streamlit as st
import gspread

# 1. Load the secrets
creds_dict = st.secrets["gcp_service_account"].to_dict()

# 2. Manually fix the private key format
# This removes potential hidden characters and forces the correct structure
if 'private_key' in creds_dict:
    creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')

# 3. Connect
client = gspread.service_account_from_dict(creds_dict)

# 4. Open
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8"
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()
st.write("Successfully connected!")
