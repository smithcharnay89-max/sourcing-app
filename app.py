import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re
import pandas as pd

# 1. Config
st.set_page_config(page_title="Design Source Pro", layout="wide")
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
FOLDER_ID = st.secrets["GDRIVE_FOLDER_ID"]

# Helper: Get or Create Project File
def get_project_spreadsheet(project_name):
    files = client.list_spreadsheet_files(folder_id=FOLDER_ID)
    file = next((f for f in files if f['name'] == project_name), None)
    if not file:
        file = client.create(project_name, folder_id=FOLDER_ID)
        sheet = client.open_by_key(file['id']).sheet1
        sheet.update("A1", [["Description", "Supplier", "Cost", "Qty", "Status"]])
    return client.open_by_key(file['id']).sheet1

# Session State
if 'active_project' not in st.session_state: st.session_state.active_project = None

# Sidebar: Project Management
with st.sidebar:
    st.header("📂 Project Library")
    proj_name = st.text_input("New Project Name")
    if st.button("➕ Create Project") and proj_name:
        get_project_spreadsheet(proj_name)
        st.rerun()
    
    files = client.list_spreadsheet_files(folder_id=FOLDER_ID)
    project_list = [f['name'] for f in files]
    active_selection = st.selectbox("Select Project", project_list)
    if active_selection:
        st.session_state.active_project = active_selection

# Main Interface
if st.session_state.active_project:
    st.title(f"🏛️ {st.session_state.active_project}")
    sheet = get_project_spreadsheet(st.session_state.active_project)
    ledger = sheet.get_all_records()
    
    # Financial Entry
    with st.expander("➕ Log Expense", expanded=True):
        col1, col2, col3 = st.columns(3)
        desc = col1.text_input("Item")
        cost = col2.number_input("Cost", step=100.0)
        qty = col3.number_input("Qty", value=1)
        if st.button("Save"):
            sheet.append_row([desc, "Vendor", cost, qty, "Pending"])
            st.rerun()
            
    # Table View
    st.dataframe(pd.DataFrame(ledger), use_container_width=True)
    total = sum(d['Cost'] * d['Qty'] for d in ledger)
    st.metric("Total Project Cost", f"R{total:,.2f}")
