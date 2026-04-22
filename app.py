import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
import re

# 1. Page Config
st.set_page_config(page_title="Design Source Pro", layout="wide", initial_sidebar_state="collapsed")

# 2. Database Connection
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# 3. Load Data
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

st.title("🏛️ Design Source Pro")

# 4. Sidebar with WhatsApp Toggle
with st.sidebar:
    st.header("Communication Filters")
    only_whatsapp = st.toggle("Show only WhatsApp-ready suppliers")
    st.divider()
    st.caption("Tip: Add phone numbers to your Google Sheet to see more buttons.")

# 5. Search & Filter Logic
query = st.text_input("Search Suppliers", placeholder="e.g. Leather, Tiles, Crema...")

# Helper to find phone numbers
def find_phone(text):
    match = re.search(r'(\+27|0)\d{9}', str(text).replace(" ", ""))
    if match:
        num = match.group()
        return num.replace("0", "27", 1) if num.startswith("0") else num
    return None

if query or only_whatsapp:
    results = data
    
    # If search is typed
    if query:
        terms = query.lower().split()
        results = [r for r in results if any(t in str(r).lower() for t in terms)]
    
    # If WhatsApp toggle is ON
    if only_whatsapp:
        results = [r for r in results if find_phone(r.get('Contact / Specialty', ''))]

    if results:
        st.success(f"Found {len(results)} Suppliers")
        for item in results:
            with st.container(border=True):
                col1, col2 = st.columns([1, 1])
                supplier = str(item.get('Supplier Name', 'Unknown'))
                location = str(item.get('Location', 'South Africa'))
                note = str(item.get('Contact / Specialty', ''))
                
                with col1:
                    st.subheader(supplier)
                    st.write(f"🏷️ **{item.get('Category', 'N/A')}**")
                    map_url = f"https://www.google.com/maps/search/{urllib.parse.quote(supplier + ' ' + location)}"
                    st.link_button(f"📍 {location}", map_url)
                
                with col2:
                    lt = item.get('Lead Time') or item.get('Lead Times') or "Inquire"
                    st.markdown(f"### ⏳ {lt}")
                    st.info(f"**Note:** {note}")
                    
                    b_col1, b_col2 = st.columns(2)
                    with b_col1:
                        if "@" in note:
                            email = note.split('/')[-1].strip() if '/' in note else note
                            mail_link = f"mailto:{email}?subject=Inquiry&body=Hi {supplier}..."
                            st.link_button("📧 Email", mail_link, use_container_width=True)
                    
                    with b_col2:
                        phone = find_phone(note)
                        if phone:
                            wa_url = f"https://wa.me/{phone}?text=Hi {supplier}, I'm inquiring via Design Source Pro."
                            st.link_button("💬 WhatsApp", wa_url, use_container_width=True)
