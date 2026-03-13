# init_db.py
import json
from database.mongo_handler import db
from models.scheme_model import SchemeModel
from utils.logger import logger
from utils.helpers import create_sample_schemes

def initialize_database():
    """Initialize database with sample data"""
    
    # Check if schemes already exist
    existing_schemes = db.get_all_schemes()
    
    if existing_schemes:
        print(f"✅ Database already has {len(existing_schemes)} schemes")
        return
    
    # Create sample schemes
    sample_schemes = create_sample_schemes()
    
    # Add to database
    success_count = 0
    for scheme_data in sample_schemes:
        try:
            # Validate with Pydantic model
            scheme = SchemeModel(**scheme_data)
            db.add_scheme(scheme.dict())
            success_count += 1
            print(f"✓ Added: {scheme.scheme_name}")
        except Exception as e:
            print(f"✗ Error adding scheme: {e}")
    
    print(f"\n✅ Successfully added {success_count} sample schemes to database")
    
    # Create admin user
    admin_user = {
        'email': 'admin@example.com',
        'name': 'Administrator',
        'is_admin': True
    }
    db.add_user(admin_user)
    print("✅ Added admin user")

if __name__ == "__main__":
    print("🚀 Initializing Scheme Navigator Database...")
    initialize_database()