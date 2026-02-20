import os
import time
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# Load environment variables
load_dotenv()

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

FOLDER_ON_CLOUDINARY = "event_photos"
LOCAL_FOLDER_TO_WATCH = "./uploads"

class PhotoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_name = os.path.basename(file_path)
        
        # Only process image files
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            print(f"New photo detected: {file_name}")
            self.upload_to_cloudinary(file_path)

    def upload_to_cloudinary(self, file_path):
        try:
            print(f"Uploading {file_path} to Cloudinary...")
            response = cloudinary.uploader.upload(
                file_path,
                folder=FOLDER_ON_CLOUDINARY,
                tags=["unprocessed"]
            )
            print(f"Successfully uploaded! URL: {response.get('secure_url')}")
            # Optional: Move to a 'synced' folder locally
        except Exception as e:
            print(f"Error uploading {file_path}: {e}")

if __name__ == "__main__":
    if not os.path.exists(LOCAL_FOLDER_TO_WATCH):
        os.makedirs(LOCAL_FOLDER_TO_WATCH)
        print(f"Created local directory: {LOCAL_FOLDER_TO_WATCH}")

    event_handler = PhotoHandler()
    observer = Observer()
    observer.schedule(event_handler, LOCAL_FOLDER_TO_WATCH, recursive=False)
    
    print(f"Photographer Sync Active. Watching folder: {LOCAL_FOLDER_TO_WATCH}")
    print("Add photos to this folder to sync them to Cloudinary...")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
