from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["tavidb"]  # Replace with your DB name

collections = db.list_collection_names()
print(f"Collections in '{db.name}': {collections}\n")

# Loop through each collection
for coll_name in collections:
    coll = db[coll_name]
    # Try to get one document to infer fields
    doc = coll.find_one()
    
    if doc:
        fields = list(doc.keys())
    else:
        fields = []  # Empty collection
    
    print(f"--- Collection: {coll_name} ---")
    if fields:
        print("Fields:", fields)
    else:
        print("No documents found. Fields cannot be inferred.")
    print()
