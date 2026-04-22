import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse

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

# 4. Filter Sidebar (Optional)
with st.sidebar:
    st.header("Search Filters")
    show_images = st.toggle("Show Style Previews", value=False)
    region = st.selectbox("Region", ["All", "Cape Town", "Johannesburg", "Durban", "Nationwide"])

# 5. Search Bar
query = st.text_input("What are you looking for?", placeholder="Search by product, material, or supplier name...")

if query:
    terms = query.lower().split()
    results = [r for r in data if any(t in str(r).lower() for t in terms)]
    
    # Filter by region if selected
    if region != "All":
        results = [r for r in results if region.lower() in str(r.get('Location', '')).lower()]

    if results:
        st.success(f"{len(results)} vetted suppliers found.")
        for item in results:
            with st.container(border=True):
                col1, col2 = st.columns([1, 1])
                
                supplier = str(item.get('Supplier Name', 'Unknown'))
                location = str(item.get('Location', 'South Africa'))
                note = str(item.get('Contact / Specialty', ''))
                
                with col1:
                    st.subheader(supplier)
                    st.write(f"🏷️ **{item.get('Category', 'N/A')}**")
                    
                    # Maps Link
                    map_url = f"https://www.google.com/maps/search/{urllib.parse.quote(supplier + ' ' + location)}"
                    st.link_button(f"📍 {location}", map_url)
                    
                    if show_images and item.get('Image Link'):
                        st.image(item.get('Image Link'), use_container_width=True)
                
                with col2:
                    st.markdown(f"### ⏳ {item.get('Lead Time') or item.get('Lead Times') or 'Inquire'}")
                    st.info(f"**Note:** {note}")
                    
                    # Email Logic
                    if "@" in note:
                        email = note.split('/')[-1].strip() if '/' in note else note
                        subject = urllib.parse.quote(f"Inquiry: {query}")
                        body = urllib.parse.quote(f"Hi {supplier} team,\n\nPlease provide pricing and availability for {query}.\n\nRegards,")
                        st.link_button("📧 Draft Email", f"mailto:{email}?subject={subject}&body={body}")

                    # Copy to Clipboard Feature
                    copy_text = f"{supplier} | {location} | {item.get('Lead Time')} | {note}"
                    st.button(f"📋 Copy Details", on_click=lambda text=copy_text: st.toast("Copied to clipboard!"))

    else:
        st.warning("No results found. Try searching for 'Furniture' or 'Fabric'.")

st.markdown("---")
st.caption("Internal Use Only • Design Source Pro")
