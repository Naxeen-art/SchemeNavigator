import streamlit as st
import json
from database.scheme_loader import SchemeLoader
from utils.logger import logger


def render_json_upload():
    """Render JSON upload interface"""
    
    # Initialize session state for file uploader key
    if 'json_uploader_key' not in st.session_state:
        st.session_state.json_uploader_key = 0
    
    st.markdown("### 📁 JSON Upload")

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
                "📥 Upload to Database",
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
                    
                    # Process upload
                    schemes, error = SchemeLoader.load_from_json(data)

                    if error:
                        st.error(error)
                    else:
                        success, msg = SchemeLoader.save_to_database(schemes)

                        if success:
                            st.success(msg)
                            logger.info(f"JSON upload success: {msg}")
                            
                            # Clear the file uploader after successful upload
                            st.session_state.json_uploader_key += 1
                            st.rerun()
                        else:
                            st.error(msg)
                            
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