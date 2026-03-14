# app_user.py

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
from utils.translator import Translator

# Initialize translator
translator = Translator()

# ---------------- CSS ----------------

# ---------------- MODERN UI CSS ----------------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(120deg,#0f2027,#203a43,#2c5364);
    color: white;
}

/* Header */
.main-header{
    background: linear-gradient(135deg,#6a11cb 0%,#2575fc 100%);
    padding:2.5rem;
    border-radius:15px;
    text-align:center;
    box-shadow:0 8px 20px rgba(0,0,0,0.3);
    margin-bottom:30px;
}

/* Scheme Card */
.scheme-card{
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(12px);
    border-radius:16px;
    padding:25px;
    margin-top:15px;
    border:1px solid rgba(255,255,255,0.1);
    transition: all 0.3s ease;
}

.scheme-card:hover{
    transform: translateY(-6px);
    box-shadow:0 10px 25px rgba(0,0,0,0.4);
}

/* Details container */
.details-container{
    background: rgba(255,255,255,0.95);
    color:black;
    border-radius:18px;
    padding:30px;
    margin-top:20px;
    box-shadow:0 10px 25px rgba(0,0,0,0.2);
}

/* Buttons */
.stButton button{
    background: linear-gradient(135deg,#ff9966,#ff5e62);
    color:white;
    border:none;
    padding:10px;
    border-radius:10px;
    font-weight:bold;
    transition:0.3s;
}

.stButton button:hover{
    transform:scale(1.05);
    background: linear-gradient(135deg,#ff5e62,#ff9966);
}

/* Sidebar */
[data-testid="stSidebar"]{
    background: linear-gradient(180deg,#141e30,#243b55);
}

/* Textarea */
textarea{
    border-radius:12px !important;
    border:1px solid rgba(255,255,255,0.2) !important;
}

/* Scrollbar */
::-webkit-scrollbar{
    width:8px;
}

::-webkit-scrollbar-thumb{
    background:#6a11cb;
    border-radius:10px;
}

/* Language selector */
.language-selector{
    position:fixed;
    top:10px;
    right:10px;
}

/* Tamil Font Support */
.ta-text{
    font-family: 'Latha','Noto Sans Tamil','Arial',sans-serif;
}

</style>
""", unsafe_allow_html=True)



# ---------------- LANGUAGE SELECTOR ----------------

def language_selector():
    """Language selector component"""
    with st.sidebar:
        st.markdown("### 🌐 Language / மொழி")
        lang = st.radio(
            "Select Language",
            ["English", "தமிழ்"],
            key="language"
        )
        return "ta" if lang == "தமிழ்" else "en"


# ---------------- LOGIN ----------------

def login_section(lang='en'):
    """Login section with language support"""
    with st.sidebar:
        if lang == 'en':
            st.markdown("### 🔐 Login")
            email = st.text_input("Email")
            name = st.text_input("Name")
            login_btn = "Login"
        else:
            st.markdown("### 🔐 உள்நுழைக")
            email = st.text_input("மின்னஞ்சல்")
            name = st.text_input("பெயர்")
            login_btn = "உள்நுழைக"

        if st.button(login_btn):
            if email and name:
                user = {
                    "email": email,
                    "name": name,
                    "login_time": datetime.now(),
                    "language": lang
                }
                db.add_user(user)
                st.session_state.user = user
                st.rerun()
            else:
                if lang == 'en':
                    st.error("Enter email and name")
                else:
                    st.error("மின்னஞ்சல் மற்றும் பெயரை உள்ளிடவும்")
    return False


# ---------------- SCHEME DETAILS ----------------

def show_scheme_details(scheme, lang='en'):
    """Display scheme details in container with language support"""
    
    with st.container():
        st.markdown('<div class="details-container">', unsafe_allow_html=True)
        
        if lang == 'en':
            st.markdown(f"## 📄 {scheme.get('scheme_name')}")
        else:
            st.markdown(f"## 📄 {scheme.get('scheme_name', '')}")
        
        col1, col2 = st.columns(2)

        with col1:
            if lang == 'en':
                st.markdown("### 📋 Basic Info")
                st.markdown(f"**Ministry:** {scheme.get('ministry', 'N/A')}")
                st.markdown(f"**Category:** {scheme.get('category', 'N/A')}")
                st.markdown(f"**State:** {scheme.get('state', 'Central')}")

                st.markdown("### 👥 Eligibility")
                st.markdown(scheme.get('eligibility', 'Not specified'))

                st.markdown("### 🎯 Beneficiaries")
                st.markdown(scheme.get('beneficiaries', 'All eligible citizens'))
            else:
                st.markdown("### 📋 அடிப்படை தகவல்")
                st.markdown(f"**அமைச்சகம்:** {scheme.get('ministry', 'N/A')}")
                st.markdown(f"**பிரிவு:** {scheme.get('category', 'N/A')}")
                st.markdown(f"**மாநிலம்:** {scheme.get('state', 'மத்திய')}")

                st.markdown("### 👥 தகுதி")
                st.markdown(scheme.get('eligibility', 'குறிப்பிடப்படவில்லை'))

                st.markdown("### 🎯 பயனாளிகள்")
                st.markdown(scheme.get('beneficiaries', 'அனைத்து தகுதியான குடிமக்கள்'))

        with col2:
            if lang == 'en':
                st.markdown("### 💰 Benefits")
                st.markdown(scheme.get('benefits', scheme.get('description', 'No benefits specified')))

                st.markdown("### 📄 Documents Required")
            else:
                st.markdown("### 💰 நன்மைகள்")
                st.markdown(scheme.get('benefits', scheme.get('description', 'நன்மைகள் குறிப்பிடப்படவில்லை')))

                st.markdown("### 📄 தேவையான ஆவணங்கள்")
            
            docs = scheme.get('documents_required', [])
            if isinstance(docs, list):
                for doc in docs:
                    st.markdown(f"• {doc}")
            else:
                st.markdown(docs)

            if lang == 'en':
                st.markdown("### 📝 Application Process")
                st.markdown(scheme.get('application_process', 'Visit nearest office or official website'))
            else:
                st.markdown("### 📝 விண்ணப்பிக்கும் முறை")
                st.markdown(scheme.get('application_process', 'அருகிலுள்ள அலுவலகம் அல்லது அதிகாரப்பூர்வ இணையதளத்தை பார்வையிடவும்'))
        
        # Contact info if available
        if scheme.get('contact_info') or scheme.get('helpline'):
            if lang == 'en':
                st.markdown("### 📞 Contact Information")
            else:
                st.markdown("### 📞 தொடர்பு தகவல்")
            
            if scheme.get('contact_info'):
                st.markdown(f"**Contact:** {scheme.get('contact_info')}")
            if scheme.get('helpline'):
                st.markdown(f"**Helpline:** {scheme.get('helpline')}")
        
        # Official website link
        if scheme.get('official_url'):
            if lang == 'en':
                st.markdown(f"**Official Website:** [Click here]({scheme.get('official_url')})")
            else:
                st.markdown(f"**அதிகாரப்பூர்வ இணையதளம்:** [இங்கே கிளிக் செய்யவும்]({scheme.get('official_url')})")
        
        # Close button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if lang == 'en':
                btn_text = "❌ Close Details"
            else:
                btn_text = "❌ மூடுக"
            
            if st.button(btn_text, key="close_details"):
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

    # Language selector
    lang = language_selector()

    # Check login
    if "user" not in st.session_state:
        if not login_section(lang):
            return

    user = st.session_state.user

    # Sidebar
    with st.sidebar:
        if lang == 'en':
            st.markdown(f"### 👋 Welcome {user['name']}")
            menu_options = ["Search Schemes", "My Queries", "About"]
            logout_btn = "Logout"
        else:
            st.markdown(f"### 👋 வணக்கம் {user['name']}")
            menu_options = ["திட்டங்களை தேடுக", "என் கேள்விகள்", "எங்களை பற்றி"]
            logout_btn = "வெளியேறு"
        
        page = st.radio(
            "Menu" if lang == 'en' else "மெனு",
            menu_options
        )

        if st.button(logout_btn):
            del st.session_state.user
            st.session_state.showing_details = False
            st.session_state.selected_scheme = None
            st.rerun()

    # ---------------- SEARCH PAGE ----------------
    if page == "Search Schemes" or page == "திட்டங்களை தேடுக":
        # Show header
        st.markdown('<div class="main-header">', unsafe_allow_html=True)
        if lang == 'en':
            st.title("🧭 Scheme Navigator AI")
            st.write("Find Government Schemes Easily")
        else:
            st.title("🧭 திட்ட வழிகாட்டி AI")
            st.write("அரசு திட்டங்களை எளிதாக கண்டறியவும்")
        st.markdown('</div>', unsafe_allow_html=True)

        # Search input
        if lang == 'en':
            query = st.text_area("Describe your requirement", key="search_input")
            search_btn = "🔍 Search"
        else:
            query = st.text_area("உங்கள் தேவையை விவரிக்கவும்", key="search_input")
            search_btn = "🔍 தேடுக"

        # Search button
        if st.button(search_btn):
            if query:
                schemes = db.get_all_schemes()
                if schemes:
                    results = matcher.find_relevant_schemes(query, schemes, top_k=5)
                    st.session_state.results = results
                    st.session_state.last_query = query
                    st.session_state.showing_details = False
                    db.save_user_query(user["email"], query, f"Found {len(results)} schemes")
                else:
                    if lang == 'en':
                        st.warning("No schemes available")
                    else:
                        st.warning("திட்டங்கள் எதுவும் இல்லை")
            else:
                if lang == 'en':
                    st.warning("Please enter a query")
                else:
                    st.warning("தயவுசெய்து ஒரு கேள்வியை உள்ளிடவும்")

        # Show search results
        if not st.session_state.showing_details and st.session_state.results:
            results = st.session_state.results
            if lang == 'en':
                st.write(f"### 🎯 Found {len(results)} schemes")
            else:
                st.write(f"### 🎯 {len(results)} திட்டங்கள் கண்டறியப்பட்டன")

            for i, scheme in enumerate(results):
                scheme_id = scheme.get("scheme_id", f"scheme_{i}")
                
                # Scheme card
                st.markdown(f"""
                <div class="scheme-card">
                    <h3>{scheme.get('scheme_name')}</h3>
                    <p><strong>{'Ministry' if lang == 'en' else 'அமைச்சகம்'}:</strong> {scheme.get('ministry', 'N/A')}</p>
                    <p><strong>{'Category' if lang == 'en' else 'பிரிவு'}:</strong> {scheme.get('category', 'N/A')}</p>
                    <p>{scheme.get('description', '')[:200]}...</p>
                    <p><small>{'Relevance' if lang == 'en' else 'பொருத்தம்'}: {scheme.get('relevance_score', 0):.1%}</small></p>
                    <p><small>{'Source' if lang == 'en' else 'மூலம்'}: {scheme.get('source', 'Database')}</small></p>
                </div>
                """, unsafe_allow_html=True)
                
                # View Details button
                if lang == 'en':
                    btn_text = "🔍 View Details"
                else:
                    btn_text = "🔍 விவரங்களை காண"
                
                if st.button(btn_text, key=f"view_{scheme_id}"):
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
            show_scheme_details(st.session_state.selected_scheme, lang)

    # ---------------- QUERY HISTORY ----------------
    elif page == "My Queries" or page == "என் கேள்விகள்":
        if lang == 'en':
            st.title("📜 Query History")
        else:
            st.title("📜 கேள்வி வரலாறு")
        
        queries = db.get_user_queries(user["email"])

        if queries:
            for q in queries:
                with st.container():
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; padding:15px; border-radius:10px; margin:10px 0;">
                        <p><strong>{'Query' if lang == 'en' else 'கேள்வி'}:</strong> {q.get('query')}</p>
                        <p><strong>{'Response' if lang == 'en' else 'பதில்'}:</strong> {q.get('response')}</p>
                        <p><small>{'Time' if lang == 'en' else 'நேரம்'}: {q.get('timestamp')}</small></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if q.get('schemes_clicked'):
                        if lang == 'en':
                            st.markdown(f"**Viewed:** {', '.join(q['schemes_clicked'])}")
                        else:
                            st.markdown(f"**பார்த்தவை:** {', '.join(q['schemes_clicked'])}")
        else:
            if lang == 'en':
                st.info("No history yet")
            else:
                st.info("இதுவரை வரலாறு இல்லை")

    # ---------------- ABOUT ----------------
    else:
        if lang == 'en':
            st.title("ℹ️ About Scheme Navigator AI")
            st.markdown("""
            ### 🎯 Purpose
            Scheme Navigator AI helps citizens discover government welfare schemes using artificial intelligence.
            
            ### ✨ Features
            - **AI-Powered Search**: Natural language understanding
            - **Smart Matching**: Semantic search for relevant schemes
            - **Web Search**: Fetches latest schemes from government portals
            - **Dual Language**: English and Tamil support
            - **Detailed Information**: Complete scheme details at your fingertips
            - **History Tracking**: Keep track of your searches
            
            ### 🚀 How It Works
            1. Describe your requirements in simple words
            2. Our AI matches you with relevant schemes
            3. Explore details and application procedures
            4. Access official websites and contacts
            
            ### 📊 Data Coverage
            - Central Government Schemes
            - State Government Schemes (including Tamil Nadu)
            - Real-time web search for latest schemes
            """)
        else:
            st.title("ℹ️ திட்ட வழிகாட்டி AI பற்றி")
            st.markdown("""
            ### 🎯 நோக்கம்
            திட்ட வழிகாட்டி AI செயற்கை நுண்ணறிவைப் பயன்படுத்தி குடிமக்கள் அரசு நலத்திட்டங்களைக் கண்டறிய உதவுகிறது.
            
            ### ✨ அம்சங்கள்
            - **AI-இயங்கும் தேடல்**: இயற்கை மொழி புரிதல்
            - **ஸ்மார்ட் பொருத்தம்**: தொடர்புடைய திட்டங்களுக்கான சொற்பொருள் தேடல்
            - **இணைய தேடல்**: அரசு இணையதளங்களிலிருந்து சமீபத்திய திட்டங்கள்
            - **இரு மொழி ஆதரவு**: ஆங்கிலம் மற்றும் தமிழ்
            - **விரிவான தகவல்**: முழுமையான திட்ட விவரங்கள்
            - **வரலாறு கண்காணிப்பு**: உங்கள் தேடல்களைக் கண்காணிக்கவும்
            
            ### 🚀 எப்படி இயங்குகிறது
            1. உங்கள் தேவைகளை எளிய வார்த்தைகளில் விவரிக்கவும்
            2. எங்கள் AI உங்களை தொடர்புடைய திட்டங்களுடன் பொருத்துகிறது
            3. விவரங்கள் மற்றும் விண்ணப்பிக்கும் முறைகளை ஆராயவும்
            4. அதிகாரப்பூர்வ இணையதளங்கள் மற்றும் தொடர்புகளை அணுகவும்
            
            ### 📊 தரவு உள்ளடக்கம்
            - மத்திய அரசு திட்டங்கள்
            - மாநில அரசு திட்டங்கள் (தமிழ்நாடு உட்பட)
            - நிகழ்நேர இணைய தேடல்
            """)


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    main()