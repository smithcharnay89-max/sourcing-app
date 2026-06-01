import streamlit as st
import gspread
import json
import re
from google.oauth2.service_account import Credentials

# 1. Setup
st.set_page_config(page_title="Design Source Pro", layout="wide")

# 2. Connection: Using the local service_account.json file
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

with open("service_account.json") as f:
    creds_dict = json.load(f)

creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

# --- SIMPLIFIED SESSION STATE ---
if 'projects' not in st.session_state:
    st.session_state.projects = {
        "Main Board": {
            "moodboard_items": [],  
            "financial_ledger": [], 
            "budget": 250000.0      
        }
    }

# 3. Sidebar for Project Management
with st.sidebar:
    st.header("📂 Project Operations")
    new_project_name = st.text_input("Create New Project", placeholder="e.g. Project Llandudno")
    if st.button("➕ Create Project") and new_project_name.strip():
        proj_title = new_project_name.strip()
        if proj_title not in st.session_state.projects:
            st.session_state.projects[proj_title] = {"moodboard_items": [], "financial_ledger": [], "budget": 100000.0}
            st.success(f"Created '{proj_title}'")
            st.rerun()
    st.write("---")
    active_project = st.selectbox("Current Active Project", options=list(st.session_state.projects.keys()))
    st.write("---")
    current_budget = st.number_input("Set Client Total Budget (R)", min_value=0.0, value=float(st.session_state.projects[active_project]["budget"]), step=5000.0)
    st.session_state.projects[active_project]["budget"] = current_budget

# Helpers
def clean_conversational_query(user_query):
    query_lower = user_query.lower().strip()
    filler_phrases = [r"where can i find a", r"where can i find", r"do you have any", r"do you have a", r"looking for a", r"looking for", r"show me", r"i need a", r"i need", r"can you find", r"please find", r"help me find"]
    for phrase in filler_phrases: query_lower = re.sub(phrase, "", query_lower)
    return [t.strip() for t in query_lower.split() if t.strip() not in ['a', 'an', 'the', 'with', 'in', 'for']]

def extract_clean_email(item_dict):
    for val in item_dict.values():
        val_str = str(val).strip()
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', val_str)
        if email_match: return email_match.group(0)
    return 'N/A'

def add_to_moodboard(item, project):
    title = item.get('Supplier Name') or item.get('Brand') or item.get('Product Name') or "Unknown Item"
    existing = st.session_state.projects[project]["moodboard_items"]
    if title not in [x.get('title') for x in existing]:
        st.session_state.projects[project]["moodboard_items"].append({"title": title, "image": item.get('Image Link') or item.get('Image') or item.get('Photo') or "", "category": item.get('Category') or "Catalog Item", "source": item.get('Supplier Name') or "Internal Database"})
        st.toast(f"Saved {title} to Moodboard!")
    else: st.toast("ℹ️ Already on your Moodboard")

def parse_quote_pdf(file_upload):
    try:
        import pdfplumber
        full_text = ""
        with pdfplumber.open(file_upload) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if text: full_text += text + "\n"
        amounts = re.findall(r'(?:R?\s?\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2}))', full_text)
        clean_amounts = [float(a.replace('R', '').replace(' ', '').replace(',', '')) for a in amounts if float(a.replace('R', '').replace(' ', '').replace(',', '')) >= 100.0]
        detected_total = max(clean_amounts) if clean_amounts else 0.0
        return {"name": f"📄 Quote", "supplier": "PDF Upload", "cost": detected_total, "qty": 1, "status": "Quoted", "image_data": None}
    except: return None

# Main UI
st.title("🏛️ Design Source Pro")
st.caption(f"📍 Managing: **{active_project}**")
tab1, tab2, tab3 = st.tabs(["🔎 Smart Assistant", "🎨 Project Moodboard", "📊 Project Finances"])

with tab1:
    query = st.text_input("Ask the Assistant")
    if query:
        search_terms = clean_conversational_query(query)
        scored_results = []
        for row in data:
            row_string = str(row).lower()
            match_count = sum(1 for term in search_terms if term in row_string)
            if match_count > 0: scored_results.append((match_count, row))
        for item in [i[1] for i in sorted(scored_results, key=lambda x: x[0], reverse=True)]:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    title = item.get('Supplier Name') or "Unknown Item"
                    st.subheader(title)
                    st.write(f"**Category:** {item.get('Category', 'N/A')}")
                with c2:
                    st.button("➕ Save", key=f"src_{title}", on_click=add_to_moodboard, args=(item, active_project))

with tab2:
    st.header(f"🎨 Moodboard: {active_project}")
    board_items = st.session_state.projects[active_project]["moodboard_items"]
    for idx, item in enumerate(board_items):
        st.image(item['image'], width=200) if item['image'] else st.write("No image")
        st.write(f"**{item['title']}**")
        if st.button("🗑️ Remove", key=f"del_{idx}"):
            st.session_state.projects[active_project]["moodboard_items"].pop(idx)
            st.rerun()

with tab3:
    st.header(f"📊 Ledger: {active_project}")
    ledger = st.session_state.projects[active_project]["financial_ledger"]
    if st.button("💾 Log Custom Expense"): st.session_state.projects[active_project]["financial_ledger"].append({"name": "Custom Item", "supplier": "Vendor", "cost": 0.0, "qty": 1, "status": "Pending", "image_data": None})
    for idx, line in enumerate(ledger):
        st.write(f"{line['name']} - R{line['cost']}")
