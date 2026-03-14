import streamlit as st
import uuid
import json
from database.mongo_handler import db
from utils.logger import logger

def render_form_upload():
    """Render manual scheme entry form with duplicate handling"""
    st.markdown("### 📝 Manual Scheme Entry")
    
    # Display current collection stats (optional)
    try:
        collection_stats = db.get_collection_stats()
        if collection_stats:
            st.caption(f"📊 Total schemes in database: {collection_stats.get('total_schemes', 'N/A')}")
    except:
        pass
    
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
                st.error("❌ Please fill all required fields (*)")
            else:
                # Auto-generate scheme_id if not provided
                if not scheme_id:
                    scheme_id = scheme_name.lower().replace(' ', '_').replace('-', '_')
                
                # Prepare scheme data
                scheme_data = {
                    'scheme_name': scheme_name,
                    'scheme_id': scheme_id,
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
                
                # Add to database with duplicate handling
                with st.spinner("🔄 Processing..."):
                    try:
                        result = db.add_scheme(scheme_data)
                        
                        # Handle different result types
                        if isinstance(result, dict):
                            if result.get("status") == "inserted":
                                st.success(f"✅ Scheme '{scheme_name}' added successfully!")
                                st.balloons()
                                logger.info(f"Form upload: Inserted scheme {scheme_name} (ID: {scheme_id})")
                                
                            elif result.get("status") == "updated":
                                st.info(f"🔄 Scheme '{scheme_name}' was updated (already existed)")
                                logger.info(f"Form upload: Updated scheme {scheme_name} (ID: {scheme_id})")
                                
                            elif result.get("status") == "skipped":
                                st.warning(f"⚠️ Scheme '{scheme_name}' already exists and was skipped")
                                logger.info(f"Form upload: Skipped existing scheme {scheme_name} (ID: {scheme_id})")
                                
                            else:
                                st.success(f"✅ Scheme '{scheme_name}' processed successfully!")
                        else:
                            # For backward compatibility
                            st.success(f"✅ Scheme '{scheme_name}' added successfully!")
                            st.balloons()
                            
                    except Exception as e:
                        error_msg = str(e)
                        if "duplicate key" in error_msg.lower() or "11000" in error_msg:
                            st.error(f"⚠️ A scheme with ID '{scheme_id}' already exists. Please use a different ID or modify the existing scheme.")
                            st.info("💡 You can:")
                            st.info("   - Use a different Scheme ID")
                            st.info("   - Update the existing scheme instead")
                            st.info("   - Check the database for existing entries")
                            
                            # Option to view existing scheme
                            try:
                                existing = db.get_scheme_by_id(scheme_id)
                                if existing:
                                    with st.expander("View existing scheme"):
                                        st.json(existing)
                            except:
                                pass
                        else:
                            st.error(f"❌ Error adding scheme: {error_msg}")
                        logger.error(f"Form upload error: {error_msg}")
                        
                        # Clear form? No - let user decide
                        st.stop()  # Stop execution to show error
                
                # Clear form (by rerunning) only if successful
                if 'result' in locals() and isinstance(result, dict) and result.get("status") in ["inserted", "updated"]:
                    st.rerun()


def render_json_upload():
    """Render JSON file upload interface with batch duplicate handling"""
    st.markdown("### 📤 Batch Upload from JSON")
    st.info("Upload a JSON file containing one or multiple schemes. Duplicates will be handled automatically.")
    
    uploaded_file = st.file_uploader("Choose JSON file", type=['json'])
    
    if uploaded_file is not None:
        try:
            # Load JSON data
            data = json.load(uploaded_file)
            
            # Handle both single scheme and array of schemes
            if isinstance(data, dict):
                schemes = [data]
            elif isinstance(data, list):
                schemes = data
            else:
                st.error("❌ Invalid JSON format. Expected an object or array of objects.")
                return
            
            st.success(f"✅ Loaded {len(schemes)} scheme(s) from file")
            
            # Preview first few schemes
            with st.expander("Preview Data"):
                st.json(schemes[:3] if len(schemes) > 3 else schemes)
            
            # Upload options
            col1, col2 = st.columns(2)
            with col1:
                upload_mode = st.radio(
                    "Duplicate Handling Mode",
                    ["Skip duplicates", "Update existing", "Error on duplicates"],
                    index=0,
                    help="How to handle schemes with existing scheme_id"
                )
            with col2:
                generate_ids = st.checkbox(
                    "Auto-generate missing scheme_ids",
                    value=True,
                    help="Generate scheme_id from scheme_name if not provided"
                )
            
            if st.button("🚀 Upload to Database", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Track results
                results = {
                    "total": len(schemes),
                    "inserted": 0,
                    "updated": 0,
                    "skipped": 0,
                    "errors": []
                }
                
                for i, scheme in enumerate(schemes):
                    # Update progress
                    progress = (i + 1) / len(schemes)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {i+1}/{len(schemes)}: {scheme.get('scheme_name', 'Unknown')}")
                    
                    try:
                        # Ensure scheme has required fields
                        if 'scheme_name' not in scheme:
                            results["errors"].append({
                                "index": i,
                                "error": "Missing scheme_name",
                                "data": scheme
                            })
                            continue
                        
                        # Auto-generate scheme_id if needed
                        if generate_ids and ('scheme_id' not in scheme or not scheme['scheme_id']):
                            scheme['scheme_id'] = scheme['scheme_name'].lower().replace(' ', '_').replace('-', '_')
                        
                        # Add to database based on mode
                        if upload_mode == "Skip duplicates":
                            # Check existence first
                            existing = db.get_scheme_by_id(scheme.get('scheme_id'))
                            if existing:
                                results["skipped"] += 1
                                continue
                        
                        # Try to insert
                        if upload_mode == "Error on duplicates":
                            # Direct insert will raise error on duplicate
                            db.add_scheme(scheme)
                            results["inserted"] += 1
                        else:
                            # Use upsert behavior
                            result = db.add_scheme(scheme)
                            if isinstance(result, dict):
                                if result.get("status") == "inserted":
                                    results["inserted"] += 1
                                elif result.get("status") == "updated":
                                    results["updated"] += 1
                                elif result.get("status") == "skipped":
                                    results["skipped"] += 1
                            else:
                                results["inserted"] += 1
                                
                    except Exception as e:
                        if "duplicate key" in str(e).lower() and upload_mode == "Skip duplicates":
                            results["skipped"] += 1
                        else:
                            results["errors"].append({
                                "index": i,
                                "scheme_id": scheme.get('scheme_id', 'unknown'),
                                "error": str(e)
                            })
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Show summary
                st.success("✅ Upload completed!")
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Processed", results["total"])
                with col2:
                    st.metric("✅ Inserted", results["inserted"])
                with col3:
                    st.metric("🔄 Updated", results["updated"])
                with col4:
                    st.metric("⏭️ Skipped", results["skipped"])
                
                if results["errors"]:
                    st.error(f"❌ Errors: {len(results['errors'])}")
                    with st.expander("View Errors"):
                        for err in results["errors"]:
                            st.write(f"- **Scheme {err.get('index', '?')}**: {err.get('error')}")
                            if 'data' in err:
                                st.json(err['data'])
                
                logger.info(f"Batch upload completed: {results}")
                
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON file: {e}")
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")


def main():
    """Main function for form upload page"""
    st.set_page_config(
        page_title="Upload Schemes",
        page_icon="📤",
        layout="wide"
    )
    
    st.title("📤 Upload Government Schemes")
    st.markdown("Add new schemes manually or upload in bulk via JSON")
    
    # Create tabs for different upload methods
    tab1, tab2 = st.tabs(["📝 Manual Entry", "📄 JSON Upload"])
    
    with tab1:
        render_form_upload()
    
    with tab2:
        render_json_upload()


if __name__ == "__main__":
    main()