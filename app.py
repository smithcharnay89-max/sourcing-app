import streamlit as st
import gspread
import json
import re
from google.oauth2.service_account import Credentials

# 1. Setup
st.set_page_config(page_title="Design Source Pro", layout="wide")

# 2. Connection using the file-based approach
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
            st.session_state.projects[proj_title] = {
                "moodboard_items": [],
                "financial_ledger": [],
                "budget": 100000.0
            }
            st.success(f"Created '{proj_title}'")
            st.rerun()
            
    st.write("---")
    
    active_project = st.selectbox(
        "Current Active Project", 
        options=list(st.session_state.projects.keys())
    )
    
    st.write("---")
    current_budget = st.number_input(
        "Set Client Total Budget (R)", 
        min_value=0.0, 
        value=float(st.session_state.projects[active_project]["budget"]), 
        step=5000.0
    )
    st.session_state.projects[active_project]["budget"] = current_budget

# Helpers
def clean_conversational_query(user_query):
    query_lower = user_query.lower().strip()
    filler_phrases = [
        r"where can i find a", r"where can i find", r"do you have any", r"do you have a", 
        r"looking for a", r"looking for", r"show me", r"i need a", r"i need", 
        r"can you find", r"please find", r"help me find"
    ]
    for phrase in filler_phrases:
        query_lower = re.sub(phrase, "", query_lower)
    return [t.strip() for t in query_lower.split() if t.strip() not in ['a', 'an', 'the', 'with', 'in', 'for']]

def extract_clean_email(item_dict):
    for val in item_dict.values():
        val_str = str(val).strip()
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', val_str)
        if email_match:
            return email_match.group(0)
    return 'N/A'

def add_to_moodboard(item, project):
    title = item.get('Supplier Name') or item.get('Brand') or item.get('Product Name') or "Unknown Item"
    existing = st.session_state.projects[project]["moodboard_items"]
    if title not in [x.get('title') for x in existing]:
        st.session_state.projects[project]["moodboard_items"].append({
            "title": title,
            "image": item.get('Image Link') or item.get('Image') or item.get('Photo') or "",
            "category": item.get('Category') or "Catalog Item",
            "source": item.get('Supplier Name') or "Internal Database"
        })
        st.toast(f"Saved {title} to Moodboard!")
    else:
        st.toast("ℹ️ Already on your Moodboard")

# Invoice/Quote Parser
def parse_quote_pdf(file_upload):
    try:
        import pdfplumber
        full_text = ""
        with pdfplumber.open(file_upload) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if text:
                    full_text += text + "\n"
                    
        if not full_text.strip():
            return None
            
        amounts = re.findall(r'(?:R?\s?\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2}))', full_text)
        clean_amounts = []
        for amt in amounts:
            c_amt = amt.replace('R', '').replace(' ', '').replace(',', '')
            try:
                val = float(c_amt)
                if val >= 100.0:
                    clean_amounts.append(val)
            except ValueError:
                continue
                
        detected_total = max(clean_amounts) if clean_amounts else 0.0
        lines = [l.strip() for l in full_text.split('\n') if l.strip()]
        detected_title = "Imported Supplier Quote"
        if lines:
            for line in lines[:3]:
                if len(line) > 4 and not line.replace('.','').replace(',','').isdigit():
                    detected_title = line[:30]
                    break
        
        return {
            "name": f"📄 {detected_title}",
            "supplier": "PDF Upload Scan",
            "cost": detected_total,
            "qty": 1,
            "status": "Quoted",
            "image_data": None
        }
    except ImportError:
        st.error("The PDF scanning extension is not installed.")
        return None
    except Exception as e:
        return None

st.title("🏛️ Design Source Pro")
st.caption(f"📍 Managing: **{active_project}**")

tab1, tab2, tab3 = st.tabs(["🔎 Smart Assistant", "🎨 Project Moodboard", "📊 Project Finances"])

# --- TAB 1, 2, AND 3 LOGIC REMAINS THE SAME AS YOUR ORIGINAL CODE ---
# [I have omitted the rest of your original logic here to save space, but please paste your full block here]
# ... (Paste your original logic for tabs 1, 2, and 3 below this line in your app.py)
