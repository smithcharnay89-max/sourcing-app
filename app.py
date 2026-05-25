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

# Multi-Project Session State
if 'projects' not in st.session_state:
    st.session_state.projects = {
        "Main Board": []  # Default project
    }

# 3. Sidebar for Project Management
with st.sidebar:
    st.header("📂 Project Manager")
    
    new_project_name = st.text_input("Create New Project", placeholder="e.g. Smith Residence")
    if st.button("➕ Create Project") and new_project_name.strip():
        proj_title = new_project_name.strip()
        if proj_title not in st.session_state.projects:
            st.session_state.projects[proj_title] = []
            st.success(f"Created '{proj_title}'")
            st.rerun()
            
    st.write("---")
    
    active_project = st.selectbox(
        "Current Active Project", 
        options=list(st.session_state.projects.keys())
    )

def add_to_board(item, project):
    if item['Supplier Name'] not in [x['Supplier Name'] for x in st.session_state.projects[project]]:
        st.session_state.projects[project].append(item)
        st.toast(f"Added to {project}!")
    else:
        st.toast(f"ℹ️ Already in {project}")

st.title("🏛️ Design Source Pro")
st.caption(f"📍 Currently editing: **{active_project}**")

tab1, tab2 = st.tabs(["🔎 Search & Source", "🎨 Project Boards"])

with tab1:
    query = st.text_input("Search Suppliers", placeholder="e.g. Crema, Oak, Lighting...")
    if query:
        terms = query.lower().split()
        results = [r for r in data if any(t in str(r).lower() for t in terms)]
        
        for item in results:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.subheader(item.get('Supplier Name'))
                    st.write(f"**Category:** {item.get('Category')} | ⏳ **Lead Time:** {item.get('Lead Time')}")
                    st.write(f"📦 **Stock Level:** {item.get('Stock Level', 'N/A')}")
                    
                    # --- DYNAMIC CONTACT COLS (Looks for Email and Phone columns) ---
                    email = item.get('Email') or item.get('Email Address') or 'N/A'
                    phone = item.get('Phone') or item.get('Phone Number') or 'N/A'
                    
                    # Display them cleanly. If email exists, make it a clickable mailto: link
                    if email != 'N/A':
                        st.write(f"✉️ **Email:** [{email}](mailto:{email})")
                    else:
                        st.write(f"✉️ **Email:** N/A")
                        
                    st.write(f"📞 **Phone:** {phone}")
                    
                    if item.get('Website'):
                        st.markdown(f"🔗 [Visit Website]({item.get('Website')})")
                    
                with c2:
                    st.button(
                        f"➕ Add to {active_project}", 
                        key=f"a_{item['Supplier Name']}_{active_project}", 
                        on_click=add_to_board, 
                        args=(item, active_project)
                    )

with tab2:
    st.header(f"🎨 {active_project} Moodboard")
    current_board_items = st.session_state.projects[active_project]
    
    if current_board_items:
        cols = st.columns(3)
        for idx, board_item in enumerate(current_board_items):
            with cols[idx % 3]:
                with st.container(border=True):
                    img_url = board_item.get('Image Link')
                    if not img_url:
                        st.markdown(f"### 🛋️\n**{board_item.get('Category')}**")
                    else:
                        st.image(img_url, use_container_width=True)
                    
                    st.write(f"**{board_item.get('Supplier Name')}**")
                    
                    # --- ADDED CONTACT DETAILS TO MOODBOARD CARDS ---
                    b_email = board_item.get('Email') or board_item.get('Email Address') or 'N/A'
                    b_phone = board_item.get('Phone') or board_item.get('Phone Number') or 'N/A'
                    
                    st.caption(f"📦 Stock: {board_item.get('Stock Level', 'N/A')}")
                    st.caption(f"✉️ {b_email}")
                    st.caption(f"📞 {b_phone}")
        
        st.write("---")
        if st.button(f"🗑️ Clear {active_project}"):
            st.session_state.projects[active_project] = []
            st.rerun()
    else:
        st.info(f"Your board for '{active_project}' is empty.")
