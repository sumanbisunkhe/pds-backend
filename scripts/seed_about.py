import os
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

load_dotenv()

def seed_about():
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DATABASE_NAME", "photo_distribution_db")
    
    client = MongoClient(uri, tlsCAFile=certifi.where())
    db = client[db_name]
    about_collection = db["About"]

    about_data = {
  "mission": {
    "title": "Why Fotoo?",
    "description": "Fotoo is built to eliminate the friction between capturing moments and delivering them. At professional events, guests rarely receive their photos due to manual sorting, bulk file sharing, and inefficient distribution workflows. PDS automates the entire lifecycle — from face detection and AI-based matching to instant personal delivery — ensuring every guest receives their memories securely, privately, and in real time.",
    "stats": {
      "trustedBy": "0",
      "totalEvents": "0",
      "satisfactionRate": "99%"
    }
  },
  "tech": {
    "title": "Technology",
    "description": "A production-grade AI pipeline designed for high-accuracy recognition, scalable cloud processing, and real-time distribution.",
    "features": [
      {
        "name": "AI Face Recognition Engine",
        "detail": "128-dimensional face encodings using dlib-based deep learning models for high-precision identification and low false-positive rates."
      },
      {
        "name": "Cloud-Native Image Pipeline",
        "detail": "Secure image storage and optimized CDN delivery via Cloudinary with automated processing triggers."
      },
      {
        "name": "Automated Telegram Bot",
        "detail": "Seamless user registration, identity verification via selfie, and instant photo notifications through a fully automated bot workflow."
      },
      {
        "name": "Real-Time Processing",
        "detail": "Asynchronous backend architecture with Server-Sent Events (SSE) for live updates and near-instant photo availability."
      }
    ]
  },
  "team": {
    "title": "Our Team",
    "description": "Engineering-driven leadership focused on AI, scalability, and real-time systems.",
    "members": [
      {
        "name": "Suman Bisunkhe",
        "role": "Founder & Lead Engineer",
        "image": "https://res.cloudinary.com/dxql0x0iq/image/upload/v1771658321/IMG_20260218_113356_1_voae07.jpg",
                "socials": {
                    "email": "sumanbisunkheofficial@gmail.com",
                    "linkedin": "https://linkedin.com/in/sumanbisunkhe",
                    "github": "https://github.com/sumanbisunkhe",
                    "facebook": "https://facebook.com/sumanbisunkhe"
                }
            }
        ]
    }
}
    # Clear existing and insert new
    about_collection.delete_many({})
    about_collection.insert_one(about_data)
    print("✓ About collection seeded successfully!")

if __name__ == "__main__":
    seed_about()
