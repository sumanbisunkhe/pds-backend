import os
from pymongo import MongoClient
import ssl
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")
db_name = os.getenv("DATABASE_NAME", "photo_distribution_db")

print(f"Attempting to connect to: {uri}")

try:
    # Disable certificate validation for debugging
    client = MongoClient(
        uri, 
        tls=True,
        tlsAllowInvalidCertificates=True, 
        serverSelectionTimeoutMS=5000
    )
    # Trigger a connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
except Exception as e:
    print(f"Connection failed: {e}")
