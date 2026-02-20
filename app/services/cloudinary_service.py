import cloudinary
import cloudinary.uploader
import cloudinary.api
from pydantic_settings import BaseSettings
import os

class CloudinarySettings(BaseSettings):
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    class Config:
        env_file = ".env"

class CloudinaryService:
    def __init__(self, cloud_name, api_key, api_secret):
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )

    def upload_image(self, image_bytes, folder="event_photos", tags=None):
        """
        Uploads image to Cloudinary with optional tags.
        """
        if tags is None:
            tags = ["unprocessed"]
            
        try:
            response = cloudinary.uploader.upload(
                image_bytes, 
                folder=folder,
                tags=tags
            )
            return response.get("secure_url"), response.get("public_id")
        except Exception as e:
            print(f"Cloudinary upload error: {e}")
            return None, None

    def list_unprocessed(self, folder="event_photos"):
        """
        Uses Search API to find images tagged as 'unprocessed' in the specific folder.
        """
        try:
            expression = f"folder:{folder} AND tags:unprocessed"
            result = cloudinary.Search().expression(expression).execute()
            return result.get("resources", [])
        except Exception as e:
            print(f"Cloudinary search error: {e}")
            return []

    def mark_as_processed(self, public_id):
        """
        Removes 'unprocessed' tag and adds 'processed' tag.
        """
        try:
            cloudinary.uploader.replace_tag("processed", public_id)
            cloudinary.uploader.remove_tag("unprocessed", public_id)
            return True
        except Exception as e:
            print(f"Cloudinary tagging error: {e}")
            return False
