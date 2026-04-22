import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# 1. Clean Page Setup
st.set_page_config(page_title="Sourcing Pro", layout="wide")

# 2. Database Connection
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# 3. Open your specific Google Sheet
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

st.title("💡 Designer's Sourcing Assistant")
st.markdown("---")

# 4. Search Bar
query = st.text_input("What are you looking for today?", placeholder="e.g. Couch, Fabric, Crema...")

if query:
    terms = query.lower().split()
    # Search every row for your keywords
    results = [r for r in data if any(t in str(r).lower() for t in terms)]

    if results:
        st.success(f"Found {len(results)} matches in your master list.")
        for item in results:
            with st.container(border=True):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader(item.get('Supplier Name', 'Unknown'))
                    st.write(f"**Category:** {item.get('Category', 'N/A')}")
                    st.caption(f"📍 {item.get('Location', 'N/A')}")
                
                with col2:
                    # SMART LEAD TIME CHECK: Looks for 'Lead Time' (Singular) or 'Lead Times' (Plural)
                    lt = item.get('Lead Time') or item.get('Lead Times') or "Inquire"
                    st.markdown(f"### ⏳ {lt}")
                    
                    # Specialty/Contact Info Notes
                    note = item.get('Contact / Specialty', 'Vetted Supplier')
                    st.info(f"**Notes:** {note}")
                    
                    # Email button if an email address exists in the notes
                    if "@" in str(note):
                        email = str(note).split('/')[-1].strip()
                        st.link_button(f"📧 Contact {item.get('Supplier Name')}", f"mailto:{email}")
    else:
        st.warning("I couldn't find that in your list. Try a broader search like 'Furniture'.")

st.markdown("---")
st.caption("Powered by your Master Supplier List • South Africa")
