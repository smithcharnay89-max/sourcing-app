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
st.caption("Professional Sourcing & Logistics Assistant")

# 4. Search Bar
query = st.text_input("What are you sourcing today?", placeholder="e.g. Leather, Tiles, Crema...")

if query:
    terms = query.lower().split()
    results = [r for r in data if any(t in str(r).lower() for t in terms)]

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
                    st.markdown(f"### ⏳ Lead Time: {lt}")
                    st.info(f"**Note:** {note}")
                    
                    # COMMUNICATION BUTTONS
                    btn_col1, btn_col2 = st.columns(2)
                    
                    with btn_col1:
                        # EMAIL LOGIC
                        if "@" in note:
                            email = note.split('/')[-1].strip() if '/' in note else note
                            subject = urllib.parse.quote(f"Inquiry: {query}")
                            body = urllib.parse.quote(f"Hi {supplier} team,\n\nI am inquiring about {query}.\n\nKind regards,\n[Your Name]")
                            st.link_button("📧 Email", f"mailto:{email}?subject={subject}&body={body}", use_container_width=True)

                    with btn_col2:
                        # WHATSAPP LOGIC - Extracts numbers from the note
                        phone_match = re.search(r'(\+27|0)\d{9}', note.replace(" ", ""))
                        if phone_match:
                            phone = phone_match.group().replace("0", "27", 1) if phone_match.group().startswith("0") else phone_match.group()
                            wa_msg = urllib.parse.quote(f"Hi {supplier}, I'm inquiring about {query} options via Design Source Pro.")
                            st.link_button("💬 WhatsApp", f"https://wa.me/{phone}?text={wa_msg}", use_container_width=True)
    else:
        st.warning("No matches found.")

st.markdown("---")
st.caption("Internal Use Only • Design Source Pro")
