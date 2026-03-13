import streamlit as st

# MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Scheme Navigator AI",
    page_icon="🧭",
    layout="wide"
)

from datetime import datetime
from database.mongo_handler import db
from agents.matcher_agent import matcher
from utils.logger import logger


# ---------------- CSS ----------------

st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg,#667eea 0%,#764ba2 100%);
    padding:2rem;
    border-radius:10px;
    color:white;
    text-align:center;
    margin-bottom:2rem;
}

.scheme-card {
    background:black;
    border-radius:10px;
    padding:20px;
    margin:10px 0;
    box-shadow:0 2px 4px rgba(0,0,0,0.1);
    border-left:4px solid #667eea;
    transition: transform 0.2s;
}

.scheme-card:hover {
    transform: translateY(-3px);
    box-shadow:0 4px 8px rgba(0,0,0,0.15);
}

.stButton button{
    width:100%;
}

.details-container {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
    border: 1px solid #e0e0e0;
}
</style>
""", unsafe_allow_html=True)


# ---------------- LOGIN ----------------

def login_section():
    with st.sidebar:
        st.markdown("### 🔐 Login")
        email = st.text_input("Email")
        name = st.text_input("Name")

        if st.button("Login"):
            if email and name:
                user = {
                    "email": email,
                    "name": name,
                    "login_time": datetime.now()
                }
                db.add_user(user)
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Enter email and name")
    return False


# ---------------- SCHEME DETAILS ----------------

def show_scheme_details(scheme):
    """Display scheme details in a container"""
    
    with st.container():
        st.markdown('<div class="details-container">', unsafe_allow_html=True)
        
        st.markdown(f"## 📄 {scheme.get('scheme_name')}")
        
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📋 Basic Info")
            st.markdown(f"**Ministry:** {scheme.get('ministry', 'N/A')}")
            st.markdown(f"**Category:** {scheme.get('category', 'N/A')}")
            st.markdown(f"**State:** {scheme.get('state', 'Central')}")

            st.markdown("### 👥 Eligibility")
            st.markdown(scheme.get('eligibility', 'Not specified'))

            st.markdown("### 🎯 Beneficiaries")
            st.markdown(scheme.get('beneficiaries', 'All eligible citizens'))

        with col2:
            st.markdown("### 💰 Benefits")
            st.markdown(scheme.get('benefits', scheme.get('description', 'No benefits specified')))

            st.markdown("### 📄 Documents Required")
            docs = scheme.get('documents_required', [])
            if isinstance(docs, list):
                for doc in docs:
                    st.markdown(f"• {doc}")
            else:
                st.markdown(docs)

            st.markdown("### 📝 Application Process")
            st.markdown(scheme.get('application_process', 'Visit nearest office or official website'))
        
        # Contact info if available
        if scheme.get('contact_info') or scheme.get('helpline'):
            st.markdown("### 📞 Contact Information")
            if scheme.get('contact_info'):
                st.markdown(f"**Contact:** {scheme.get('contact_info')}")
            if scheme.get('helpline'):
                st.markdown(f"**Helpline:** {scheme.get('helpline')}")
        
        # Official website link
        if scheme.get('official_url'):
            st.markdown(f"**Official Website:** [Click here]({scheme.get('official_url')})")
        
        # Close button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("❌ Close Details", key="close_details"):
                st.session_state.showing_details = False
                st.session_state.selected_scheme = None
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


# ---------------- MAIN APP ----------------

def main():
    # Initialize session state variables
    if 'showing_details' not in st.session_state:
        st.session_state.showing_details = False
    if 'selected_scheme' not in st.session_state:
        st.session_state.selected_scheme = None
    if 'results' not in st.session_state:
        st.session_state.results = []

    # Check login
    if "user" not in st.session_state:
        if not login_section():
            return

    user = st.session_state.user

    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👋 Welcome {user['name']}")
        page = st.radio(
            "Menu",
            ["Search Schemes", "My Queries", "About"]
        )

        if st.button("Logout"):
            del st.session_state.user
            st.session_state.showing_details = False
            st.session_state.selected_scheme = None
            st.rerun()

    # ---------------- SEARCH PAGE ----------------
    if page == "Search Schemes":
        # Show header
        st.markdown('<div class="main-header">', unsafe_allow_html=True)
        st.title("🧭 Scheme Navigator AI")
        st.write("Find Government Schemes Easily")
        st.markdown('</div>', unsafe_allow_html=True)

        # Search input
        query = st.text_area("Describe your requirement", key="search_input")

        # Search button
        if st.button("🔍 Search"):
            if query:
                schemes = db.get_all_schemes()
                if schemes:
                    results = matcher.find_relevant_schemes(query, schemes, top_k=5)
                    st.session_state.results = results
                    st.session_state.last_query = query
                    st.session_state.showing_details = False  # Hide details when new search
                    db.save_user_query(user["email"], query, f"Found {len(results)} schemes")
                else:
                    st.warning("No schemes available")
            else:
                st.warning("Please enter a query")

        # Show search results (only if not showing details)
        if not st.session_state.showing_details and st.session_state.results:
            results = st.session_state.results
            st.write(f"### 🎯 Found {len(results)} schemes")

            for i, scheme in enumerate(results):
                scheme_id = scheme.get("scheme_id", f"scheme_{i}")
                
                # Scheme card
                st.markdown(f"""
                <div class="scheme-card">
                    <h3>{scheme.get('scheme_name')}</h3>
                    <p><strong>Ministry:</strong> {scheme.get('ministry', 'N/A')}</p>
                    <p><strong>Category:</strong> {scheme.get('category', 'N/A')}</p>
                    <p>{scheme.get('description', '')[:200]}...</p>
                    <p><small>Relevance: {scheme.get('relevance_score', 0):.1%}</small></p>
                </div>
                """, unsafe_allow_html=True)
                
                # View Details button
                if st.button("🔍 View Details", key=f"view_{scheme_id}"):
                    st.session_state.selected_scheme = scheme
                    st.session_state.showing_details = True
                    
                    # Track click
                    if st.session_state.get('last_query'):
                        db.get_collection("queries").update_one(
                            {'query': st.session_state.last_query, 'user_email': user['email']},
                            {'$push': {'schemes_clicked': scheme.get('scheme_name')}}
                        )
                    st.rerun()
                
                st.markdown("---")

        # Show scheme details if active
        if st.session_state.showing_details and st.session_state.selected_scheme:
            show_scheme_details(st.session_state.selected_scheme)

    # ---------------- QUERY HISTORY ----------------
    elif page == "My Queries":
        st.title("📜 Query History")
        queries = db.get_user_queries(user["email"])

        if queries:
            for q in queries:
                with st.container():
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; padding:15px; border-radius:10px; margin:10px 0;">
                        <p><strong>Query:</strong> {q.get('query')}</p>
                        <p><strong>Response:</strong> {q.get('response')}</p>
                        <p><small>Time: {q.get('timestamp')}</small></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if q.get('schemes_clicked'):
                        st.markdown(f"**Viewed:** {', '.join(q['schemes_clicked'])}")
        else:
            st.info("No history yet")

    # ---------------- ABOUT ----------------
    else:
        st.title("ℹ️ About Scheme Navigator AI")
        st.markdown("""
        ### 🎯 Purpose
        Scheme Navigator AI helps citizens discover government welfare schemes using artificial intelligence.
        
        ### ✨ Features
        - **AI-Powered Search**: Natural language understanding
        - **Smart Matching**: Semantic search for relevant schemes
        - **Detailed Information**: Complete scheme details at your fingertips
        - **Quick Actions**: Documents, application process, and links
        - **History Tracking**: Keep track of your searches
        
        ### 🚀 How It Works
        1. Describe your requirements in simple words
        2. Our AI matches you with relevant schemes
        3. Explore details and application procedures
        4. Access official websites and contacts
        
        ### 📊 Data Coverage
        - Central Government Schemes
        - State Government Schemes
        - Regularly updated by administrators
        """)


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    main()