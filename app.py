import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse

# Page Setup - This makes it look like a real website
st.set_page_config(page_title="Design Sourcing Pro", layout="wide")
st.title("🌟 Designer's Sourcing Dashboard")

# Secure connection to your Google Sheet
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Open your specific Master Supplier List
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

# The Search Bar - Clean and simple
search = st.text_input("Search by Name, Category, or Location:", placeholder="e.g. Furniture, Cape Town...")

if search:
    results = [row for row in data if search.lower() in str(row.values()).lower()]
    st.write(f"✅ Found {len(results)} matches")
    
    # Grid Layout
    cols = st.columns(3) 
    for i, item in enumerate(results):
        with cols[i % 3]:
            name = item.get('Supplier Name', 'N/A')
            cat = item.get('Category', 'N/A')
            loc = item.get('Location', 'N/A')
            img = item.get('Image Link', "")
            
            if not img or len(str(img)) < 5:
                img = "https://placehold.co/400x300/e0e0e0/666666?text=Design+Preview"
            
            with st.container(border=True):
                st.image(img, use_container_width=True)
                st.subheader(name)
                st.caption(f"📍 {loc} | {cat}")
                
                # Professional Buttons
                contact = item.get('Contact / Specialty', '')
                email = contact.split('/')[-1].strip() if '/' in contact else ""
                mail_link = f"mailto:{email}?subject=Inquiry from Simply Roarke"
                st.link_button("📧 Email Supplier", mail_link)
