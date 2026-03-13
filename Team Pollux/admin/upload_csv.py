


# 2️⃣ `admin/upload_csv.py`

import streamlit as st
import pandas as pd
from database.scheme_loader import SchemeLoader
from utils.logger import logger


def render_csv_upload():
    """Render CSV upload interface"""

    st.markdown("### 📊 CSV Upload")

    st.markdown(
        """
**CSV Format Requirements:**

Required columns:
- `scheme_name`
- `description`

Optional columns:
- `scheme_id`
- `ministry`
- `category`
- `eligibility`
- `benefits`
- `documents_required`

**Sample CSV Format:**

scheme_name,description,ministry,category  
PM Kisan Samman Nidhi,Income support for farmers,Agriculture Ministry,Agriculture  
Scholarship Scheme,Financial aid for students,Education Ministry,Education
"""
    )

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        key="csv_uploader",
    )

    if uploaded_file is not None:
        try:
            # Load CSV
            df = pd.read_csv(uploaded_file)

            st.markdown("### Preview")
            st.dataframe(df.head())

            st.markdown(f"**Total rows:** {len(df)}")
            st.markdown(f"**Columns:** {', '.join(df.columns)}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "📥 Upload to Database",
                    type="primary",
                    key="csv_upload_btn",
                ):
                    uploaded_file.seek(0)

                    schemes, error = SchemeLoader.load_from_csv(uploaded_file)

                    if error:
                        st.error(error)
                    else:
                        success, msg = SchemeLoader.save_to_database(schemes)

                        if success:
                            st.success(msg)
                            logger.info(f"CSV upload: {msg}")
                        else:
                            st.error(msg)

            with col2:
                if st.button("❌ Cancel", key="csv_cancel"):
                    st.rerun()

        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            logger.error(f"CSV upload error: {e}")
