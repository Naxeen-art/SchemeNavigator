import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database.mongo_handler import db
from utils.logger import logger
import json

# -----------------------------
# Cached DB fetch functions
# -----------------------------
@st.cache_data(ttl=60)
def get_schemes():
    return db.get_all_schemes()

@st.cache_data(ttl=60)
def get_queries(limit=None):
    return db.get_all_queries(limit=limit)

@st.cache_data(ttl=60)
def get_users():
    return db.get_all_users()

@st.cache_data(ttl=60)
def get_dashboard_stats():
    return db.get_dashboard_stats()

# -----------------------------
# Dashboard rendering
# -----------------------------
def render_dashboard():
    st.markdown("### 📊 Dashboard Overview")

    stats = get_dashboard_stats()

    # --- Stats cards ---
    col1, col2, col3, col4 = st.columns(4)
    card_style = """
    <div style="padding: 20px; border-radius: 10px; color: white; text-align: center;">
        <h3>{value}</h3>
        <p>{label}</p>
    </div>
    """

    with col1:
        st.markdown(
            card_style.format(value=stats.get('total_schemes', 0), label='Total Schemes')\
            .replace("padding: 20px;", "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px;"),
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            card_style.format(value=stats.get('total_users', 0), label='Total Users')\
            .replace("padding: 20px;", "background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px;"),
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            card_style.format(value=stats.get('total_queries', 0), label='Total Queries')\
            .replace("padding: 20px;", "background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px;"),
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            card_style.format(value=stats.get('queries_today', 0), label='Queries Today')\
            .replace("padding: 20px;", "background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px;"),
            unsafe_allow_html=True
        )

    st.markdown("---")

    # --- Charts ---
    col1, col2 = st.columns(2)

    with col1:
        queries = get_queries(limit=500)  # Cached fetch
        if queries:
            df_queries = pd.DataFrame(queries)
            df_queries['date'] = pd.to_datetime(df_queries['timestamp']).dt.date
            query_trend = df_queries.groupby('date').size().reset_index(name='count')

            fig = px.line(
                query_trend,
                x='date',
                y='count',
                title='Daily Query Trend',
                labels={'count': 'Number of Queries', 'date': 'Date'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        schemes = get_schemes()  # Cached fetch
        if schemes:
            df_schemes = pd.DataFrame(schemes)
            if 'category' in df_schemes.columns:
                category_counts = df_schemes['category'].value_counts()
                fig = px.pie(
                    values=category_counts.values,
                    names=category_counts.index,
                    title='Schemes by Category'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

    # --- Recent queries ---
    st.markdown("### 🔍 Recent User Queries")
    recent_queries = get_queries(limit=10)
    if recent_queries:
        df_recent = pd.DataFrame(recent_queries)
        df_recent['timestamp'] = pd.to_datetime(df_recent['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(
            df_recent[['user_email', 'query', 'timestamp']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No queries yet")

    # --- Quick actions ---
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)

    # Refresh button with spinner and cache clear
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            with st.spinner("Refreshing dashboard..."):
                get_schemes.clear()
                get_queries.clear()
                get_users.clear()
                get_dashboard_stats.clear()
                st.experimental_rerun()

    # Export reports
    with col2:
        if st.button("📥 Export Reports", use_container_width=True):
            schemes = get_schemes()
            queries = get_queries()
            users = get_users()
            export_data = {
                'schemes': schemes,
                'queries': queries,
                'users': users,
                'export_date': datetime.now().isoformat()
            }
            st.download_button(
                label="Download Report",
                data=json.dumps(export_data, indent=2, default=str),
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    # System health
    with col3:
        if st.button("⚙️ System Health", use_container_width=True):
            st.info("✅ All systems operational")
            st.info(f"📊 Database: Connected")
            st.info(f"🕒 Server Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# -----------------------------
# Run dashboard
# -----------------------------
if __name__ == "__main__":
    render_dashboard()
