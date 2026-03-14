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
        self._ensure_indexes()
    
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
    
    def _ensure_indexes(self):
        """Ensure indexes are created for collections"""
        try:
            # Create unique index on scheme_id for schemes collection
            schemes_collection = self.get_collection("schemes")
            schemes_collection.create_index("scheme_id", unique=True, sparse=True)
            
            # Create index on email for users collection
            users_collection = self.get_collection("users")
            users_collection.create_index("email", unique=True)
            
            # Create index on timestamp for queries collection
            queries_collection = self.get_collection("queries")
            queries_collection.create_index("timestamp", -1)
            
            logger.info("Database indexes ensured")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def get_collection(self, collection_name):
        """Get collection by name"""
        return self.db[collection_name]
    
    # Scheme operations
    def add_scheme(self, scheme_data):
        """
        Add a single scheme with duplicate handling
        Returns: dict with status information
        """
        try:
            collection = self.get_collection("schemes")
            
            # Ensure scheme_id exists
            if 'scheme_id' not in scheme_data or not scheme_data['scheme_id']:
                if 'scheme_name' in scheme_data:
                    scheme_data['scheme_id'] = scheme_data['scheme_name'].lower().replace(' ', '_').replace('-', '_')
                else:
                    scheme_data['scheme_id'] = f"scheme_{datetime.now().timestamp()}"
            
            # Add timestamps
            now = datetime.now()
            scheme_data['created_at'] = now
            scheme_data['updated_at'] = now
            
            # Try to insert with error handling for duplicates
            try:
                result = collection.insert_one(scheme_data)
                logger.info(f"✅ Added new scheme: {scheme_data.get('scheme_name')} (ID: {scheme_data['scheme_id']})")
                return {"status": "inserted", "id": str(result.inserted_id), "scheme_id": scheme_data['scheme_id']}
                
            except DuplicateKeyError:
                # Scheme already exists - update it instead
                logger.info(f"🔄 Scheme already exists, updating: {scheme_data['scheme_id']}")
                
                # CRITICAL FIX: Create a copy of scheme_data for update
                update_data = scheme_data.copy()
                
                # Remove _id if it exists (MongoDB immutable field)
                if '_id' in update_data:
                    del update_data['_id']
                
                # Remove created_at to keep original creation date
                if 'created_at' in update_data:
                    del update_data['created_at']
                
                # Update updated_at
                update_data['updated_at'] = datetime.now()
                
                # Perform update WITHOUT _id field
                result = collection.update_one(
                    {"scheme_id": scheme_data["scheme_id"]},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    return {"status": "updated", "modified": result.modified_count, "scheme_id": scheme_data['scheme_id']}
                elif result.matched_count > 0:
                    return {"status": "skipped", "reason": "no_changes", "scheme_id": scheme_data['scheme_id']}
                else:
                    return {"status": "error", "reason": "not_found", "scheme_id": scheme_data['scheme_id']}
                    
        except Exception as e:
            logger.error(f"Error adding scheme: {e}")
            raise e
    
    def add_schemes_bulk(self, schemes_list):
        """
        Add multiple schemes with duplicate handling
        Returns: dict with detailed results
        """
        try:
            results = {
                "total": len(schemes_list),
                "inserted": 0,
                "updated": 0,
                "skipped": 0,
                "errors": []
            }
            
            for scheme in schemes_list:
                try:
                    # Process each scheme individually for better error handling
                    result = self.add_scheme(scheme)
                    
                    if result.get("status") == "inserted":
                        results["inserted"] += 1
                    elif result.get("status") == "updated":
                        results["updated"] += 1
                    elif result.get("status") == "skipped":
                        results["skipped"] += 1
                        
                except DuplicateKeyError:
                    results["skipped"] += 1
                except Exception as e:
                    results["errors"].append({
                        "scheme_id": scheme.get('scheme_id', 'unknown'),
                        "scheme_name": scheme.get('scheme_name', 'unknown'),
                        "error": str(e)
                    })
            
            logger.info(f"Bulk add completed: {results['inserted']} inserted, {results['updated']} updated, {results['skipped']} skipped, {len(results['errors'])} errors")
            return results
            
        except Exception as e:
            logger.error(f"Error bulk adding schemes: {e}")
            raise e
    
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
    
    def get_scheme_by_name(self, scheme_name):
        """Get scheme by name (case-insensitive search)"""
        try:
            collection = self.get_collection("schemes")
            return collection.find_one(
                {'scheme_name': {'$regex': f'^{scheme_name}$', '$options': 'i'}},
                {'_id': 0}
            )
        except Exception as e:
            logger.error(f"Error getting scheme by name {scheme_name}: {e}")
            return None
    
    def update_scheme(self, scheme_id, update_data):
        """Update a scheme"""
        try:
            collection = self.get_collection("schemes")
            update_data['updated_at'] = datetime.now()
            
            # Don't allow updating scheme_id
            if 'scheme_id' in update_data:
                del update_data['scheme_id']
            
            # Remove _id if present
            if '_id' in update_data:
                del update_data['_id']
            
            result = collection.update_one(
                {'scheme_id': scheme_id},
                {'$set': update_data}
            )
            
            if result.matched_count > 0:
                logger.info(f"Updated scheme: {scheme_id}")
                return {"status": "updated", "modified": result.modified_count}
            else:
                logger.warning(f"Scheme not found: {scheme_id}")
                return {"status": "not_found"}
                
        except Exception as e:
            logger.error(f"Error updating scheme {scheme_id}: {e}")
            raise e
    
    def upsert_scheme(self, scheme_data):
        """
        Upsert a scheme (update if exists, insert if not)
        This is an alias for add_scheme with upsert behavior
        """
        return self.add_scheme(scheme_data)
    
    def delete_scheme(self, scheme_id):
        """Delete a scheme"""
        try:
            collection = self.get_collection("schemes")
            result = collection.delete_one({'scheme_id': scheme_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted scheme: {scheme_id}")
                return {"status": "deleted", "count": result.deleted_count}
            else:
                logger.warning(f"Scheme not found for deletion: {scheme_id}")
                return {"status": "not_found"}
                
        except Exception as e:
            logger.error(f"Error deleting scheme {scheme_id}: {e}")
            raise e
    
    def clear_all_schemes(self):
        """Clear all schemes"""
        try:
            collection = self.get_collection("schemes")
            result = collection.delete_many({})
            logger.warning(f"Cleared {result.deleted_count} schemes")
            return {"status": "cleared", "count": result.deleted_count}
        except Exception as e:
            logger.error(f"Error clearing schemes: {e}")
            raise e
    
    # User operations
    def add_user(self, user_info):
        """Add or update user"""
        try:
            collection = self.get_collection("users")
            
            # Ensure email exists
            if 'email' not in user_info:
                raise ValueError("Email is required for user")
            
            user_info['last_login'] = datetime.now()
            
            # Try upsert
            result = collection.update_one(
                {'email': user_info['email']},
                {
                    '$set': user_info,
                    '$setOnInsert': {'created_at': datetime.now()}
                },
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"New user added: {user_info['email']}")
                return {"status": "inserted", "id": str(result.upserted_id)}
            else:
                logger.info(f"User updated: {user_info['email']}")
                return {"status": "updated", "matched": result.matched_count}
                
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            raise e
    
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
            return {"status": "saved", "id": str(result.inserted_id)}
        except Exception as e:
            logger.error(f"Error saving query: {e}")
            raise e
    
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
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            stats = {
                'total_schemes': self.get_collection("schemes").count_documents({}),
                'total_users': self.get_collection("users").count_documents({}),
                'total_queries': self.get_collection("queries").count_documents({}),
                'queries_today': self.get_collection("queries").count_documents({
                    'timestamp': {'$gte': today}
                }),
                'active_users_today': len(self.get_collection("queries").distinct(
                    'user_email', 
                    {'timestamp': {'$gte': today}}
                ))
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    # Search operations
    def search_schemes(self, search_term, limit=50):
        """Search schemes by name, description, or ministry"""
        try:
            collection = self.get_collection("schemes")
            
            # Case-insensitive search across multiple fields
            query = {
                '$or': [
                    {'scheme_name': {'$regex': search_term, '$options': 'i'}},
                    {'description': {'$regex': search_term, '$options': 'i'}},
                    {'ministry': {'$regex': search_term, '$options': 'i'}},
                    {'category': {'$regex': search_term, '$options': 'i'}},
                    {'beneficiaries': {'$regex': search_term, '$options': 'i'}}
                ]
            }
            
            return list(collection.find(query, {'_id': 0}).limit(limit))
        except Exception as e:
            logger.error(f"Error searching schemes: {e}")
            return []
    
    def get_schemes_by_category(self, category, limit=100):
        """Get schemes by category"""
        try:
            collection = self.get_collection("schemes")
            return list(collection.find(
                {'category': {'$regex': f'^{category}$', '$options': 'i'}},
                {'_id': 0}
            ).limit(limit))
        except Exception as e:
            logger.error(f"Error getting schemes by category: {e}")
            return []
    
    def get_schemes_by_ministry(self, ministry, limit=100):
        """Get schemes by ministry"""
        try:
            collection = self.get_collection("schemes")
            return list(collection.find(
                {'ministry': {'$regex': ministry, '$options': 'i'}},
                {'_id': 0}
            ).limit(limit))
        except Exception as e:
            logger.error(f"Error getting schemes by ministry: {e}")
            return []
    
    def get_schemes_by_state(self, state, limit=100):
        """Get schemes by state"""
        try:
            collection = self.get_collection("schemes")
            query = {'state': {'$regex': f'^{state}$', '$options': 'i'}} if state != 'Central' else {'state': 'Central'}
            return list(collection.find(query, {'_id': 0}).limit(limit))
        except Exception as e:
            logger.error(f"Error getting schemes by state: {e}")
            return []
    
    # Collection management
    def get_collection_stats(self, collection_name="schemes"):
        """Get collection statistics"""
        try:
            collection = self.get_collection(collection_name)
            return {
                "total_documents": collection.count_documents({}),
                "collection_name": collection_name,
                "database": self.db_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return None

# Global instance
db = MongoDBHandler()