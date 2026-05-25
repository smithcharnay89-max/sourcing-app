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

# Fetch data
data = sheet.get_all_records()

# --- DIAGNOSTIC: GET ACTUAL SHEET HEADERS ---
# This grabs the very first row of your sheet so we can see the exact column names.
try:
    sheet_headers = sheet.row_values(1)
except Exception:
    sheet_headers = list(data[0].keys()) if data else []

# Multi-Project Session State
if 'projects' not in st.session_state:
    st.session_state.projects = {
        "Main Board": []
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
    
    # --- VISUAL INSPECTOR (Look here on your app screen!) ---
    st.write("---")
    with st.expander("🔍 Inspect Sheet Columns"):
        st.caption("These are your exact column names from Google Sheets:")
        st.write(sheet_headers)

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
                    
                    # Safe extraction helper that ignores case and spaces
                    def get_field(item_dict, keys_to_try):
                        for k in keys_to_try:
                            # Try exact match
                            if k in item_dict and item_dict[k]:
                                return item_dict[k]
                            # Try lowercase/stripped matching fallback
                            for actual_key in item_dict.keys():
                                if actual_key.lower().strip() == k.lower().strip() and item_dict[actual_key]:
                                    return item_dict[actual_key]
                        return 'N/A'

                    # Extract values using common naming variations
                    stock_val = get_field(item, ['Stock Level', 'Stock', 'In Stock', 'Qty'])
                    email_val = get_field(item, ['Email', 'Email Address', 'Contact Email', 'Supplier Email'])
                    phone_val = get_field(item, ['Phone', 'Phone Number', 'Telephone', 'Contact Number'])
                    
                    st.write(f"📦 **Stock Level:** {stock_val}")
                    
                    if email_val != 'N/A':
                        st.write(f"✉️ **Email:** [{email_val}](mailto:{email_val})")
                    else:
                        st.write(f"✉️ **Email:** N/A")
                        
                    st.write(f"📞 **Phone:** {phone_val}")
                    
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
                    
                    # Carry over the helper values for the moodboard layout
                    b_stock = get_field(board_item, ['Stock Level', 'Stock', 'In Stock', 'Qty'])
                    b_email = get_field(board_item, ['Email', 'Email Address', 'Contact Email', 'Supplier Email'])
                    b_phone = get_field(board_item, ['Phone', 'Phone Number', 'Telephone', 'Contact Number'])
                    
                    st.caption(f"📦 Stock: {b_stock}")
                    st.caption(f"✉️ {b_email}")
                    st.caption(f"📞 {b_phone}")
        
        st.write("---")
        if st.button(f"🗑️ Clear {active_project}"):
            st.session_state.projects[active_project] = []
            st.rerun()
    else:
        st.info(f"Your board for '{active_project}' is empty.")
