import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Design Source Pro", layout="wide")

# 2. Database Connection Configuration
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
spreadsheet = client.open_by_key(SHEET_ID)

# Tab 1: Catalog Data Master
sheet = spreadsheet.sheet1
data = sheet.get_all_records()

# Tab 2: Financial Backups Configuration
backup_sheet_ready = False
try:
    backup_sheet = spreadsheet.worksheet("Financial_Backups")
    backup_sheet_ready = True
except Exception:
    st.error("⚠️ Cloud Sync Warning: Please create a tab named 'Financial_Backups' in your Google Sheet to activate auto-saving.")

# --- BACKGROUND DATA PERSISTENCE ENGINE ---
def sync_ledger_to_cloud(project_name):
    """Saves the current project finances permanently to Google Sheets instantly."""
    if not backup_sheet_ready:
        return
    try:
        all_records = backup_sheet.get_all_records()
        rows_to_keep = [["Project", "Name", "Supplier", "Cost", "Qty", "Status"]]
        
        # Keep histories for other non-active workspaces
        for r in all_records:
            if r.get("Project") != project_name and r.get("Project"):
                rows_to_keep.append([r.get("Project"), r.get("Name"), r.get("Supplier"), r.get("Cost"), r.get("Qty"), r.get("Status")])
        
        # Append updated rows for this active workspace
        for line in st.session_state.projects[project_name]["financial_ledger"]:
            clean_name = str(line["name"]).replace("📄 ", "").replace("📸 ", "")
            rows_to_keep.append([
                project_name,
                clean_name,
                line["supplier"],
                line["cost"],
                line["qty"],
                line["status"]
            ])
            
        backup_sheet.clear()
        backup_sheet.update(range_name="A1", values=rows_to_keep)
    except Exception:
        pass

def discover_and_load_all_projects():
    """Scans the entire database to register all historic project workspaces instantly."""
    # Always guarantee baseline defaults are registered
    base_structure = {
        "Main Board": {"moodboard_items": [], "financial_ledger": [], "budget": 250000.0},
        "Project Llandudno": {"moodboard_items": [], "financial_ledger": [], "budget": 1000000.0}
    }
    
    if not backup_sheet_ready:
        return base_structure
        
    try:
        all_records = backup_sheet.get_all_records()
        
        # 1. Dynamically discover every unique project name saved in your sheet rows
        for r in all_records:
            p_name = r.get("Project")
            if p_name and p_name not in base_structure:
                base_structure[p_name] = {"moodboard_items": [], "financial_ledger": [], "budget": 100000.0}
                
        # 2. Re-populate ledger values into their respective dynamic workspaces
        for r in all_records:
            p_name = r.get("Project")
            if p_name in base_structure:
                supplier_str = str(r.get("Supplier", ""))
                prefix = "📄 " if "PDF" in supplier_str or "Scan" in supplier_str else ""
                base_structure[p_name]["financial_ledger"].append({
                    "name": f"{prefix}{r.get('Name')}",
                    "supplier": r.get("Supplier"),
                    "cost": float(r.get("Cost") or 0.0),
                    "qty": int(r.get("Qty") or 1),
                    "status": r.get("Status", "Pending"),
                    "image_data": None
                })
        return base_structure
    except Exception:
        return base_structure

# --- SESSION STATE INITIALIZATION ---
if 'projects' not in st.session_state:
    st.session_state.projects = discover_and_load_all_projects()

# Persistent dynamic selection helper
if 'active_project_selection' not in st.session_state:
    st.session_state.active_project_selection = "Main Board"

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
                text = page.extract_text()
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
    except Exception as e:
        return None

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
            st.session_state.active_project_selection = proj_title
            st.success(f"Created '{proj_title}'")
            st.rerun()
            
    st.write("---")
    
    # Track selection changes without dropping state parameters
    available_options = list(st.session_state.projects.keys())
    if st.session_state.active_project_selection not in available_options:
        st.session_state.active_project
