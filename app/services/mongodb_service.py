from pymongo import MongoClient
from pydantic_settings import BaseSettings
import os

class MongoSettings(BaseSettings):
    mongodb_uri: str
    database_name: str = "photo_distribution_db"

    class Config:
        env_file = ".env"

import certifi

class MongoDBService:
    def __init__(self, uri, db_name):
        # Increased timeouts and ensured tls=True for Atlas connectivity
        self.client = MongoClient(
            uri, 
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000
        )
        self.db = self.client[db_name]
        self.users = self.db["users"]
        self.photos = self.db["photos"]

    def save_user_encoding(self, telegram_id, encoding):
        """
        Saves user's face encoding (list of 128 numbers).
        """
        self.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"encoding": encoding.tolist() if hasattr(encoding, 'tolist') else encoding}},
            upsert=True
        )

    def save_web_user(self, web_id, encoding):
        """
        Saves web user's face encoding.
        """
        self.users.update_one(
            {"web_id": web_id},
            {"$set": {"encoding": encoding.tolist() if hasattr(encoding, 'tolist') else encoding}},
            upsert=True
        )

    def get_user_encoding(self, telegram_id):
        """
        Retrieves user's face encoding by telegram_id.
        """
        user = self.users.find_one({"telegram_id": telegram_id})
        return user["encoding"] if user else None

    def get_web_user_encoding(self, web_id):
        """
        Retrieves user's face encoding by web_id.
        """
        user = self.users.find_one({"web_id": web_id})
        return user["encoding"] if user else None

    def save_photo_metadata(self, url, public_id, encodings):
        """
        Saves photo URL and all face encodings found in it.
        """
        self.photos.insert_one({
            "url": url,
            "public_id": public_id,
            "encodings": [enc.tolist() for enc in encodings]
        })

    def find_matches_for_user(self, user_encoding, tolerance=0.6):
        """
        This is a basic implementation. For 1000s of photos, 
        you'd want to optimize this search.
        """
        import face_recognition
        import numpy as np

        matched_photos = []
        # Fetch all photos with their encodings, latest first
        photos = self.photos.find({}).sort("_id", -1)
        
        user_enc = np.array(user_encoding)
        
        for photo in photos:
            photo_encodings = [np.array(enc) for enc in photo["encodings"]]
            if not photo_encodings:
                continue
            
            matches = face_recognition.compare_faces(photo_encodings, user_enc, tolerance=tolerance)
            if any(matches):
                matched_photos.append(photo["url"])
                
        return matched_photos
