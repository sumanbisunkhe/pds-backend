import os
import time
import sys
import threading
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import requests

# Add project root to path so we can import app services

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.cloudinary_service import CloudinaryService

# Load environment variables
load_dotenv()

# Initialize Services
cloudinary_service = CloudinaryService(
    os.getenv("CLOUDINARY_CLOUD_NAME"),
    os.getenv("CLOUDINARY_API_KEY"),
    os.getenv("CLOUDINARY_API_SECRET")
)

# FTP Configuration
FTP_USER = os.getenv("FTP_USER", "camera")
FTP_PASSWORD = os.getenv("FTP_PASSWORD", "password123")
FTP_PORT = int(os.getenv("FTP_PORT", "2121"))
FTP_DIRECTORY = "./ftp_uploads"

# Global set to prevent duplicate processing
processed_files = set()

class PhotoFileWatcher(FileSystemEventHandler):
    """
    Watches the FTP directory for new or renamed image files and uploads them.
    This is more robust than FTP callbacks for mobile clients.
    """
    def on_created(self, event):
        self._check_and_process(event.src_path)

    def on_moved(self, event):
        self._check_and_process(event.dest_path)

    def _check_and_process(self, file_path):
        if os.path.isdir(file_path):
            return
        
        file_name = os.path.basename(file_path)
        
        # 1. Ignore hidden/temp files
        if file_name.startswith('.'):
            return

        # 2. Only process image files
        if not file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            return

        # 3. Prevent duplicate processing
        if file_name in processed_files:
            return

        # Wait a brief moment to ensure file is closed/written
        time.sleep(1.0)
        
        try:
            print(f"Detected final photo: {file_name}")
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
            
            print(f"Uploading {file_name} to Cloudinary...")
            url, public_id = cloudinary_service.upload_image(
                image_bytes, 
                folder="event_photos",
                tags=["unprocessed"]
            )
            
            if url:
                print(f"Successfully uploaded: {url}")
                processed_files.add(file_name)
                
                # TRIGGER AUTOMATIC PROCESSING
                try:
                    requests.post("http://localhost:8000/process-photos", timeout=1)
                    print("Triggered automatic face matching.")
                except:
                    pass # Backend might still be starting up

                # Cleanup from set after a while
                threading.Timer(60, lambda: processed_files.discard(file_name)).start()
                
                # IMPORTANT: Cleanup local file after upload
                os.remove(file_path)
                print(f"Cleaned up local storage for: {file_name}")

        except Exception as e:
            # If file is busy, it might be still writing. Retry once?
            print(f"Error processing {file_name}: {e}")

def run_ftp_server():
    if not os.path.exists(FTP_DIRECTORY):
        os.makedirs(FTP_DIRECTORY)

    # Start Watchdog Observer
    event_handler = PhotoFileWatcher()
    observer = Observer()
    observer.schedule(event_handler, FTP_DIRECTORY, recursive=True)
    observer.start()
    print(f"Watchdog active, monitoring: {FTP_DIRECTORY}")

    # Start FTP Server
    authorizer = DummyAuthorizer()
    authorizer.add_user(FTP_USER, FTP_PASSWORD, FTP_DIRECTORY, perm="elradfmwMT")
    
    handler = FTPHandler
    handler.authorizer = authorizer
    handler.banner = "Photo Dist Server (Watchdog Enabled)"

    server = FTPServer(("0.0.0.0", FTP_PORT), handler)
    print(f"FTP Server started on port {FTP_PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.close_all()
        observer.stop()
    observer.join()

if __name__ == "__main__":
    run_ftp_server()
