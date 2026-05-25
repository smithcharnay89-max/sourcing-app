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

# CONVERSATIONAL CLEANER: Strips out conversational filler phrases
def clean_conversational_query(user_query):
    query_lower = user_query.lower().strip()
    
    # Phrases to remove so the bot can focus on actual design materials/items
    filler_phrases = [
        r"where can i find a", r"where can i find", r"do you have any", r"do you have a", 
        r"looking for a", r"looking for", r"show me", r"i need a", r"i need", 
        r"can you find", r"please find", r"help me find"
    ]
    
    for phrase in filler_phrases:
        query_lower = re.sub(phrase, "", query_lower)
        
    # Split into clean, individual descriptive terms (e.g., ['black', 'leather', 'couch'])
    terms = [t.strip() for t in query_lower.split() if t.strip() not in ['a', 'an', 'the', 'with', 'in', 'for']]
    return terms

# Cleaner helper for emails
def extract_clean_email(item_dict):
    for val in item_dict.values():
        val_str = str(val).strip()
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', val_str)
        if email_match:
            return email_match.group(0)
    return 'N/A'

def add_to_board(item, project):
    title = item.get('Supplier Name') or item.get('Brand') or item.get('Product Name') or "Unknown Item"
    if title not in [x.get('Supplier Name') or x.get('Brand') or x.get('Product Name') for x in st.session_state.projects[project]]:
        st.session_state.projects[project].append(item)
        st.toast(f"Added to {project}!")
    else:
        st.toast("ℹ️ Already in project")

st.title("🏛️ Design Source Pro")
st.caption(f"📍 Currently editing: **{active_project}**")

tab1, tab2 = st.tabs(["🔎 Smart Assistant", "🎨 Project Boards"])

with tab1:
    # Conversational placeholder hint
    query = st.text_input("Ask the Assistant", placeholder="e.g., Where can I find a black leather couch?")
    
    if query:
        # Process the conversational text into search keywords
        search_terms = clean_conversational_query(query)
        
        if search_terms:
            # Smart Matching: Ranks items by how many keywords match the row data
            scored_results = []
            for row in data:
                row_string = str(row).lower()
                # Count how many of your search terms match this specific row
                match_count = sum(1 for term in search_terms if term in row_string)
                if match_count > 0:
                    scored_results.append((match_count, row))
            
            # Sort results so the ones with the highest keyword matches appear first
            results = [item[1] for item in sorted(scored_results, key=lambda x: x[0], reverse=True)]
            
            if results:
                st.write(f"✨ *I parsed your request down to keywords: `{', '.join(search_terms)}` and found {len(results)} potential matches:*")
                
                for item in results:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            title = item.get('Supplier Name') or item.get('Brand') or item.get('Product Name') or "Unknown Item"
                            st.subheader(title)
                            
                            category = item.get('Category') or item.get('Type') or 'N/A'
                            lead_time = item.get('Lead Time') or item.get('Leadtime') or 'N/A'
                            st.write(f"**Category:** {category} | ⏳ **Lead Time:** {lead_time}")
                            
                            # Safely show stock if it exists, default to 'Contact Supplier' instead of N/A
                            stock_val = item.get('Stock Level') or item.get('Stock') or 'Available to Order'
                            st.write(f"📦 **Stock/Availability:** {stock_val}")
                            
                            email_val = extract_clean_email(item)
                            if email_val != 'N/A':
                                st.write(f"✉️ **Email:** [{email_val}](mailto:{email_val})")
                            
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
            else:
                st.warning(f"I couldn't find an exact match for `{', '.join(search_terms)}` in your current spreadsheet database. Try adjusting your description terms.")
        else:
            st.info("How can I help you source today?")

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
                    
                    b_stock = board_item.get('Stock Level') or board_item.get('Stock') or 'Available to Order'
                    b_email = extract_clean_email(board_item)
                    
                    st.caption(f"📦 Status: {b_stock}")
                    if b_email != 'N/A':
                        st.caption(f"✉️ {b_email}")
        
        st.write("---")
        if st.button(f"🗑️ Clear {active_project}"):
            st.session_state.projects[active_project] = []
            st.rerun()
    else:
        st.info(f"Your board for '{active_project}' is empty.")
