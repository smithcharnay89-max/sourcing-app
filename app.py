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

# --- BACKGROUND DATA PERSISTENCE ENGINE (MULTI-TAB ARCHITECTURE) ---
def sync_ledger_to_cloud(project_name):
    """Saves records to a dedicated worksheet tab named after the project itself."""
    try:
        # Sanitize name to make sure it's a valid Google Sheets tab title
        tab_title = str(project_name).strip()[:30]
        
        # Open the worksheet if it exists, or dynamically create a brand-new tab if it doesn't
        try:
            worksheet = spreadsheet.worksheet(tab_title)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=tab_title, rows="100", cols="10")
            
        active_ledger = st.session_state.projects[project_name]["financial_ledger"]
        budget_limit = float(st.session_state.projects[project_name]["budget"])
        total_spent = sum(float(line['cost'] or 0.0) * int(line['qty'] or 1) for line in active_ledger)
        remaining_balance = budget_limit - total_spent
        
        # Structure a beautiful, presentation-ready client invoice layout
        sheet_layout = [
            ["--- BUDGET SUMMARY ---", f"CLIENT WORKSPACE: {tab_title}", "", "", "", ""],
            ["Total Allocated Budget:", budget_limit, "", "", "", ""],
            ["Total Funds Allocated Spent:", total_spent, "Remaining Project Balance:", remaining_balance, "", ""],
            ["", "", "", "", "", ""], 
            ["Project Workspace", "Item Description", "Supplier / Vendor", "Unit Cost (R)", "Quantity", "Approval Status"]
        ]
        
        # Append rows strictly isolated to this sheet tab
        for line in active_ledger:
            clean_name = str(line["name"]).replace("📄 ", "").replace("📸 ", "")
            sheet_layout.append([
                tab_title,
                str(clean_name),
                str(line["supplier"]),
                float(line["cost"] or 0.0),
                int(line["qty"] or 1),
                str(line["status"])
            ])
            
        worksheet.clear()
        worksheet.update(range_name="A1", values=sheet_layout)
    except Exception:
        pass

def discover_and_load_all_projects():
    """Discovers all projects dynamically by scanning every separate tab title inside your sheet file."""
    base_structure = {
        "Main Board": {"moodboard_items": [], "financial_ledger": [], "budget": 250000.0},
        "Project Llandudno": {"moodboard_items": [], "financial_ledger": [], "budget": 1000000.0},
        "Project Welgemoed": {"moodboard_items": [], "financial_ledger": [], "budget": 1000000.0}
    }
    
    try:
        # Scan through all available tabs inside the Google Sheet document
        all_worksheets = spreadsheet.worksheets()
        
        for ws in all_worksheets:
            title = ws.title
            # Ignore sheet1 (the master catalog)
            if title == sheet.title:
                continue
                
            try:
                # Read the historical entries safely from Row 5 downwards for each tab
                records = ws.get_all_records(expected_headers=[], head=5)
                
                # Dynamic tab configuration registration
                if title not in base_structure:
                    base_structure[title] = {"moodboard_items": [], "financial_ledger": [], "budget": 100000.0}
                
                # Extract historical client budget numbers directly from cell B2 if present
                try:
                    raw_rows = ws.get_all_values()
                    if len(raw_rows) >= 2 and raw_rows[1][1]:
                        base_structure[title]["budget"] = float(raw_rows[1][1])
                except Exception:
                    pass
                    
                for r in records:
                    desc = r.get("Item Description") or r.get("Name")
                    if desc:
                        supplier_str = str(r.get("Supplier / Vendor") or r.get("Supplier", ""))
                        prefix = "📄 " if "PDF" in supplier_str or "Scan" in supplier_str else ""
                        
                        existing_ledger = base_structure[title]["financial_ledger"]
                        item_name = f"{prefix}{desc}"
                        
                        if not any(item['name'] == item_name for item in existing_ledger):
                            base_structure[title]["financial_ledger"].append({
                                "name": item_name,
                                "supplier": r.get("Supplier / Vendor") or r.get("Supplier") or "Unknown",
                                "cost": float(r.get("Unit Cost (R)") or r.get("Cost") or 0.0),
                                "qty": int(r.get("Quantity") or r.get("Qty") or 1),
                                "status": r.get("Approval Status") or r.get("Status") or "Pending",
                                "image_data": None
                            })
            except Exception:
                continue
                
        return base_structure
    except Exception:
        return base_structure

# --- SESSION STATE INITIALIZATION ---
if 'projects' not in st.session_state:
    st.session_state.projects = discover_and_load_all_projects()

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
                "budget": 1000000.0
            }
            st.session_state.active_project_selection = proj_title
            sync_ledger_to_cloud(proj_title) # Create the tab instantly
            st.success(f"Created '{proj_title}' Workspace Tab!")
            st.rerun()
            
    st.write("---")
    
    available_options = list(st.session_state.projects.keys())
    if st.session_state.active_project_selection not in available_options:
        st.session_state.active_project_selection = available_options[0]
        
    active_project = st.selectbox(
        "Current Active Project", 
        options=available_options,
        index=available_options.index(st.session_state.active_project_selection)
    )
    st.session_state.active_project_selection = active_project
    
    st.write("---")
    current_budget = st.number_input(
        "Set Client Total Budget (R)", 
        min_value=0.0, 
        value=float(st.session_state.projects[active_project]["budget"]), 
        step=5000.0
    )
    
    if current_budget != st.session_state.projects[active_project]["budget"]:
        st.session_state.projects[active_project]["budget"] = current_budget
        sync_ledger_to_cloud(active_project)
        st.rerun()

# --- MAIN APP INTERFACE ---
st.title("🏛️ Design Source Pro")
st.caption(f"📍 Active Tab Workspace: **{active_project}**")

tab1, tab2, tab3 = st.tabs(["🔎 Smart Assistant", "🎨 Project Moodboard", "📊 Project Finances"])

# --- TAB 1: SMART ASSISTANT ---
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
                for item in results:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            title = item.get('Supplier Name') or item.get('Brand') or item.get('Product Name') or "Unknown Item"
                            st.subheader(title)
                            st.write(f"**Category:** {item.get('Category', 'N/A')} | ⏳ **Lead Time:** {item.get('Lead Time', 'N/A')}")
                            st.write(f"📦 **Availability:** {item.get('Stock Level') or 'Available to Order'}")
                            email_val = extract_clean_email(item)
                            if email_val != 'N/A':
                                st.write(f"✉️ **Email:** [{email_val}](mailto:{email_val})")
                        with c2:
                            st.button(f"➕ Save to Board", key=f"src_{title}_{active_project}", on_click=add_to_moodboard, args=(item, active_project))

# --- TAB 2: VISUAL MOODBOARD ---
with tab2:
    st.header(f"🎨 Visual Moodboard: {active_project}")
    with st.expander("🔗 Clip Web Inspiration (Pinterest, Web Links, etc.)", expanded=False):
        col_clip1, col_clip2 = st.columns([2, 1])
        with col_clip1:
            web_img_url = st.text_input("Paste Image Address URL", placeholder="https://pinterest.com/pin/example.jpg")
        with col_clip2:
            web_img_title = st.text_input("Inspiration Label", placeholder="e.g., Lounge Concept")
            web_img_cat = st.text_input("Category Type", placeholder="e.g., Furniture")
            
        if st.button("📌 Pin to Moodboard"):
            if web_img_url.strip() and web_img_title.strip():
                st.session_state.projects[active_project]["moodboard_items"].append({
                    "title": web_img_title.strip(),
                    "image": web_img_url.strip(),
                    "category": web_img_cat.strip() if web_img_cat.strip() else "Web Inspiration",
                    "source": "Web Clipper"
                })
                st.success(f"Pinned '{web_img_title}' successfully!")
                st.rerun()

    st.write("---")
    board_items = st.session_state.projects[active_project]["moodboard_items"]
    if board_items:
        cols = st.columns(3)
        for idx, board_item in enumerate(board_items):
            with cols[idx % 3]:
                with st.container(border=True):
                    if board_item.get('image'):
                        st.image(board_item['image'], use_container_width=True)
                    st.write(f"**{board_item.get('title')}**")
                    st.caption(f"🏷️ {board_item.get('category')} | 📍 {board_item.get('source')}")
                    if st.button("🗑️ Remove Pin", key=f"rm_pin_{idx}_{active_project}"):
                        st.session_state.projects[active_project]["moodboard_items"].pop(idx)
                        st.rerun()
    else:
        st.info("Your visual moodboard is empty.")

# --- TAB 3: PROJ FINANCES ---
with tab3:
    st.header(f"📊 Project Procurement Ledger: {active_project}")
    ledger = st.session_state.projects[active_project]["financial_ledger"]
    col_left, col_right = st.columns([1, 1] if len(ledger) > 0 else [1, 2])
    
    with col_left:
        st.subheader("➕ Add Expenses")
        
        with st.expander("📥 Option A: Import From Moodboard", expanded=False):
            mb_options = [item.get('title') for item in board_items]
            selected_mb_item = st.selectbox("Select saved item", options=["-- Select Item --"] + mb_options)
            if st.button("📥 Import to Ledger") and selected_mb_item != "-- Select Item --":
                target_item = next(item for item in board_items if item.get('title') == selected_mb_item)
                st.session_state.projects[active_project]["financial_ledger"].append({
                    "name": selected_mb_item, "supplier": target_item.get('source', 'Catalog'),
                    "cost": 0.0, "qty": 1, "status": "Pending", "image_data": None
                })
                sync_ledger_to_cloud(active_project)
                st.rerun()
                
        with st.expander("💾 Option B: Log Custom Purchase", expanded=True):
            c_name = st.text_input("Description")
            c_supplier = st.text_input("Supplier")
            c_cost = st.number_input("Unit Cost (R)", min_value=0.0, step=100.0)
            c_qty = st.number_input("Quantity", min_value=1, step=1, value=1)
            c_status = st.selectbox("Status", ["Pending", "Quoted", "Paid"])
            if st.button("💾 Log Custom Expense"):
                if c_name.strip():
                    st.session_state.projects[active_project]["financial_ledger"].append({
                        "name": c_name.strip(), "supplier": c_supplier.strip() or "Direct Vendor",
                        "cost": float(c_cost), "qty": int(c_qty), "status": c_status, "image_data": None
                    })
                    sync_ledger_to_cloud(active_project)
                    st.rerun()
        
        with st.expander("⚡ Option C: Capture Quote / Snap Receipt", expanded=False):
            input_mode = st.radio("Capture Method", ["📁 Upload Digital PDF", "📸 Mobile Camera Snap"], horizontal=True)
            if input_mode == "📁 Upload Digital PDF":
                uploaded_quote = st.file_uploader("Upload Supplier PDF Document", type=["pdf"])
                if st.button("🔍 Run Document Scan"):
                    if uploaded_quote is not None:
                        with st.spinner("Extracting parameters..."):
                            parsed_result = parse_quote_pdf(uploaded_quote)
                            if parsed_result:
                                st.session_state.projects[active_project]["financial_ledger"].append(parsed_result)
                                sync_ledger_to_cloud(active_project)
                                st.rerun()
                            else:
                                st.error("Could not read text details from this specific document structure.")
            else:
                camera_image = st.camera_input("Position receipt clearly")
                cam_name = st.text_input("Receipt Label")
                cam_supplier = st.text_input("Vendor")
                cam_cost = st.number_input("Total Amount (R)", min_value=0.0, step=50.0)
                if st.button("💾 Save Camera Snap to Ledger"):
                    if camera_image is not None and cam_name.strip():
                        st.session_state.projects[active_project]["financial_ledger"].append({
                            "name": f"📸 {cam_name.strip()}", "supplier": cam_supplier.strip() or "On-Site",
                            "cost": float(cam_cost), "qty": 1, "status": "Paid", "image_data": camera_image.getvalue()
                        })
                        sync_ledger_to_cloud(active_project)
                        st.rerun()

    with col_right:
        st.subheader("📋 Budget Calculator")
        budget_limit = st.session_state.projects[active_project]["budget"]
        total_spent = sum(line['cost'] * line['qty'] for line in ledger)
        remaining_budget = budget_limit - total_spent
        
        m1, m2 = st.columns(2)
        m1.metric("Total Cost Allocation", f"R{total_spent:,.2f}")
        m2.metric("Remaining Balance", f"R{remaining_budget:,.2f}", delta="Within Budget" if remaining_budget >= 0 else "Over Budget", delta_color="normal" if remaining_budget >= 0 else "inverse")
        
        if ledger:
            export_df = pd.DataFrame([{
                "Project": active_project, "Description": str(line["name"]).replace("📄 ", "").replace("📸 ", ""),
                "Supplier": line["supplier"], "Unit Cost (R)": line["cost"], "Quantity": line["qty"],
                "Total (R)": line["cost"] * line["qty"], "Status": line["status"]
            } for line in ledger])
            st.download_button(
                label="📥 Export Ledger to Excel (.csv)", data=export_df.to_csv(index=False),
                file_name=f"DesignSourcePro_{active_project}.csv", mime="text/csv"
            )
            
        st.write("---")
        if ledger:
            for idx, line in enumerate(ledger):
                with st.container(border=True):
                    grid1, grid2 = st.columns([3, 2])
                    with grid1:
                        st.write(f"**{line['name']}**")
                        st.caption(f"Supplier: {line['supplier']} | Total: R{line['cost']*line['qty']:,.2f}")
                        if line.get("image_data"):
                            st.image(line["image_data"], width=150)
                    with grid2:
                        new_cost = st.number_input(f"Cost (R)##{idx}", min_value=0.0, value=line['cost'], key=f"c_{idx}_{active_project}")
                        new_qty = st.number_input(f"Qty##{idx}", min_value=1, value=line['qty'], key=f"q_{idx}_{active_project}")
                        new_stat = st.selectbox(f"Status##{idx}", ["Pending", "Quoted", "Paid"], index=["Pending", "Quoted", "Paid"].index(line['status']), key=f"s_{idx}_{active_project}")
                        
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("✏️ Save Changes", key=f"save_{idx}_{active_project}"):
                                st.session_state.projects[active_project]["financial_ledger"][idx].update({
                                    "cost": new_cost, 
                                    "qty": new_qty, 
                                    "status": new_stat
                                })
                                sync_ledger_to_cloud(active_project)
                                st.toast("✅ Google Sheet Updated!")
                                st.rerun()
                        with btn_col2:
                            if st.button("🗑️ Remove", key=f"del_{idx}_{active_project}"):
                                st.session_state.projects[active_project]["financial_ledger"].pop(idx)
                                sync_ledger_to_cloud(active_project)
                                st.rerun()
