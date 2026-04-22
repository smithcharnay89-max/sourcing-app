if query:
    search_terms = query.lower().split()
    results = []

    for row in data:
        # We combine the Name, Category, and Description to search everything at once
        full_text = f"{row.get('Supplier Name', '')} {row.get('Category', '')} {row.get('Contact / Specialty', '')}".lower()
        
        # This makes the search "Fuzzy" - if any of your words match any part of the row
        if any(term in full_text for term in search_terms):
            results.append(row)

    if results:
        st.success(f"I found {len(results)} potential matches for you.")
        for item in results:
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.subheader(item.get('Supplier Name', 'N/A'))
                    st.caption(f"📍 {item.get('Location', 'N/A')}")
                with c2:
                    # Explicitly pull Lead Times and Stock
                    # Make sure these column names match your Google Sheet exactly!
                    lead = item.get('Lead Times', 'Contact for details')
                    stock = item.get('Stock Levels', 'Check availability')
                    
                    st.markdown(f"⏳ **Lead Time:** {lead}")
                    st.markdown(f"📦 **Stock Status:** {stock}")
                    
                    # Specialty text
                    specialty = item.get('Contact / Specialty', 'High-end sourcing')
                    st.write(f"📝 {specialty}")
                    
                    # Email Logic
                    email = str(specialty).split('/')[-1].strip() if '/' in str(specialty) else ""
                    if "@" in email:
                        st.link_button(f"📧 Message {item.get('Supplier Name')}", f"mailto:{email}")
