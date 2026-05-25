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

# --- NEW: MULTI-PROJECT SESSION STATE ---
# We now store items as a dictionary where keys are project names: {"Project A": [items], "Project B": [items]}
if 'projects' not in st.session_state:
    st.session_state.projects = {
        "Main Board": []  # Default project
    }

# 3. Sidebar for Project Management
with st.sidebar:
    st.header("📂 Project Manager")
    
    # Text input to create a brand new project
    new_project_name = st.text_input("Create New Project", placeholder="e.g. Smith Residence, Office Fitout")
    if st.button("➕ Create Project") and new_project_name.strip():
        proj_title = new_project_name.strip()
        if proj_title not in st.session_state.projects:
            st.session_state.projects[proj_title] = []
            st.success(f"Created '{proj_title}'")
            st.rerun()
            
    st.write("---")
    
    # Dropdown to select which project you are currently working on
    active_project = st.selectbox(
        "Current Active Project", 
        options=list(st.session_state.projects.keys())
    )

# Callback function to add item to the currently selected project
def add_to_board(item, project):
    # Check if the item is already in this specific project to avoid duplicates
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
                    st.write(f"📦 **Stock Level:** {item.get('Stock Level', 'N/A')} | 📞 **Contact:** {item.get('Contact Details', 'N/A')}")
                    if item.get('Website'):
                        st.markdown(f"🔗 [Visit Website]({item.get('Website')})")
                    
                with c2:
                    # Pass BOTH the item and the active_project to the function
                    st.button(
                        f"➕ Add to {active_project}", 
                        key=f"a_{item['Supplier Name']}_{active_project}", 
                        on_click=add_to_board, 
                        args=(item, active_project)
                    )

with tab2:
    st.header(f"🎨 {active_project} Moodboard")
    
    # Get the items specifically for the active project
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
                    st.caption(f"📦 Stock: {board_item.get('Stock Level', 'N/A')}")
                    st.caption(f"⏳ Lead: {board_item.get('Lead Time', 'N/A')}")
        
        st.write("---")
        if st.button(f"🗑️ Clear {active_project}"):
            st.session_state.projects[active_project] = []
            st.rerun()
    else:
        st.info(f"Your board for '{active_project}' is empty. Search for items and click 'Add to {active_project}' to populate it.")
