import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse

# 1. Setup
st.set_page_config(page_title="Design Source Pro", layout="wide")

# 2. Connection
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

if 'moodboard' not in st.session_state:
    st.session_state.moodboard = []

def add_to_board(item):
    if item['Supplier Name'] not in [x['Supplier Name'] for x in st.session_state.moodboard]:
        st.session_state.moodboard.append(item)
        st.toast(f"Added {item['Supplier Name']}")

st.title("🏛️ Design Source Pro")

tab1, tab2 = st.tabs(["🔎 Search", "🎨 Moodboard"])

with tab1:
    query = st.text_input("Search Suppliers", placeholder="e.g. Crema, Oak, Lighting...")
    if query:
        terms = query.lower().split()
        results = [r for r in data if any(t in str(r).lower() for t in terms)]
        
        for item in results:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])  # Adjusted column ratio slightly for extra text space
                with c1:
                    st.subheader(item.get('Supplier Name'))
                    st.write(f"**Category:** {item.get('Category')} | ⏳ **Lead Time:** {item.get('Lead Time')}")
                    
                    # --- NEW DETAILS ADDED HERE ---
                    # Note: Match the text in quotes exactly to your Google Sheet column names!
                    st.write(f"📦 **Stock Level:** {item.get('Stock Level', 'N/A')}")
                    st.write(f"📞 **Contact:** {item.get('Contact Details', 'N/A')}")
                    
                    # Optional: Add a clickable website link if you have one in your sheet
                    if item.get('Website'):
                        st.markdown(f"🔗 [Visit Website]({item.get('Website')})")
                    # ------------------------------
                    
                with c2:
                    st.button(f"➕ Add", key=f"a_{item['Supplier Name']}", on_click=add_to_board, args=(item,))

with tab2:
    if st.session_state.moodboard:
        cols = st.columns(3)
        for idx, board_item in enumerate(st.session_state.moodboard):
            with cols[idx % 3]:
                with st.container(border=True):
                    # AUTOMATIC ICON LOGIC: No work required from you!
                    img_url = board_item.get('Image Link')
                    if not img_url:
                        # Professional designer-style placeholder
                        st.markdown(f"### 🛋️\n**{board_item.get('Category')}**")
                    else:
                        st.image(img_url, use_container_width=True)
                    
                    st.write(f"**{board_item.get('Supplier Name')}**")
                    
                    # --- ADDED DETAILS TO THE MOODBOARD CARDS TOO ---
                    st.caption(f"📦 Stock: {board_item.get('Stock Level', 'N/A')}")
                    st.caption(f"📞 {board_item.get('Contact Details', 'N/A')}")
                    # ------------------------------------------------
        
        st.write("---")
        if st.button("Clear Board"):
            st.session_state.moodboard = []
            st.rerun()  # Fixed the space typo here
    else:
        st.info("Your board is ready for new ideas.")
