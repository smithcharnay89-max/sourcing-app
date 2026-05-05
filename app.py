import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse

# 1. Setup
st.set_page_config(page_title="Design Source Pro", layout="wide", initial_sidebar_state="collapsed")

# 2. Connection
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

# --- MOODBOARD STORAGE ---
if 'moodboard' not in st.session_state:
    st.session_state.moodboard = []

def add_to_board(item):
    if item['Supplier Name'] not in [x['Supplier Name'] for x in st.session_state.moodboard]:
        st.session_state.moodboard.append(item)
        st.toast(f"✅ {item['Supplier Name']} added!")

st.title("🏛️ Design Source Pro")

# --- NAVIGATION TABS ---
tab1, tab2 = st.tabs(["🔎 Sourcing Search", "🎨 Visual Moodboard"])

with tab1:
    query = st.text_input("What are you sourcing?", placeholder="e.g. Marble, Oak, Crema...")
    if query:
        terms = query.lower().split()
        results = [r for r in data if any(t in str(r).lower() for t in terms)]
        
        for item in results:
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.subheader(item.get('Supplier Name'))
                    st.caption(f"Category: {item.get('Category')}")
                with c2:
                    st.button(f"➕ Add to Board", key=f"add_{item['Supplier Name']}", 
                              on_click=add_to_board, args=(item,))

with tab2:
    if st.session_state.moodboard:
        st.header("Project Palette")
        
        # Grid Layout
        cols = st.columns(3)
        for idx, board_item in enumerate(st.session_state.moodboard):
            with cols[idx % 3]:
                with st.container(border=True):
                    # Placeholder if no image link exists
                    img = board_item.get('Image Link') if board_item.get('Image Link') else "https://via.placeholder.com/300x200.png?text=No+Image+Provided"
                    st.image(img, use_container_width=True)
                    st.write(f"**{board_item.get('Supplier Name')}**")
                    st.caption(f"⏳ Lead Time: {board_item.get('Lead Time')}")
        
        st.divider()
        if st.button("🗑️ Reset Moodboard"):
            st.session_state.moodboard = []
            st.rerun()
    else:
        st.info("Search for suppliers and click 'Add to Board' to build your project palette here.")

st.markdown("---")
st.caption("Professional Sourcing Tool • Design Source Pro")
