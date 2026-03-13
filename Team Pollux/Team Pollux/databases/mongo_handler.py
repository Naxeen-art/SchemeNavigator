from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from datetime import datetime
import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

class MongoDBHandler:
    def __init__(self):
        """Initialize MongoDB connection"""
        self.uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.db_name = os.getenv("DATABASE_NAME", "scheme_navigator")
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            # Test connection
            self.client.admin.command('ping')
            logger.success(f"Connected to MongoDB: {self.db_name}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def get_collection(self, collection_name):
        """Get collection by name"""
        return self.db[collection_name]
    
    # Scheme operations
    def add_scheme(self, scheme_data):
        """Add a single scheme"""
        try:
            collection = self.get_collection("schemes")
            scheme_data['created_at'] = datetime.now()
            scheme_data['updated_at'] = datetime.now()
            result = collection.insert_one(scheme_data)
            logger.info(f"Added scheme: {scheme_data.get('scheme_name')}")
            return result
        except Exception as e:
            logger.error(f"Error adding scheme: {e}")
            raise
    
    def add_schemes_bulk(self, schemes_list):
        """Add multiple schemes"""
        try:
            collection = self.get_collection("schemes")
            for scheme in schemes_list:
                scheme['created_at'] = datetime.now()
                scheme['updated_at'] = datetime.now()
            result = collection.insert_many(schemes_list)
            logger.info(f"Added {len(result.inserted_ids)} schemes")
            return result
        except Exception as e:
            logger.error(f"Error bulk adding schemes: {e}")
            raise
    
    def get_all_schemes(self):
        """Get all schemes"""
        try:
            collection = self.get_collection("schemes")
            return list(collection.find({}, {'_id': 0}))
        except Exception as e:
            logger.error(f"Error getting schemes: {e}")
            return []
    
    def get_scheme_by_id(self, scheme_id):
        """Get scheme by ID"""
        try:
            collection = self.get_collection("schemes")
            return collection.find_one({'scheme_id': scheme_id}, {'_id': 0})
        except Exception as e:
            logger.error(f"Error getting scheme {scheme_id}: {e}")
            return None
    
    def update_scheme(self, scheme_id, update_data):
        """Update a scheme"""
        try:
            collection = self.get_collection("schemes")
            update_data['updated_at'] = datetime.now()
            result = collection.update_one(
                {'scheme_id': scheme_id},
                {'$set': update_data}
            )
            logger.info(f"Updated scheme: {scheme_id}")
            return result
        except Exception as e:
            logger.error(f"Error updating scheme {scheme_id}: {e}")
            raise
    
    def delete_scheme(self, scheme_id):
        """Delete a scheme"""
        try:
            collection = self.get_collection("schemes")
            result = collection.delete_one({'scheme_id': scheme_id})
            logger.info(f"Deleted scheme: {scheme_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting scheme {scheme_id}: {e}")
            raise
    
    def clear_all_schemes(self):
        """Clear all schemes"""
        try:
            collection = self.get_collection("schemes")
            result = collection.delete_many({})
            logger.warning(f"Cleared {result.deleted_count} schemes")
            return result
        except Exception as e:
            logger.error(f"Error clearing schemes: {e}")
            raise
    
    # User operations
    def add_user(self, user_info):
        """Add or update user"""
        try:
            collection = self.get_collection("users")
            user_info['last_login'] = datetime.now()
            result = collection.update_one(
                {'email': user_info['email']},
                {'$set': user_info, '$setOnInsert': {'created_at': datetime.now()}},
                upsert=True
            )
            logger.info(f"User added/updated: {user_info['email']}")
            return result
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            raise
    
    def get_user(self, email):
        """Get user by email"""
        try:
            collection = self.get_collection("users")
            return collection.find_one({'email': email}, {'_id': 0})
        except Exception as e:
            logger.error(f"Error getting user {email}: {e}")
            return None
    
    def get_all_users(self):
        """Get all users"""
        try:
            collection = self.get_collection("users")
            return list(collection.find({}, {'_id': 0}))
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    # Query operations
    def save_user_query(self, user_email, query, response, schemes_clicked=None):
        """Save user query and response"""
        try:
            collection = self.get_collection("queries")
            query_data = {
                'user_email': user_email,
                'query': query,
                'response': response,
                'schemes_clicked': schemes_clicked or [],
                'timestamp': datetime.now()
            }
            result = collection.insert_one(query_data)
            logger.info(f"Saved query from {user_email}")
            return result
        except Exception as e:
            logger.error(f"Error saving query: {e}")
            raise
    
    def get_user_queries(self, user_email=None, limit=100):
        """Get user queries"""
        try:
            collection = self.get_collection("queries")
            query = {}
            if user_email:
                query['user_email'] = user_email
            
            return list(collection.find(query, {'_id': 0})
                       .sort('timestamp', -1)
                       .limit(limit))
        except Exception as e:
            logger.error(f"Error getting queries: {e}")
            return []
    
    def get_all_queries(self, limit=1000):
        """Get all queries"""
        try:
            collection = self.get_collection("queries")
            return list(collection.find({}, {'_id': 0})
                       .sort('timestamp', -1)
                       .limit(limit))
        except Exception as e:
            logger.error(f"Error getting all queries: {e}")
            return []
    
    # Statistics
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        try:
            stats = {
                'total_schemes': self.get_collection("schemes").count_documents({}),
                'total_users': self.get_collection("users").count_documents({}),
                'total_queries': self.get_collection("queries").count_documents({}),
                'queries_today': self.get_collection("queries").count_documents({
                    'timestamp': {'$gte': datetime.now().replace(hour=0, minute=0, second=0)}
                })
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

# Global instance
db = MongoDBHandler()