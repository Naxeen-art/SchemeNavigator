import streamlit as st
from datetime import datetime
import pandas as pd
from streamlit_option_menu import option_menu

from database.mongo_handler import db
from agents.matcher_agent import matcher
from utils.logger import logger

# Page config
st.set_page_config(
    page_title="Scheme Navigator AI",
    page_icon="🧭",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .scheme-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.3s;
        cursor: pointer;
    }
    .scheme-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .quick-actions {
        display: flex;
        gap: 10px;
        margin-top: 15px;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 8px;
    }
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

def login_section():
    """Simple login section (for demo)"""
    with st.sidebar:
        st.image("https://www.gstatic.com/images/branding/product/2x/avatar_48dp.png", width=100)
        st.markdown("### User Login")
        
        email = st.text_input("Email", placeholder="Enter your email")
        name = st.text_input("Name", placeholder="Enter your name")
        
        if st.button("🔐 Login", type="primary", use_container_width=True):
            if email and name:
                user_info = {
                    'email': email,
                    'name': name,
                    'is_admin': False
                }
                db.add_user(user_info)
                st.session_state.user = user_info
                st.rerun()
            else:
                st.error("Please enter both email and name")
        
        return False

def show_scheme_details(scheme):
    """Show expanded scheme details"""
    with st.expander(f"📋 {scheme.get('scheme_name')} - Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Scheme Details**")
            st.markdown(f"• **Ministry:** {scheme.get('ministry', 'N/A')}")
            st.markdown(f"• **Category:** {scheme.get('category', 'N/A')}")
            st.markdown(f"• **Beneficiaries:** {scheme.get('beneficiaries', 'N/A')}")
            st.markdown(f"• **Eligibility:** {scheme.get('eligibility', 'N/A')}")
        
        with col2:
            st.markdown("**Quick Actions**")
            action = st.radio(
                "Select action:",
                ["📄 Documents", "📝 How to Apply", "💰 Benefits", "🔗 Official Link"],
                key=f"action_{scheme.get('scheme_id')}"
            )
            
            if action == "📄 Documents":
                docs = scheme.get('documents_required', [])
                if isinstance(docs, list):
                    for doc in docs:
                        st.markdown(f"• {doc}")
                else:
                    st.markdown(docs)
            
            elif action == "📝 How to Apply":
                st.markdown(scheme.get('application_process', 'Contact concerned department'))
            
            elif action == "💰 Benefits":
                st.markdown(scheme.get('benefits', scheme.get('description', 'N/A')))
            
            elif action == "🔗 Official Link":
                url = scheme.get('official_url', '#')
                st.markdown(f"[Visit Official Website]({url})")
        
        st.markdown("---")
        st.markdown(f"**Full Description:** {scheme.get('description', 'No description')}")

def main():
    # Check authentication
    if 'user' not in st.session_state:
        if not login_section():
            return
    
    user = st.session_state.user
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### Welcome, {user.get('name', 'User')}!")
        st.markdown(f"📧 {user.get('email')}")
        
        st.markdown("---")
        
        # Navigation
        selected = option_menu(
            menu_title="Navigation",
            options=["Scheme Navigator", "My Queries", "About"],
            icons=["search", "clock-history", "info-circle"],
            menu_icon="cast",
            default_index=0,
        )
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            del st.session_state.user
            st.rerun()
    
    # Main content
    if selected == "Scheme Navigator":
        st.markdown('<div class="main-header">', unsafe_allow_html=True)
        st.title("🧭 Scheme Navigator AI")
        st.markdown("Find the perfect government scheme for your needs")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Search section
        col1, col2 = st.columns([4, 1])
        with col1:
            user_query = st.text_area(
                "Describe your requirements:",
                placeholder="E.g., I'm a farmer from Maharashtra looking for crop insurance...",
                height=100
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            search_button = st.button("🔍 Search Schemes", type="primary", use_container_width=True)
        
        # Search and display results
        if search_button and user_query:
            with st.spinner("🔎 Searching for relevant schemes..."):
                # Get all schemes
                schemes = db.get_all_schemes()
                
                if schemes:
                    # Find relevant schemes
                    relevant_schemes = matcher.find_relevant_schemes(user_query, schemes)
                    
                    # Save query to database
                    db.save_user_query(
                        user['email'],
                        user_query,
                        f"Found {len(relevant_schemes)} schemes"
                    )
                    
                    # Display results
                    st.markdown(f"### 🎯 Found {len(relevant_schemes)} relevant schemes")
                    
                    for scheme in relevant_schemes:
                        # Scheme card
                        st.markdown(f"""
                        <div class="scheme-card">
                            <h3>{scheme.get('scheme_name')}</h3>
                            <p><strong>Ministry:</strong> {scheme.get('ministry', 'N/A')}</p>
                            <p><strong>Category:</strong> {scheme.get('category', 'N/A')}</p>
                            <p>{scheme.get('description', '')[:200]}...</p>
                            <p><small>Relevance: {scheme.get('relevance_score', 0):.2%}</small></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Details button
                        if st.button(f"📋 View Details", key=f"view_{scheme.get('scheme_id')}"):
                            show_scheme_details(scheme)
                            
                            # Track click
                            db.get_collection("queries").update_one(
                                {'query': user_query, 'user_email': user['email']},
                                {'$push': {'schemes_clicked': scheme.get('scheme_name')}}
                            )
                else:
                    st.warning("No schemes found in database. Please contact admin.")
    
    elif selected == "My Queries":
        st.markdown("## 📜 Your Query History")
        
        queries = db.get_user_queries(user['email'])
        
        if queries:
            for query in queries:
                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #e0e0e0; border-radius: 10px; padding: 15px; margin: 10px 0; background: #f8f9fa;">
                        <p><strong>Query:</strong> {query.get('query')}</p>
                        <p><strong>Response:</strong> {query.get('response')}</p>
                        <p><small>Time: {query.get('timestamp').strftime('%Y-%m-%d %H:%M:%S')}</small></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if query.get('schemes_clicked'):
                        st.markdown("**Viewed schemes:** " + ", ".join(query['schemes_clicked']))
        else:
            st.info("No query history found")
    
    else:
        st.markdown("## ℹ️ About Scheme Navigator AI")
        st.markdown("""
        **Scheme Navigator AI** is an intelligent assistant that helps citizens find relevant government schemes.
        
        ### Features:
        - 🔍 Smart search using AI
        - 📊 Real-time scheme matching
        - 📝 Detailed scheme information
        - 🚀 Quick actions for documents and application
        - 📜 Query history tracking
        
        ### How it works:
        1. Describe your requirements
        2. AI matches with available schemes
        3. Explore detailed information
        4. Access application procedures
        
        ### Contact:
        For support or feedback, please contact the administrator.
        """)

if __name__ == "__main__":
    main()