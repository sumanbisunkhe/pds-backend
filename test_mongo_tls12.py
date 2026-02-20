import os
from pymongo import MongoClient
import ssl
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")
db_name = os.getenv("DATABASE_NAME", "photo_distribution_db")

print(f"Attempting to connect to: {uri}")

try:
    # Explicitly use TLS 1.2
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.maximum_version = ssl.TLSVersion.TLSv1_2
    # Load default CA
    context.load_default_certs()
    
    client = MongoClient(
        uri, 
        tls=True,
        tlsContext=context,
        serverSelectionTimeoutMS=5000
    )
    # Trigger a connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
except Exception as e:
    print(f"Connection failed: {e}")
