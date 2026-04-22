import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse

# 1. Page Config
st.set_page_config(page_title="Sourcing Pro", layout="wide")

# 2. Database Connection
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# 3. Load Data
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

st.title("🏛️ Interior Design Master Assistant")
st.markdown("---")

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
                
                supplier = item.get('Supplier Name', 'Unknown')
                location = item.get('Location', 'South Africa')
                
                with col1:
                    st.subheader(supplier)
                    st.write(f"**Category:** {item.get('Category', 'N/A')}")
                    
                    # GOOGLE MAPS LINK: Clickable Address
                    map_url = f"https://www.google.com/maps/search/{urllib.parse.quote(supplier + ' ' + location)}"
                    st.link_button(f"📍 View Address: {location}", map_url)
                
                with col2:
                    # LEAD TIMES
                    lt = item.get('Lead Time') or item.get('Lead Times') or "Inquire"
                    st.markdown(f"### ⏳ Lead Time: {lt}")
                    
                    # NOTES
                    note = item.get('Contact / Specialty', 'Vetted Supplier')
                    st.info(f"**Note:** {note}")
                    
                    # DRAFT EMAIL BUTTON
                    if "@" in str(note):
                        email = str(note).split('/')[-1].strip()
                        # This creates a professional subject line automatically
                        subject = urllib.parse.quote(f"Product Inquiry: {query} (via Simply Roarke)")
                        body = urllib.parse.quote(f"Hi {supplier} team,\n\nI hope you are well. I am inquiring about {query} options. Please let me know current availability.\n\nKind regards,")
                        
                        mail_link = f"mailto:{email}?subject={subject}&body={body}"
                        st.link_button(f"📧 Draft Email to {supplier}", mail_link)
    else:
        st.warning("No matches found. Try a different keyword.")

st.markdown("---")
st.caption("Custom Assistant for Professional Sourcing")
