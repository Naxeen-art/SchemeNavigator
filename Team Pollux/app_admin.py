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

# ---------------- MODERN ADMIN UI CSS ----------------

st.markdown("""
<style>

/* Main Background */
.stApp {
    background: linear-gradient(120deg,#1f1c2c,#928dab);
    color:white;
}

/* Admin Header */
.admin-header {
    background: linear-gradient(135deg,#ff512f,#dd2476);
    padding:2rem;
    border-radius:16px;
    color:white;
    text-align:center;
    margin-bottom:30px;
    box-shadow:0 10px 25px rgba(0,0,0,0.35);
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#141E30,#243B55);
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg,#36d1dc,#5b86e5);
    border:none;
    color:white;
    padding:10px;
    border-radius:10px;
    font-weight:600;
    transition:0.3s;
}

.stButton button:hover {
    transform:scale(1.05);
}

/* Cards */
.admin-card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    border-radius:16px;
    padding:20px;
    margin-bottom:15px;
    border:1px solid rgba(255,255,255,0.1);
    transition:0.3s;
}

.admin-card:hover {
    transform:translateY(-5px);
    box-shadow:0 8px 20px rgba(0,0,0,0.4);
}

/* Expander */
.streamlit-expanderHeader {
    font-weight:600;
}

/* Input fields */
input, textarea {
    border-radius:10px !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width:8px;
}

::-webkit-scrollbar-thumb {
    background:#5b86e5;
    border-radius:10px;
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
