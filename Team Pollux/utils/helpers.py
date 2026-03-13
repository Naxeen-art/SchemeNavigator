import re
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import streamlit as st

from utils.logger import logger

def validate_scheme_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate scheme data before processing
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['scheme_name', 'description', 'ministry']
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"
    
    # Validate scheme_name length
    if len(data['scheme_name']) < 3:
        return False, "Scheme name must be at least 3 characters"
    
    if len(data['scheme_name']) > 200:
        return False, "Scheme name must be less than 200 characters"
    
    # Validate description length
    if len(data['description']) < 10:
        return False, "Description must be at least 10 characters"
    
    # Generate scheme_id if not provided
    if 'scheme_id' not in data or not data['scheme_id']:
        data['scheme_id'] = generate_scheme_id(data['scheme_name'])
    
    return True, "Valid"

def generate_scheme_id(name: str) -> str:
    """Generate a unique scheme ID from scheme name"""
    # Convert to lowercase and replace spaces with underscores
    base_id = name.lower().strip()
    base_id = re.sub(r'[^a-z0-9\s-]', '', base_id)
    base_id = re.sub(r'[\s-]+', '_', base_id)
    
    # Add timestamp hash for uniqueness
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_hash = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:6]
    
    return f"{base_id}_{unique_hash}"

def format_scheme_for_display(scheme: Dict[str, Any]) -> Dict[str, Any]:
    """Format scheme data for display in UI"""
    formatted = scheme.copy()
    
    # Format dates
    if 'created_at' in formatted:
        if isinstance(formatted['created_at'], datetime):
            formatted['created_at'] = formatted['created_at'].strftime('%Y-%m-%d %H:%M')
    
    if 'updated_at' in formatted:
        if isinstance(formatted['updated_at'], datetime):
            formatted['updated_at'] = formatted['updated_at'].strftime('%Y-%m-%d %H:%M')
    
    # Format documents list
    if 'documents_required' in formatted:
        if isinstance(formatted['documents_required'], list):
            formatted['documents_required_display'] = ', '.join(formatted['documents_required'])
    
    # Format currency
    if 'max_income' in formatted and formatted['max_income']:
        formatted['max_income_display'] = f"₹{formatted['max_income']:,.0f}"
    
    # Format age range
    if 'min_age' in formatted and 'max_age' in formatted:
        if formatted['min_age'] == 0 and formatted['max_age'] == 100:
            formatted['age_range'] = "No age restriction"
        else:
            formatted['age_range'] = f"{formatted['min_age']} - {formatted['max_age']} years"
    
    return formatted

def parse_date_range(date_range: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Parse date range string into start and end dates"""
    date_range = date_range.lower().strip()
    now = datetime.now()
    
    if date_range == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif date_range == 'yesterday':
        start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)
    elif date_range == 'this week':
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif date_range == 'this month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif date_range == 'last 7 days':
        start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif date_range == 'last 30 days':
        start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:
        return None, None
    
    return start, end

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\-\:\;\(\)]', '', text)
    
    return text.strip()

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract important keywords from text"""
    # Common stop words
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through',
                  'during', 'before', 'after', 'above', 'below', 'is', 'are', 'was',
                  'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
                  'did', 'will', 'would', 'shall', 'should', 'may', 'might', 'must',
                  'can', 'could', 'this', 'that', 'these', 'those'}
    
    # Clean and split text
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    
    # Filter stop words
    keywords = [word for word in words if word not in stop_words]
    
    # Count frequency
    from collections import Counter
    keyword_counts = Counter(keywords)
    
    # Return most common
    return [word for word, count in keyword_counts.most_common(max_keywords)]

def create_sample_schemes() -> List[Dict[str, Any]]:
    """Create sample scheme data for testing"""
    return [
        {
            "scheme_id": "pm_kisan_001",
            "scheme_name": "PM Kisan Samman Nidhi",
            "description": "Income support scheme for small and marginal farmers",
            "ministry": "Ministry of Agriculture",
            "category": "Agriculture",
            "state": "Central",
            "eligibility": "Small and marginal farmers with landholding up to 2 hectares",
            "beneficiaries": "Farmers",
            "benefits": "₹6000 per year in three installments",
            "documents_required": ["Aadhaar Card", "Land Records", "Bank Account Details"],
            "application_process": "Apply online through PM Kisan portal or visit local agriculture office",
            "official_url": "https://pmkisan.gov.in",
            "max_income": 200000
        },
        {
            "scheme_id": "nsp_001",
            "scheme_name": "National Scholarship Portal",
            "description": "Scholarships for students from economically weaker sections",
            "ministry": "Ministry of Education",
            "category": "Education",
            "state": "Central",
            "eligibility": "Students with family income less than ₹2.5 lakh per annum",
            "beneficiaries": "Students",
            "benefits": "Up to ₹20,000 per year",
            "documents_required": ["Aadhaar Card", "Income Certificate", "Previous Year Marksheet"],
            "application_process": "Apply through National Scholarship Portal",
            "official_url": "https://scholarships.gov.in",
            "min_age": 16,
            "max_age": 25,
            "max_income": 250000
        },
        {
            "scheme_id": "pmjay_001",
            "scheme_name": "Ayushman Bharat - PM Jan Arogya Yojana",
            "description": "Health insurance coverage for vulnerable families",
            "ministry": "Ministry of Health",
            "category": "Health",
            "state": "Central",
            "eligibility": "Families identified in SECC database",
            "beneficiaries": "Poor and vulnerable families",
            "benefits": "Health cover of ₹5 lakh per family per year",
            "documents_required": ["Aadhaar Card", "SECC Certificate", "Ration Card"],
            "application_process": "Visit empaneled hospital or nearest Common Service Centre",
            "official_url": "https://pmjay.gov.in",
            "helpline": "14555"
        }
    ]

def load_sample_data():
    """Load sample data into database"""
    from database.mongo_handler import db
    from services.scheme_service import scheme_service
    
    # Check if schemes already exist
    existing = db.get_all_schemes()
    if not existing:
        sample_schemes = create_sample_schemes()
        success, errors = scheme_service.add_schemes_bulk(sample_schemes)
        if success > 0:
            logger.info(f"Loaded {success} sample schemes")
            return True, f"Loaded {success} sample schemes"
        else:
            logger.error(f"Failed to load sample schemes: {errors}")
            return False, "Failed to load sample schemes"
    else:
        return True, f"Database already has {len(existing)} schemes"

def format_currency(amount: float) -> str:
    """Format amount as currency"""
    if amount is None:
        return "N/A"
    
    if amount >= 10000000:  # 1 Crore
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 Lakh
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.0f}"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def safe_json_loads(json_str: str) -> Optional[Dict]:
    """Safely load JSON string"""
    try:
        return json.loads(json_str)
    except:
        return None

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_download_link(data: Any, filename: str, link_text: str) -> str:
    """Create a download link for data"""
    import base64
    
    if isinstance(data, (dict, list)):
        data = json.dumps(data, indent=2, default=str)
    
    b64 = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

@st.cache_data(ttl=3600)
def get_cached_schemes():
    """Get cached schemes for better performance"""
    from database.mongo_handler import db
    return db.get_all_schemes()

def clear_cache():
    """Clear Streamlit cache"""
    st.cache_data.clear()
    logger.info("Cache cleared")