import streamlit as st
import pandas as pd
import numpy as np
from database.mongo_handler import db
from utils.logger import logger


class SchemeLoader:
    """Helper class to handle scheme loading from CSV"""

    @staticmethod
    def load_from_csv(file):
        """Load schemes from CSV file"""
        try:
            df = pd.read_csv(file)

            # Required columns
            required_cols = ["scheme_name", "description"]
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                return None, f"Missing required columns: {', '.join(missing_cols)}"

            # Replace NaN
            df = df.replace({np.nan: None})

            schemes = df.to_dict("records")

            for scheme in schemes:

                # documents_required -> list
                if scheme.get("documents_required"):
                    if isinstance(scheme["documents_required"], str):
                        scheme["documents_required"] = [
                            d.strip() for d in scheme["documents_required"].split(",")
                        ]
                else:
                    scheme["documents_required"] = []

                # numeric fields
                for field in ["min_age", "max_age", "max_income"]:
                    if scheme.get(field):
                        try:
                            scheme[field] = int(float(scheme[field]))
                        except:
                            scheme[field] = None

                # auto scheme_id
                if not scheme.get("scheme_id") and scheme.get("scheme_name"):
                    scheme["scheme_id"] = (
                        scheme["scheme_name"]
                        .lower()
                        .replace(" ", "_")
                        .replace("-", "_")
                    )

            return schemes, None

        except Exception as e:
            return None, f"Error loading CSV: {str(e)}"

    @staticmethod
    def save_to_database(schemes):
        """Save schemes to database"""
        try:
            result = db.add_schemes_bulk(schemes)

            if isinstance(result, dict):

                total = result.get("total", len(schemes))
                inserted = result.get("inserted", 0)
                updated = result.get("updated", 0)
                skipped = result.get("skipped", 0)
                errors = result.get("errors", [])

                msg = f"""
✅ Upload Complete

Total: {total}
Inserted: {inserted}
Updated: {updated}
Skipped: {skipped}
Errors: {len(errors)}
"""

                return True, msg

            else:
                return True, f"Uploaded {len(schemes)} schemes"

        except Exception as e:
            logger.error(e)
            return False, f"Database Error: {str(e)}"


def render_csv_upload():
    """CSV Upload UI"""

    if "csv_uploader_key" not in st.session_state:
        st.session_state.csv_uploader_key = 0

    if "upload_status" not in st.session_state:
        st.session_state.upload_status = None

    st.title("📊 Scheme CSV Upload")

    tab1, tab2 = st.tabs(["Upload", "CSV Guide"])

    # ---------------- FORMAT GUIDE ----------------
    with tab2:

        st.markdown("### CSV Format")

        st.markdown("""
Required columns:

- scheme_name  
- description  

Optional columns:

- scheme_id
- ministry
- category
- state
- eligibility
- beneficiaries
- benefits
- documents_required
- application_process
- official_url
- contact_info
- helpline
- min_age
- max_age
- max_income
""")

        template_df = pd.DataFrame({
            "scheme_name": ["PM Kisan Samman Nidhi"],
            "scheme_id": ["pm_kisan_001"],
            "description": ["Income support for farmers"],
            "ministry": ["Ministry of Agriculture"],
            "category": ["Agriculture"],
            "state": ["Central"],
            "eligibility": ["Small farmers"],
            "beneficiaries": ["Farmers"],
            "benefits": ["₹6000 per year"],
            "documents_required": ["Aadhaar Card,Land Records"],
            "application_process": ["Apply online"],
            "official_url": ["https://pmkisan.gov.in"],
            "contact_info": ["Agriculture Department"],
            "helpline": ["1800-123-4567"],
            "min_age": [18],
            "max_age": [75],
            "max_income": [200000]
        })

        csv_template = template_df.to_csv(index=False)

        st.download_button(
            "Download CSV Template",
            data=csv_template,
            file_name="schemes_template.csv",
            mime="text/csv",
        )

    # ---------------- UPLOAD TAB ----------------
    with tab1:

        uploaded_file = st.file_uploader(
            "Upload CSV File",
            type=["csv"],
            key=f"csv_uploader_{st.session_state.csv_uploader_key}",
        )

        if uploaded_file:

            df = pd.read_csv(uploaded_file)

            st.subheader("Preview")
            st.dataframe(df.head(10))

            col1, col2 = st.columns(2)

            with col1:

                if st.button("Upload to Database"):

                    uploaded_file.seek(0)

                    schemes, error = SchemeLoader.load_from_csv(uploaded_file)

                    if error:
                        st.error(error)

                    else:

                        success, msg = SchemeLoader.save_to_database(schemes)

                        if success:
                            st.success(msg)

                            st.session_state.csv_uploader_key += 1
                            st.rerun()

                        else:
                            st.error(msg)

            with col2:

                if st.button("Cancel"):
                    st.session_state.csv_uploader_key += 1
                    st.rerun()

        else:
            st.info("Please upload a CSV file")


# Run app
if __name__ == "__main__":
    render_csv_upload()
