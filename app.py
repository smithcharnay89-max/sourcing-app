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

# --- SIMPLIFIED SESSION STATE ---
if 'projects' not in st.session_state:
    st.session_state.projects = {
        "Main Board": {
            "moodboard_items": [],  
            "financial_ledger": [], 
            "budget": 250000.0      
        }
    }

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
                "budget": 100000.0
            }
            st.success(f"Created '{proj_title}'")
            st.rerun()
            
    st.write("---")
    
    active_project = st.selectbox(
        "Current Active Project", 
        options=list(st.session_state.projects.keys())
    )
    
    st.write("---")
    # Clean float value step normalization to clear commas from interface
    current_budget = st.number_input(
        "Set Client Total Budget (R)", 
        min_value=0.0, 
        value=float(st.session_state.projects[active_project]["budget"]), 
        step=5000.0
    )
    st.session_state.projects[active_project]["budget"] = current_budget

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
    if title not in [x.get('Supplier Name') or x.get('Brand') or x.get('Product Name') for x in existing]:
        st.session_state.projects[project]["moodboard_items"].append(item)
        st.toast(f"Saved {title} to Moodboard!")
    else:
        st.toast("ℹ️ Already on your Moodboard")

# ADVANCED EXTRACTION ENGINE USING PDFPLUMBER
def parse_quote_pdf(file_upload):
    try:
        import pdfplumber
        full_text = ""
        
        # pdfplumber systematically walks through structural tables and columns
        with pdfplumber.open(file_upload) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True) # Retains tabular structural proximity
                if text:
                    full_text += text + "\n"
                    
        if not full_text.strip():
            return None
            
        # Expanded Regex pattern matching variants common in SA invoicing (e.g., R 15 000.00, R15,400.99, 1200.00)
        amounts = re.findall(r'(?:R?\s?\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2}))', full_text)
        
        clean_amounts = []
        for amt in amounts:
            # Clean symbols out to isolate raw float allocations safely
            c_amt = amt.replace('R', '').replace(' ', '').replace(',', '')
            try:
                val = float(c_amt)
                # Filter out obvious micro line item details or quantities (under R100)
                if val >= 100.0:
                    clean_amounts.append(val)
            except ValueError:
                continue
                
        # Target the maximum numeric parameter as the primary grand total summary
        detected_total = max(clean_amounts) if clean_amounts else 0.0
        
        # Establish a description name string from document parameters
        lines = [l.strip() for l in full_text.split('\n') if l.strip()]
        detected_title = "Scanned Document"
        if lines:
            # Try to grab the first text element line that isn't purely numbers
            for line in lines[:3]:
                if len(line) > 4 and not line.replace('.','').replace(',','').isdigit():
                    detected_title = line[:30]
                    break
        
        return {
            "name": f"📄 {detected_title}",
            "supplier": "Imported Supplier Quote",
            "cost": detected_total,
            "qty": 1,
            "status": "Quoted"
        }
    except ImportError:
        st.error("The upgraded scanning extension is compiling on the server platform. Give it a brief moment.")
        return None
    except Exception as e:
        return None


st.title("🏛️ Design Source Pro")
st.caption(f"📍 Managing: **{active_project}**")

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
                            
                            stock_val = item.get('Stock Level') or item.get('Stock') or 'Available to Order'
                            st.write(f"📦 **Availability:** {stock_val}")
                            
                            email_val = extract_clean_email(item)
                            if email_val != 'N/A':
                                st.write(f"✉️ **Email:** [{email_val}](mailto:{email_val})")
                        with c2:
                            st.button(f"➕ Save to Board", key=f"src_{title}_{active_project}", on_click=add_to_moodboard, args=(item, active_project))

# --- TAB 2: VISUAL MOODBOARD ---
with tab2:
    st.header(f"🎨 Visual Moodboard: {active_project}")
    board_items = st.session_state.projects[active_project]["moodboard_items"]
    
    if board_items:
        cols = st.columns(3)
        for idx, board_item in enumerate(board_items):
            with cols[idx % 3]:
                with st.container(border=True):
                    img_url = board_item.get('Image Link') or board_item.get('Image') or board_item.get('Photo')
                    cat = board_item.get('Category') or 'Item'
                    
                    if not img_url:
                        st.markdown(f"<div style='background-color:#EAE6DF; padding:40px; text-align:center; border-radius:5px;'><h3>🛋️</h3><small style='color:#666;'>{cat.upper()}</small></div>", unsafe_allow_html=True)
                    else:
                        st.image(img_url, use_container_width=True)
                    
                    title_text = board_item.get('Supplier Name') or board_item.get('Brand') or board_item.get('Product Name') or "Selection"
                    st.write(f"**{title_text}**")
                    
                    email_val = extract_clean_email(board_item)
                    if email_val != 'N/A':
                        st.caption(f"✉️ {email_val}")
    else:
        st.info("Your moodboard is currently empty. Use the Smart Assistant tab to find and add items.")

# --- TAB 3: INDEPENDENT FINANCES & PDF SCANNING ---
with tab3:
    st.header(f"📊 Project Procurement Ledger: {active_project}")
    
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("➕ Add Expenses")
        
        st.markdown("**Option A: Import From Moodboard**")
        mb_options = [item.get('Supplier Name') or item.get('Brand') or item.get('Product Name') for item in board_items]
        selected_mb_item = st.selectbox("Select saved item to pull into finances", options=["-- Select Item --"] + mb_options)
        if st.button("📥 Import Item to Ledger") and selected_mb_item != "-- Select Item --":
            target_item = next(item for item in board_items if (item.get('Supplier Name') or item.get('Brand') or item.get('Product Name')) == selected_mb_item)
            new_expense = {
                "name": selected_mb_item,
                "supplier": target_item.get('Category') or "Catalog Item",
                "cost": float(target_item.get('Price') or target_item.get('Unit Cost') or 0.0),
                "qty": 1,
                "status": "Pending"
            }
            st.session_state.projects[active_project]["financial_ledger"].append(new_expense)
            st.toast(f"Imported {selected_mb_item} into finances!")
            st.rerun()
            
        st.write("---")
        
        st.markdown("**Option B: Log Custom/Ad-Hoc Purchase**")
        c_name = st.text_input("Expense Description", placeholder="e.g. Custom Black Leather Chair")
        c_supplier = st.text_input("Supplier/Store", placeholder="e.g. Weylandts")
        c_cost = st.number_input("Unit Cost (R)", min_value=0.0, step=100.0)
        c_qty = st.number_input("Quantity", min_value=1, step=1, value=1)
        c_status = st.selectbox("Status", ["Pending", "Quoted", "Paid"])
        if st.button("💾 Log Custom Expense"):
            if c_name.strip():
                new_custom = {
                    "name": c_name.strip(),
                    "supplier": c_supplier.strip() if c_supplier.strip() else "Direct Vendor",
                    "cost": float(c_cost),
                    "qty": int(c_qty),
                    "status": c_status
                }
                st.session_state.projects[active_project]["financial_ledger"].append(new_custom)
                st.toast("Logged custom expense!")
                st.rerun()
            else:
                st.error("Please enter a description.")

        st.write("---")
        
        st.markdown("**Option C: ⚡ Scan Quote/Invoice PDF**")
        uploaded_quote = st.file_uploader("Upload Supplier PDF Document", type=["pdf"], key="invoice_scanner_upload")
        
        if st.button("🔍 Run Document Scan"):
            if uploaded_quote is not None:
                with st.spinner("Extracting parameters and running deep structural scan..."):
                    parsed_result = parse_quote_pdf(uploaded_quote)
                    if parsed_result:
                        st.session_state.projects[active_project]["financial_ledger"].append(parsed_result)
                        st.toast("Processed quote parameters successfully!")
                        st.rerun()
                    else:
                        st.error("Could not pull structured text lines. The document format might be unreadable or unencrypted.")
            else:
                st.warning("Please drag and drop a PDF document into the container zone before running scan operations.")

    with col_right:
        st.subheader("📋 Budget Calculator")
        
        ledger = st.session_state.projects[active_project]["financial_ledger"]
        budget_limit = st.session_state.projects[active_project]["budget"]
        
        total_spent = sum(line['cost'] * line['qty'] for line in ledger)
        remaining_budget = budget_limit - total_spent
        
        m1, m2 = st.columns(2)
        m1.metric("Total Cost Allocation", f"R{total_spent:,.2f}")
        if remaining_budget >= 0:
            m2.metric("Remaining Balance", f"R{remaining_budget:,.2f}", delta="Within Budget")
        else:
            m2.metric("Remaining Balance", f"R{remaining_budget:,.2f}", delta="- OVER BUDGET", delta_color="inverse")
            st.error(f"🚨 Allocation warning: Over budget by R{abs(remaining_budget):,.2f}")
            
        st.write("---")
        
        if ledger:
            for idx, line in enumerate(ledger):
                with st.container(border=True):
                    grid1, grid2, grid3 = st.columns([2, 1, 1])
                    with grid1:
                        st.write(f"**{line['name']}**")
                        st.caption(f"Supplier: {line['supplier']} | Total: R{line['cost']*line['qty']:,.2f}")
                    with grid2:
                        new_cost = st.number_input(f"Cost (R)##val_{idx}", min_value=0.0, value=line['cost'], step=100.0, key=f"cost_input_{idx}")
                        new_qty = st.number_input(f"Qty##val_{idx}", min_value=1, value=line['qty'], step=1, key=f"qty_input_{idx}")
                    with grid3:
                        new_stat = st.selectbox(f"Status##val_{idx}", ["Pending", "Quoted", "Paid"], index=["Pending", "Quoted", "Paid"].index(line['status']), key=f"status_select_{idx}")
                        if st.button("🗑️ Remove", key=f"del_{idx}"):
                            st.session_state.projects[active_project]["financial_ledger"].pop(idx)
                            st.rerun()
                            
                    if new_cost != line['cost'] or new_qty != line['qty'] or new_stat != line['status']:
                        st.session_state.projects[active_project]["financial_ledger"][idx]['cost'] = new_cost
                        st.session_state.projects[active_project]["financial_ledger"][idx]['qty'] = new_qty
                        st.session_state.projects[active_project]["financial_ledger"][idx]['status'] = new_stat
                        st.rerun()
                        
            if st.button("🗑️ Clear Entire Financial Sheet"):
                st.session_state.projects[active_project]["financial_ledger"] = []
                st.rerun()
        else:
            st.info("The procurement ledger is currently clear. Use the panel on the left to pull items over from your moodboard or enter manual shop receipts.")
