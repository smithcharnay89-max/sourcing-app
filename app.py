import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re

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

# Advanced logic to surgically extract emails and phone numbers from anywhere in the row
def extract_clean_details(item_dict):
    stock = 'N/A'
    email = 'N/A'
    phone = 'N/A'
    
    # 1. Extract Stock Level
    stock_keys = ['stock', 'stock level', 'qty', 'quantity', 'availability', 'in stock', 'status']
    for k, v in item_dict.items():
        if str(k).lower().strip() in stock_keys and v:
            stock = str(v)
            break

    # Loop through all values in the row to find hidden contact details
    for val in item_dict.values():
        val_str = str(val).strip()
        if not val_str:
            continue
            
        # 2. Surgical Email Extraction (Finds "info@domain.co.za" even inside "[Text / info@...]")
        if email == 'N/A':
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', val_str)
            if email_match:
                email = email_match.group(0)

        # 3. Surgical Phone Extraction (Finds typical SA/international phone patterns within text strings)
        if phone == 'N/A':
            # Looks for numbers with 7 to 15 digits that might include spaces, dashes, or leading plus signs
            phone_match = re.search(r'(\+?\(?\d{1,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4})', val_str)
            if phone_match:
                cleaned_phone = phone_match.group(0).strip()
                # Ensure it's a real phone number, not a short code or year
                if len([c for c in cleaned_phone if c.isdigit()]) >= 7:
                    phone = cleaned_phone
                
    return stock, email, phone

def add_to_board(item, project):
    title = item.get('Supplier Name') or item.get('Brand') or item.get('Product Name') or "Unknown Item"
    if title not in [x.get('Supplier Name') or x.get('Brand') or x.get('Product Name') for x in st.session_state.projects[project]]:
        st.session_state.projects[project].append(item)
        st.toast(f"Added to {project}!")
    else:
        st.toast("ℹ️ Already in project")

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
                    title = item.get('Supplier Name') or item.get('Brand') or item.get('Product Name') or "Unknown Item"
                    st.subheader(title)
                    
                    category = item.get('Category') or item.get('Type') or 'N/A'
                    lead_time = item.get('Lead Time') or item.get('Leadtime') or 'N/A'
                    st.write(f"**Category:** {category} | ⏳ **Lead Time:** {lead_time}")
                    
                    # Run the dynamic detail parser
                    stock_val, email_val, phone_val = extract_clean_details(item)
                    
                    st.write(f"📦 **Stock Level:** {stock_val}")
                    
                    if email_val != 'N/A':
                        st.write(f"✉️ **Email:** [{email_val}](mailto:{email_val})")
                    else:
                        st.write(f"✉️ **Email:** N/A")
                        
                    st.write(f"📞 **Phone:** {phone_val}")
                    
                    website = item.get('Website') or item.get('Link')
                    if website:
                        st.markdown(f"🔗 [Visit Website]({website})")
                    
                with c2:
                    st.button(
                        f"➕ Add to {active_project}", 
                        key=f"a_{title}_{active_project}", 
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
                    img_url = board_item.get('Image Link') or board_item.get('Image') or board_item.get('Photo')
                    category_fallback = board_item.get('Category') or board_item.get('Type') or 'Item'
                    if not img_url:
                        st.markdown(f"### 🛋️\n**{category_fallback}**")
                    else:
                        st.image(img_url, use_container_width=True)
                    
                    b_title = board_item.get('Supplier Name') or board_item.get('Brand') or board_item.get('Product Name') or "Item"
                    st.write(f"**{b_title}**")
                    
                    b_stock, b_email, b_phone = extract_clean_details(board_item)
                    
                    st.caption(f"📦 Stock: {b_stock}")
                    st.caption(f"✉️ {b_email}")
                    st.caption(f"📞 {b_phone}")
        
        st.write("---")
        if st.button(f"🗑️ Clear {active_project}"):
            st.session_state.projects[active_project] = []
            st.rerun()
    else:
        st.info(f"Your board for '{active_project}' is empty.")
