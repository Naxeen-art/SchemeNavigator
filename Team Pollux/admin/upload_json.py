import streamlit as st
import json
from database.scheme_loader import SchemeLoader
from utils.logger import logger


def render_json_upload():
    """Render JSON upload interface"""
    
    # All code MUST be indented inside the function
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
    
    # ✅ THIS LINE IS NOW PROPERLY INDENTED INSIDE THE FUNCTION
    uploaded_file = st.file_uploader(
        "Choose a JSON file",
        type=["json"],
        key="json_uploader"
    )
    
    # ✅ THIS BLOCK IS ALSO INDENTED INSIDE THE FUNCTION
    if uploaded_file is not None:
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

            col1, col2 = st.columns(2)

            # Upload button
            with col1:
                if st.button(
                    "📥 Upload to Database",
                    type="primary",
                    key="json_upload_btn"
                ):
                    schemes, error = SchemeLoader.load_from_json(data)

                    if error:
                        st.error(error)
                    else:
                        success, msg = SchemeLoader.save_to_database(schemes)

                        if success:
                            st.success(msg)
                            logger.info(f"JSON upload success: {msg}")
                        else:
                            st.error(msg)

            # Cancel button
            with col2:
                if st.button("❌ Cancel", key="json_cancel"):
                    st.rerun()

        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {str(e)}")
            logger.error(f"JSON parse error: {e}")

        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            logger.error(f"JSON upload error: {e}")