import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Minimalist Layout
st.set_page_config(page_title="Sourcing Pro", layout="wide")

# Database Connection
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

st.title("🔎 Sourcing Assistant")
st.info("Searching your Master Supplier List...")

query = st.text_input("What do you need?", placeholder="e.g. Fabric, Marble, Crema...")

if query:
    terms = query.lower().split()
    results = [r for r in data if any(t in str(r).lower() for t in terms)]

    if results:
        for item in results:
            with st.container(border=True):
                # We put the most important info in columns so it's easy to read
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader(item.get('Supplier Name', 'N/A'))
                    st.write(f"**Category:** {item.get('Category', 'N/A')}")
                    st.caption(f"📍 {item.get('Location', 'N/A')}")
                
                with col2:
                    # HIGHLIGHTING LEAD TIMES FOR EFFICIENCY
                    lead_time = item.get('Lead Time', 'Inquire')
                    st.markdown(f"### ⏳ {lead_time}")
                    
                    # Specialty/Contact Info
                    specialty = item.get('Contact / Specialty', '')
                    st.write(f"**Note:** {specialty}")
                    
                    # Quick Email Button
                    if "@" in str(specialty):
                        email = str(specialty).split('/')[-1].strip()
                        st.link_button("📧 Quick Email", f"mailto:{email}")
    else:
        st.warning("No matches found in your list.")
