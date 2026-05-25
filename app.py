import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re

# 1. Setup
st.set_page_config(page_title="Design Source Pro", layout="wide")

# 2. Connection
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)
SHEET_ID = "16FVZwJEuiFB50Assgdx4weL9HqdO5t1MpYoUPvoEAo8" 
sheet = client.open_by_key(SHEET_ID).sheet1
data = sheet.get_all_records()

# --- HYBRID SESSION STATE MANAGEMENT ---
if 'projects' not in st.session_state:
    st.session_state.projects = {
        "Main Board": {
            "items": [],        # Items pinned from the Google Sheet
            "ad_hoc": [],       # Manually entered custom expenses
            "budget": 250000.0  # Default project budget
        }
    }

# 3. Sidebar for Project Management
with st.sidebar:
    st.header("📂 Project Operations")
    
    new_project_name = st.text_input("Create New Project", placeholder="e.g. Smith Residence")
    if st.button("➕ Create Project") and new_project_name.strip():
        proj_title = new_project_name.strip()
        if proj_title not in st.session_state.projects:
            st.session_state.projects[proj_title] = {
                "items": [],
                "ad_hoc": [],
                "budget": 100000.0  # Starting default budget
            }
            st.success(f"Created '{proj_title}'")
            st.rerun()
            
    st.write("---")
    
    active_project = st.selectbox(
        "Current Active Project", 
        options=list(st.session_state.projects.keys())
    )
    
    st.write("---")
    # Dynamic Budget Input for the Active Project
    current_budget = st.number_input(
        "Set Client Total Budget (R)", 
        min_value=0.0, 
        value=float(st.session_state.projects[active_project]["budget"]), 
        step=5000.0
    )
    st.session_state.projects[active_project]["budget"] = current_budget

# Conversational helper logic
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

def add_to_board(item, project):
    title = item.get('Supplier Name') or item.get('Brand') or item.get('Product Name') or "Unknown Item"
    # Attach a default baseline cost/qty structure to sheet items for financial compatibility
    item_copy = item.copy()
    if 'Cost' not in item_copy:
        # Tries to look for price tags in your sheet data, default to 0.0 if not specified
        item_copy['Cost'] = float(item.get('Price') or item.get('Unit Cost') or 0.0)
    item_copy['Quantity'] = 1
    item_copy['Status'] = 'Pending'
    
    existing_items = st.session_state.projects[project]["items"]
    if title not in [x.get('Supplier Name') or x.get('Brand') or x.get('Product Name') for x in existing_items]:
        st.session_state.projects[project]["items"].append(item_copy)
        st.toast(f"Added {title} to {project}!")
    else:
        st.toast("ℹ️ Already in project board")

st.title("🏛️ Design Source Pro")
st.caption(f"📍 Currently managing operational dashboards for: **{active_project}**")

# TABS: Adding the crucial financial dashboard
tab1, tab2, tab3 = st.tabs(["🔎 Smart Assistant", "🎨 Project Boards", "📊 Project Finances"])

# --- TAB 1: SMART ASSISTANT SEARCH ---
with tab1:
    query = st.text_input("Ask the Assistant", placeholder="e.g., Where can I find a black leather couch?")
    if query:
        search_terms = clean_conversational_query(query)
        if search_terms:
            scored_results = []
            for row in data:
                row_string = str(row).lower()
                match_count = sum(1 for term in search_terms if term in row_string)
                if match_count > 0:
                    scored_results.append((match_count, row))
            
            results = [item[1] for item in sorted(scored_results, key=lambda x: x[0], reverse=True)]
            
            if results:
                st.write(f"✨ *Keyword matches found: `{', '.join(search_terms)}`*")
                for item in results:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            title = item.get('Supplier Name') or item.get('Brand') or item.get('Product Name') or "Unknown Item"
                            st.subheader(title)
                            st.write(f"**Category:** {item.get('Category', 'N/A')} | ⏳ **Lead Time:** {item.get('Lead Time', 'N/A')}")
                            
                            stock_val = item.get('Stock Level') or item.get('Stock') or 'Available to Order'
                            st.write(f"📦 **Stock/Availability:** {stock_val}")
                            
                            email_val = extract_clean_email(item)
                            if email_val != 'N/A':
                                st.write(f"✉️ **Email:** [{email_val}](mailto:{email_val})")
                            if item.get('Website'):
                                st.markdown(f"🔗 [Visit Website]({item.get('Website')})")
                        with c2:
                            st.button(f"➕ Add to {active_project}", key=f"a_{title}_{active_project}", on_click=add_to_board, args=(item, active_project))
            else:
                st.warning(f"No explicit matches found for `{', '.join(search_terms)}`.")

# --- TAB 2: PROJECT VISUAL MOODBOARD & AD-HOC LOGGING ---
with tab2:
    st.header(f"🎨 Visual Moodboard: {active_project}")
    
    # Ad-Hoc Form to capture items NOT in your spreadsheet instantly
    with st.expander("➕ Log Ad-Hoc Purchase / Project Expense (Saves Instantly without Inventory)"):
        c_name = st.text_input("Item / Expense Description", placeholder="e.g. Custom Black Leather Accent Chair")
        c_supplier = st.text_input("Supplier / Store Name", placeholder="e.g. Weylandts")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            c_cost = st.number_input("Unit Cost (R)", min_value=0.0, step=100.0)
        with col_c2:
            c_qty = st.number_input("Quantity Required", min_value=1, step=1, value=1)
        with col_c3:
            c_status = st.selectbox("Financial Status", ["Pending", "Quoted", "Paid"])
            
        if st.button("💾 Log Custom Expense to Project"):
            if c_name.strip():
                new_adhoc = {
                    "Product Name": c_name.strip(),
                    "Supplier Name": c_supplier.strip() if c_supplier.strip() else "Direct Vendor",
                    "Cost": float(c_cost),
                    "Quantity": int(c_qty),
                    "Status": c_status,
                    "Category": "Custom Selection"
                }
                st.session_state.projects[active_project]["ad_hoc"].append(new_adhoc)
                st.toast("✅ Custom item added straight to project financial ledger!")
                st.rerun()
            else:
                st.error("Please provide an item description.")

    st.write("---")
    
    # Render unified visual layout
    sheet_items = st.session_state.projects[active_project]["items"]
    adhoc_items = st.session_state.projects[active_project]["ad_hoc"]
    all_visual_items = sheet_items + adhoc_items
    
    if all_visual_items:
        cols = st.columns(3)
        for idx, board_item in enumerate(all_visual_items):
            with cols[idx % 3]:
                with st.container(border=True):
                    img_url = board_item.get('Image Link') or board_item.get('Image') or board_item.get('Photo')
                    cat = board_item.get('Category') or 'Item'
                    
                    if not img_url:
                        # Professional presentation placeholder card for manual entries or items missing images
                        st.markdown(f"<div style='background-color:#EAE6DF; padding:40px; text-align:center; border-radius:5px;'><h3>🛋️</h3><small style='color:#666;'>{cat.upper()}</small></div>", unsafe_allow_html=True)
                    else:
                        st.image(img_url, use_container_width=True)
                    
                    title_text = board_item.get('Supplier Name') or board_item.get('Brand') or board_item.get('Product Name') or "Project Selection"
                    st.write(f"**{title_text}**")
                    if board_item.get('Product Name') and board_item.get('Supplier Name') != board_item.get('Product Name'):
                        st.caption(f"Desc: {board_item.get('Product Name')}")
                    
                    st.caption(f"💰 Cost Allocation: R{board_item.get('Cost', 0.0):,.2f} x {board_item.get('Quantity', 1)}")
    else:
        st.info("No selections saved to this project board yet.")

# --- TAB 3: PROJECT FINANCES & EXPENSE MANAGEMENT ---
with tab3:
    st.header(f"📊 Financial Procurement Ledger: {active_project}")
    
    project_data = st.session_state.projects[active_project]
    proj_items = project_data["items"]
    proj_adhoc = project_data["ad_hoc"]
    
    # 1. Calculation Engine
    total_spent = 0.0
    all_lines = []
    
    # Format database rows and ad-hoc rows into a clean math table data matrix
    for idx, item in enumerate(proj_items):
        name = item.get('Supplier Name') or item.get('Brand') or "Database Item"
        cost = float(item.get('Cost', 0.0))
        qty = int(item.get('Quantity', 1))
        line_total = cost * qty
        total_spent += line_total
        all_lines.append({"type": "sheet", "idx": idx, "name": name, "supplier": item.get('Category', 'Catalog'), "cost": cost, "qty": qty, "total": line_total, "status": item.get('Status', 'Pending')})
        
    for idx, item in enumerate(proj_adhoc):
        name = item.get('Product Name', 'Custom Expense')
        cost = float(item.get('Cost', 0.0))
        qty = int(item.get('Quantity', 1))
        line_total = cost * qty
        total_spent += line_total
        all_lines.append({"type": "adhoc", "idx": idx, "name": name, "supplier": item.get('Supplier Name', 'Custom'), "cost": cost, "qty": qty, "total": line_total, "status": item.get('Status', 'Pending')})

    budget_limit = project_data["budget"]
    remaining_budget = budget_limit - total_spent
    
    # 2. Metric Highlight Widgets
    m1, m2, m3 = st.columns(3)
    m1.metric("Target Project Budget", f"R{budget_limit:,.2f}")
    m2.metric("Total Line Allocation", f"R{total_spent:,.2f}")
    
    if remaining_budget >= 0:
        m3.metric("Remaining Balance (Surplus)", f"R{remaining_budget:,.2f}", delta="Within Budget")
    else:
        m3.metric("Remaining Balance (Deficit)", f"R{remaining_budget:,.2f}", delta="- OVER BUDGET", delta_color="inverse")
        st.error(f"🚨 Operational Warning: Project allocations currently exceed assigned budget constraints by R{abs(remaining_budget):,.2f}")

    st.write("---")
    st.subheader("📋 Expense Line-Item Calculations")
    
    if all_lines:
        # Render a real interactive editor layout so you can tune your numbers live in front of clients/employers
        for line in all_lines:
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                with col1:
                    st
