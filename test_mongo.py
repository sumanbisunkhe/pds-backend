import os
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")
db_name = os.getenv("DATABASE_NAME", "photo_distribution_db")

print(f"Attempting to connect to: {uri}")

try:
    client = MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    # Trigger a connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
    db = client[db_name]
    print(f"Current collections: {db.list_collection_names()}")
    
except Exception as e:
    print(f"Connection failed: {e}")
