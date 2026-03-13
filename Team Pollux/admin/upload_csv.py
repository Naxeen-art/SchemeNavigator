import streamlit as st
import pandas as pd
from database.scheme_loader import SchemeLoader
from utils.logger import logger


def render_csv_upload():
    """Render CSV upload interface and handle upload logic"""

    # Initialize session state for file uploader reset key
    if 'csv_uploader_key' not in st.session_state:
        st.session_state.csv_uploader_key = 0

    st.markdown("### 📊 CSV Upload")

    st.markdown("""
    **CSV Format Requirements:**
    
    **Required columns:**
    - `scheme_name`
    - `description`
    
    **Optional columns:**
    - `scheme_id`
    - `ministry`
    - `category`
    - `eligibility`
    - `benefits`
    - `documents_required`
    
    **Sample CSV Format:**
    ```
    scheme_name,description,ministry,category
    PM Kisan Samman Nidhi,Income support for farmers,Agriculture Ministry,Agriculture
    Scholarship Scheme,Financial aid for students,Education Ministry,Education
    ```
    """)

    # File uploader with dynamic key for reset
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        key=f"csv_uploader_{st.session_state.csv_uploader_key}"
    )

    col1, col2 = st.columns([1, 1])

    # Upload and save CSV to database
    if uploaded_file is not None:
        try:
            # Preview CSV
            df = pd.read_csv(uploaded_file)
            st.markdown("### Preview")
            st.dataframe(df.head())
            st.markdown(f"**Total rows:** {len(df)}")
            st.markdown(f"**Columns:** {', '.join(df.columns)}")

            # Upload button
            with col1:
                if st.button("📥 Upload to Database", key="csv_upload_btn"):
                    # Reset file pointer
                    uploaded_file.seek(0)
                    schemes, error = SchemeLoader.load_from_csv(uploaded_file)

                    if error:
                        st.error(error)
                    else:
                        success, msg = SchemeLoader.save_to_database(schemes)
                        if success:
                            st.success(msg)
                            logger.info(f"CSV upload: {msg}")
                            # Reset file uploader
                            st.session_state.csv_uploader_key += 1
                            st.experimental_rerun()
                        else:
                            st.error(msg)

            # Cancel button
            with col2:
                if st.button("❌ Cancel", key="csv_cancel"):
                    st.session_state.csv_uploader_key += 1
                    st.experimental_rerun()

        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            logger.error(f"CSV upload error: {e}")

    # Info message when no file is selected
    if uploaded_file is None:
        st.info("👆 Please select a CSV file to upload")


# Call the function to render the upload interface
if __name__ == "__main__":
    render_csv_upload()
