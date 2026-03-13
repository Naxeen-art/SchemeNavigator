# test_connection.py
from database.mongo_handler import db
from utils.logger import logger

def test_connection():
    """Test database connection"""
    try:
        # Test connection
        db.client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Get stats
        schemes_count = db.get_collection("schemes").count_documents({})
        users_count = db.get_collection("users").count_documents({})
        
        print(f"📊 Database Statistics:")
        print(f"   - Schemes: {schemes_count}")
        print(f"   - Users: {users_count}")
        print(f"   - Database: {db.db_name}")
        
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()