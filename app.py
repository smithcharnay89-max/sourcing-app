import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
import re

# 1. Page Config
st.set_page_config(page_title="Design Source Pro", layout="wide", initial_sidebar_state="collapsed")

# 2. Database Connection
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# 3. Load Data
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

# --- MOODBOARD LOGIC ---
if 'moodboard' not in st.session_state:
    st.session_state.moodboard = []

def add_to_board(item):
    if item not in st.session_state.moodboard:
        st.session_state.moodboard.append(item)
        st.toast(f"Added {item['Supplier Name']} to your board!")

def clear_board():
    st.session_state.moodboard = []
    st.toast("Board cleared")

# --- UI LAYOUT ---
st.title("🏛️ Design Source Pro")

# Tabs for Search vs. Moodboard
tab1, tab2 = st.tabs(["🔎 Search Suppliers", "🎨 My Moodboard"])

with tab1:
    query = st.text_input("Sourcing Search", placeholder="e.g. Oak, Velvet, Lighting...")
    
    if query:
        terms = query.lower().split()
        results = [r for r in data if any(t in str(r).lower() for t in terms)]

        for item in results:
            with st.container(border=True):
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.subheader(item.get('Supplier Name'))
                    st.write(f"**{item.get('Category')}**")
                    if item.get('Image Link'):
                        st.image(item.get('Image Link'), width=200)
                with c2:
                    st.markdown(f"⏳ **{item.get('Lead Time')}**")
                    st.button(f"➕ Add to Moodboard", key=f"btn_{item['Supplier Name']}", 
                              on_click=add_to_board, args=(item,))

with tab2:
    if st.session_state.moodboard:
        st.header("Project Moodboard")
        st.button("🗑️ Clear Everything", on_click=clear_board)
        
        # Display the moodboard in a 3-column grid
        cols = st.columns(3)
        for idx, board_item in enumerate(st.session_state.moodboard):
            with cols[idx % 3]:
                with st.container(border=True):
                    if board_item.get('Image Link'):
                        st.image(board_item.get('Image Link'), use_container_width=True)
                    st.write(f"**{board_item.get('Supplier Name')}**")
                    st.caption(board_item.get('Category'))
    else:
        st.info("Your moodboard is empty. Go to the Search tab to add suppliers and materials.")

st.markdown("---")
st.caption("Professional Sourcing Tool • Design Source Pro")
