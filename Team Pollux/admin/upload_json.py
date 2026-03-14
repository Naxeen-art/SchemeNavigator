import streamlit as st
import json
from database.mongo_handler import db
from utils.logger import logger
from datetime import datetime


def render_json_upload():
    """Render JSON upload interface with upsert (update or insert) functionality"""
    
    # Initialize session state for file uploader key
    if 'json_uploader_key' not in st.session_state:
        st.session_state.json_uploader_key = 0
    
    st.markdown("### 📁 JSON Upload (Upsert Mode)")

    st.info("""
    **🔄 Upsert Mode Active**
    - If scheme exists → It will be **UPDATED** with new data
    - If scheme is new → It will be **INSERTED** into database
    - No data loss, no duplicate errors
    """)

    st.markdown("""
    **JSON Format Example:**
    
    ```json
    [
        {
            "scheme_id": "PMKISAN001",
            "scheme_name": "PM Kisan Samman Nidhi",
            "ministry": "Ministry of Agriculture",
            "category": "Agriculture",
            "description": "Income support scheme for farmers",
            "eligibility": "Small and marginal farmers",
            "beneficiaries": "Farmers",
            "benefits": "₹6000 per year",
            "documents_required": ["Aadhaar", "Land records"],
            "application_process": "Online through portal"
        }
    ]
    """)
    
    # Use dynamic key to allow resetting
    uploaded_file = st.file_uploader(
        "Choose a JSON file",
        type=["json"],
        key=f"json_uploader_{st.session_state.json_uploader_key}"
    )
    
    # Create columns for buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if uploaded_file is not None:
            if st.button(
                "📥 Upload (Upsert)",
                type="primary",
                key="json_upload_btn"
            ):
                try:
                    # Read and parse JSON
                    content = uploaded_file.read().decode("utf-8")
                    data = json.loads(content)
                    
                    # Show preview
                    st.markdown("### 🔍 Preview")

                    if isinstance(data, list):
                        if len(data) > 2:
                            preview_data = data[:2]
                            st.json(preview_data)
                            st.info(f"Showing first 2 of {len(data)} records")
                        else:
                            st.json(data)
                    else:
                        st.json(data)
                        data = [data]  # Convert single scheme to list
                    
                    # Process upload with upsert
                    success_count, update_count, errors = upsert_schemes_to_database(data)

                    if success_count > 0 or update_count > 0:
                        st.success(f"✅ Successfully processed {success_count + update_count} schemes")
                        if success_count > 0:
                            st.info(f"📝 New schemes added: {success_count}")
                        if update_count > 0:
                            st.info(f"🔄 Existing schemes updated: {update_count}")
                        if errors:
                            st.warning(f"⚠️ {len(errors)} errors occurred")
                            with st.expander("View Errors"):
                                for error in errors[:5]:
                                    st.error(error)
                        
                        logger.info(f"JSON upload: {success_count} added, {update_count} updated")
                        
                        # Clear the file uploader after successful upload
                        st.session_state.json_uploader_key += 1
                        st.rerun()
                    else:
                        st.error("No schemes were processed")
                        if errors:
                            with st.expander("View Errors"):
                                for error in errors:
                                    st.error(error)
                            
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON format: {str(e)}")
                    logger.error(f"JSON parse error: {e}")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    logger.error(f"JSON upload error: {e}")
    
    with col2:
        if uploaded_file is not None:
            if st.button("❌ Cancel", key="json_cancel"):
                # Increment the key to reset the file uploader
                st.session_state.json_uploader_key += 1
                st.rerun()
    
    # Show message when no file is selected
    if uploaded_file is None:
        st.info("👆 Please select a JSON file to upload")


def upsert_schemes_to_database(schemes_data):
    """
    Upsert schemes to database (update if exists, insert if new)
    
    Returns:
        tuple: (inserted_count, updated_count, errors)
    """
    collection = db.get_collection("schemes")
    inserted_count = 0
    updated_count = 0
    errors = []
    
    for idx, scheme in enumerate(schemes_data):
        try:
            # Generate scheme_id if missing
            if 'scheme_id' not in scheme or not scheme['scheme_id']:
                if scheme.get('scheme_name'):
                    scheme['scheme_id'] = scheme['scheme_name'].lower().replace(' ', '_')
                else:
                    errors.append(f"Row {idx + 1}: Missing both scheme_id and scheme_name")
                    continue
            
            # Add/update timestamps
            scheme['updated_at'] = datetime.now()
            
            # Check if scheme exists
            existing = collection.find_one({'scheme_id': scheme['scheme_id']})
            
            if existing:
                # Update existing scheme
                result = collection.update_one(
                    {'scheme_id': scheme['scheme_id']},
                    {'$set': scheme}
                )
                if result.modified_count > 0:
                    updated_count += 1
                    logger.info(f"Updated scheme: {scheme['scheme_id']}")
            else:
                # Insert new scheme
                scheme['created_at'] = datetime.now()
                collection.insert_one(scheme)
                inserted_count += 1
                logger.info(f"Inserted new scheme: {scheme['scheme_id']}")
                
        except Exception as e:
            error_msg = f"Error processing scheme {scheme.get('scheme_id', 'unknown')}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
    
    return inserted_count, updated_count, errors