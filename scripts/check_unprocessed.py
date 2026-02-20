import os
import sys
sys.path.append(os.getcwd())
from app.services.cloudinary_service import CloudinaryService

from dotenv import load_dotenv

load_dotenv()

cloudinary_service = CloudinaryService(
    os.getenv("CLOUDINARY_CLOUD_NAME"),
    os.getenv("CLOUDINARY_API_KEY"),
    os.getenv("CLOUDINARY_API_SECRET")
)

print("Checking Cloudinary for Unprocessed Photos...")
resources = cloudinary_service.list_unprocessed(folder="event_photos")

if not resources:
    print("No 'unprocessed' photos found in Cloudinary.")
else:
    print(f"Found {len(resources)} unprocessed photos:")
    for res in resources:
        print(f"- {res['secure_url']} (Public ID: {res['public_id']})")
