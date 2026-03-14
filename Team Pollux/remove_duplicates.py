from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["scheme_db"]
collection = db["schemes"]

seen = set()

for doc in collection.find():
    name = doc["scheme_name"]

    if name in seen:
        collection.delete_one({"_id": doc["_id"]})
    else:
        seen.add(name)

print("Duplicates removed successfully")
