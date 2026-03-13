import streamlit as st
from streamlit_option_menu import option_menu

from database.mongo_handler import db
from admin.dashboard import render_dashboard
from admin.upload_json import render_json_upload
from admin.upload_csv import render_csv_upload
from admin.upload_form import render_form_upload
from utils.logger import logger

# Page config
st.set_page_config(
    page_title="Scheme Navigator Admin",
    page_icon="⚙️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .admin-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def admin_login():
    """Admin login section"""
    with st.sidebar:
        st.image("https://www.gstatic.com/images/branding/product/2x/avatar_48dp.png", width=100)
        st.markdown("### Admin Login")
        
        email = st.text_input("Email", placeholder="Enter admin email")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        # For demo purposes - in production, use proper authentication
        admin_creds = {
            "admin@example.com": "admin123",
            "superadmin@example.com": "super123"
        }
        
        if st.button("🔐 Login", type="primary", use_container_width=True):
            if email in admin_creds and admin_creds[email] == password:
                user_info = {
                    'email': email,
                    'name': 'Administrator',
                    'is_admin': True
                }
                db.add_user(user_info)
                st.session_state.admin = user_info
                logger.info(f"Admin logged in: {email}")
                st.rerun()
            else:
                st.error("Invalid credentials")
        
        return False

def main():
    # Check authentication
    if 'admin' not in st.session_state:
        if not admin_login():
            return
    
    admin = st.session_state.admin
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### Welcome, Admin!")
        st.markdown(f"📧 {admin.get('email')}")
        st.markdown("🛡️ Role: Administrator")
        
        st.markdown("---")
        
        # Navigation
        selected = option_menu(
            menu_title="Admin Panel",
            options=["Dashboard", "Upload JSON", "Upload CSV", "Form Entry", "View Queries"],
            icons=["graph-up", "filetype-json", "filetype-csv", "ui-checks", "search"],
            menu_icon="cast",
            default_index=0,
        )
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            del st.session_state.admin
            logger.info("Admin logged out")
            st.rerun()
    
    # Main content header
    st.markdown('<div class="admin-header">', unsafe_allow_html=True)
    st.title("⚙️ Scheme Navigator Admin Panel")
    st.markdown(f"**Logged in as:** {admin.get('email')}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Render selected page
    if selected == "Dashboard":
        render_dashboard()
    
    elif selected == "Upload JSON":
        render_json_upload()
    
    elif selected == "Upload CSV":
        render_csv_upload()
    
    elif selected == "Form Entry":
        render_form_upload()
    
    elif selected == "View Queries":
        st.markdown("### 🔍 User Queries")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            search_user = st.text_input("Search by email")
        with col2:
            limit = st.number_input("Number of queries", min_value=10, max_value=1000, value=100)
        
        # Get queries
        queries = db.get_all_queries(limit=limit)
        
        if queries:
            import pandas as pd
            df = pd.DataFrame(queries)
            
            # Filter by email
            if search_user:
                df = df[df['user_email'].str.contains(search_user, case=False, na=False)]
            
            # Display
            for _, query in df.iterrows():
                with st.expander(f"📝 {query['query'][:100]}... - {query['user_email']}"):
                    st.markdown(f"**User:** {query['user_email']}")
                    st.markdown(f"**Time:** {query['timestamp']}")
                    st.markdown(f"**Query:** {query['query']}")
                    st.markdown(f"**Response:** {query['response']}")
                    
                    if query.get('schemes_clicked'):
                        st.markdown("**Schemes Viewed:**")
                        for scheme in query['schemes_clicked']:
                            st.markdown(f"- {scheme}")
            
            # Export
            if st.button("📥 Export to CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"queries_export.csv",
                    mime="text/csv"
                )
        else:
            st.info("No queries found")

if __name__ == "__main__":
    main()