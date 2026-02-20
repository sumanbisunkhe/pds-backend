import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGODB_URI")
db_name = os.getenv("DATABASE_NAME", "photo_distribution_db")

client = MongoClient(mongo_uri)
db = client[db_name]

print(f"Checking Database: {db_name}")

# Check Photos count
photo_count = db.photos.count_documents({})
print(f"Total Photos Processed: {photo_count}")

# Check Users count
user_count = db.users.count_documents({"encoding": {"$exists": True}})
print(f"Total Users Registered: {user_count}")

# Show recent photos
print("\nRecent Photos in Database:")
for photo in db.photos.find().sort("_id", -1).limit(5):
    print(f"- {photo['url']}")
    print(f"  Faces found: {len(photo['encodings'])}")
