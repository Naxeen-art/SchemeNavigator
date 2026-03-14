# fix_duplicate_ids.py
from database.mongo_handler import db
from utils.helpers import generate_scheme_id
from pymongo import DESCENDING

def fix_duplicate_scheme_ids():
    """Find and fix duplicate scheme IDs"""
    
    print("🔍 Finding duplicate scheme IDs...")
    
    schemes_collection = db.get_collection("schemes")
    
    # Find all duplicate scheme_ids
    pipeline = [
        {"$group": {
            "_id": "$scheme_id",
            "count": {"$sum": 1},
            "docs": {"$push": {"_id": "$_id", "name": "$scheme_name"}}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    duplicates = list(schemes_collection.aggregate(pipeline))
    
    if not duplicates:
        print("✅ No duplicate scheme IDs found!")
        return
    
    print(f"\n❌ Found {len(duplicates)} duplicate scheme IDs:")
    
    for dup in duplicates:
        scheme_id = dup['_id']
        count = dup['count']
        docs = dup['docs']
        
        print(f"\n  Scheme ID: '{scheme_id}' appears {count} times:")
        
        # Keep the first one, rename the rest
        for i, doc in enumerate(docs):
            if i == 0:
                print(f"    ✓ Keeping: {doc['name']}")
            else:
                # Generate new unique ID
                new_id = generate_scheme_id(doc['name'])
                print(f"    ✗ Renaming: {doc['name']} -> {new_id}")
                
                # Update the document
                schemes_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"scheme_id": new_id}}
                )
    
    print("\n✅ Duplicate IDs fixed!")

def list_all_scheme_ids():
    """List all scheme IDs to verify"""
    
    schemes_collection = db.get_collection("schemes")
    schemes = list(schemes_collection.find({}, {"scheme_id": 1, "scheme_name": 1}).limit(20))
    
    print("\n📋 Current scheme IDs:")
    for s in schemes:
        print(f"  {s.get('scheme_id')}: {s.get('scheme_name')}")

if __name__ == "__main__":
    fix_duplicate_scheme_ids()
    list_all_scheme_ids()