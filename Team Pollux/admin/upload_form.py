import streamlit as st
import uuid
from database.mongo_handler import db
from utils.logger import logger

def render_form_upload():
    """Render form upload interface"""
    st.markdown("### 📝 Manual Scheme Entry")
    
    with st.form("scheme_form"):
        # Basic Information
        st.markdown("#### Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            scheme_name = st.text_input(
                "Scheme Name *",
                placeholder="e.g., PM Kisan Samman Nidhi"
            )
            scheme_id = st.text_input(
                "Scheme ID (optional)",
                placeholder="Leave empty for auto-generation",
                help="If left empty, ID will be generated from scheme name"
            )
            ministry = st.text_input(
                "Ministry *",
                placeholder="e.g., Ministry of Agriculture"
            )
            
        with col2:
            category = st.selectbox(
                "Category *",
                ["Agriculture", "Education", "Health", "Housing", 
                 "Employment", "Social Welfare", "Business", "Other"]
            )
            state = st.text_input(
                "State (optional)",
                placeholder="Leave empty for central schemes"
            )
        
        # Description
        st.markdown("#### Description")
        description = st.text_area(
            "Description *",
            placeholder="Brief description of the scheme...",
            height=100
        )
        
        # Eligibility and Benefits
        st.markdown("#### Eligibility & Benefits")
        col1, col2 = st.columns(2)
        
        with col1:
            eligibility = st.text_area(
                "Eligibility Criteria",
                placeholder="Who can apply?",
                height=100
            )
            beneficiaries = st.text_input(
                "Beneficiaries",
                placeholder="e.g., Farmers, Students, Women"
            )
            
        with col2:
            benefits = st.text_area(
                "Benefits",
                placeholder="What are the benefits?",
                height=100
            )
            max_income = st.number_input(
                "Maximum Income Limit (₹)",
                min_value=0,
                value=0,
                help="0 for no income limit"
            )
        
        # Age criteria
        st.markdown("#### Age Criteria")
        col1, col2 = st.columns(2)
        with col1:
            min_age = st.number_input("Minimum Age", min_value=0, max_value=100, value=0)
        with col2:
            max_age = st.number_input("Maximum Age", min_value=0, max_value=100, value=100)
        
        # Documents Required
        st.markdown("#### Documents Required")
        documents = st.text_area(
            "Documents Required (one per line)",
            placeholder="Aadhaar Card\nIncome Certificate\nResidence Proof",
            height=100
        )
        
        # Application Process
        st.markdown("#### Application Process")
        application_process = st.text_area(
            "How to Apply",
            placeholder="Step-by-step application process...",
            height=100
        )
        
        # Additional Information
        st.markdown("#### Additional Information")
        col1, col2 = st.columns(2)
        
        with col1:
            official_url = st.text_input("Official Website URL")
            deadline = st.date_input("Application Deadline (if any)")
            
        with col2:
            contact_info = st.text_input("Contact Information")
            helpline = st.text_input("Helpline Number")
        
        # Submit button
        submitted = st.form_submit_button("✅ Add Scheme", type="primary", use_container_width=True)
        
        if submitted:
            if not all([scheme_name, ministry, description]):
                st.error("Please fill all required fields (*)")
            else:
                # Prepare scheme data
                scheme_data = {
                    'scheme_name': scheme_name,
                    'scheme_id': scheme_id or scheme_name.lower().replace(' ', '_'),
                    'ministry': ministry,
                    'category': category,
                    'description': description,
                    'eligibility': eligibility,
                    'beneficiaries': beneficiaries,
                    'benefits': benefits,
                    'documents_required': [doc.strip() for doc in documents.split('\n') if doc.strip()],
                    'application_process': application_process,
                    'official_url': official_url,
                    'contact_info': contact_info,
                    'helpline': helpline,
                    'state': state if state else 'Central',
                    'min_age': min_age,
                    'max_age': max_age,
                    'max_income': max_income if max_income > 0 else None
                }
                
                # Add to database
                db.add_scheme(scheme_data)
                st.success(f"Scheme '{scheme_name}' added successfully!")
                logger.info(f"Form upload: Added scheme {scheme_name}")
                
                # Clear form (by rerunning)
                st.rerun()