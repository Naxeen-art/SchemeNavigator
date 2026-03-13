import streamlit as st

# MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Scheme Navigator Admin",
    page_icon="⚙️",
    layout="wide"
)

from streamlit_option_menu import option_menu
from database.mongo_handler import db
from admin.dashboard import render_dashboard
from admin.upload_json import render_json_upload
from admin.upload_csv import render_csv_upload
from admin.upload_form import render_form_upload
from utils.logger import logger

# ---------------- CSS ----------------

st.markdown("""
<style>
.admin-header {
    background: linear-gradient(135deg,#667eea 0%,#764ba2 100%);
    padding:1.5rem;
    border-radius:10px;
    color:white;
    text-align:center;
    margin-bottom:2rem;
}
</style>
""", unsafe_allow_html=True)


# ---------------- ADMIN LOGIN ----------------

def admin_login():

    with st.sidebar:

        st.markdown("### 🔐 Admin Login")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        admin_creds = {
            "admin@example.com": "admin123",
            "superadmin@example.com": "super123"
        }

        if st.button("Login"):

            if email in admin_creds and admin_creds[email] == password:

                admin = {
                    "email": email,
                    "name": "Administrator",
                    "is_admin": True
                }

                db.add_user(admin)

                st.session_state.admin = admin
                logger.info(f"Admin logged in: {email}")

                st.rerun()

            else:
                st.error("Invalid credentials")

    return False


# ---------------- MAIN APP ----------------

def main():

    if "admin" not in st.session_state:

        if not admin_login():
            return

    admin = st.session_state.admin

    # Sidebar

    with st.sidebar:

        st.markdown("### ⚙️ Admin Panel")
        st.markdown(f"📧 {admin['email']}")

        selected = option_menu(
            menu_title="Menu",
            options=[
                "Dashboard",
                "Upload JSON",
                "Upload CSV",
                "Form Entry",
                "View Queries"
            ],
            icons=[
                "graph-up",
                "filetype-json",
                "filetype-csv",
                "ui-checks",
                "search"
            ],
            default_index=0
        )

        if st.button("Logout"):

            del st.session_state.admin
            logger.info("Admin logged out")

            st.rerun()

    # Header

    st.markdown('<div class="admin-header">', unsafe_allow_html=True)

    st.title("⚙️ Scheme Navigator Admin Panel")

    st.markdown(f"Logged in as **{admin['email']}**")

    st.markdown('</div>', unsafe_allow_html=True)

    # Pages

    if selected == "Dashboard":

        render_dashboard()

    elif selected == "Upload JSON":

        render_json_upload()

    elif selected == "Upload CSV":

        render_csv_upload()

    elif selected == "Form Entry":

        render_form_upload()

    elif selected == "View Queries":

        st.title("User Queries")

        queries = db.get_all_queries()

        if queries:

            import pandas as pd

            df = pd.DataFrame(queries)

            for _, q in df.iterrows():

                with st.expander(q["query"][:80]):

                    st.write("User:", q["user_email"])
                    st.write("Query:", q["query"])
                    st.write("Response:", q["response"])
                    st.write("Time:", q["timestamp"])

        else:

            st.info("No queries found")


# ---------------- RUN ----------------

if __name__ == "__main__":
    main()
