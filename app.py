import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Page Setup - Clean & Minimalist
st.set_page_config(page_title="Design Sourcing Pro", layout="wide")

# Secure connection to your Google Sheet
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Open your Master Supplier List
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

st.title("💡 Intelligent Sourcing Assistant")
st.markdown("---")

# The Smart Search Bar
query = st.text_input("What are you looking for?", placeholder="e.g. black leather couch, curtains, local lighting...")

if query:
    # This is the "Smart Brain" logic
    # It looks for words that *match* or *relate* to your categories
    search_terms = query.lower().split()
    results = []

    for row in data:
        # We combine all text in the row to give the AI more to "read"
        row_content = " ".join(str(val).lower() for val in row.values())
        if any(term in row_content for term in search_terms):
            results.append(row)

    if results:
        st.success(f"Found {len(results)} potential matches for '{query}'")
        
        for item in results:
            with st.container(border=True):
                # Layout: Name on the left, details on the right
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader(item.get('Supplier Name', 'Unknown'))
                    st.caption(f"📍 {item.get('Location', 'N/A')}")
                
                with col2:
                    st.write(f"**Category:** {item.get('Category', 'N/A')}")
                    
                    # Showing the "Intelligence" (Lead times/Stock)
                    lead = item.get('Lead Times', 'Contact for info')
                    stock = item.get('Stock Levels', 'Check availability')
                    st.write(f"⏳ **Lead Time:** {lead} | 📦 **Stock:** {stock}")
                    
                    # Email Button
                    contact_email = str(item.get('Contact / Specialty', '')).split('/')[-1].strip()
                    if "@" in contact_email:
                        mail_link = f"mailto:{contact_email}?subject=Inquiry: {query}"
                        st.link_button("📧 Contact Supplier", mail_link)
    else:
        st.warning("I couldn't find an exact match in your list. Try a broader term like 'Furniture' or 'Fabric'.")

st.markdown("---")
st.info("Note: This assistant only searches your vetted Master Supplier List.")
