import os
import asyncio
import zipfile
import httpx
from fastapi import FastAPI, BackgroundTasks, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from app.services.cloudinary_service import CloudinaryService
from app.services.mongodb_service import MongoDBService
from app.services.face_recognition_service import FaceRecognitionService
from app.services.telegram_service import TelegramService
import requests
import io
import uuid
import numpy as np
from telegram import Bot

load_dotenv()

from contextlib import asynccontextmanager

async def auto_process_loop():
    """
    Infinite loop that checks for new photos every 30 seconds.
    """
    while True:
        try:
            await process_new_photos()
        except Exception as e:
            print(f"Error in auto-processing loop: {e}")
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("System started. Initializing background tasks...")
    loop_task = asyncio.create_task(auto_process_loop())
    
    # Start Telegram Bot in a separate thread
    import threading
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("Telegram Bot thread started.")
    
    yield
    # Shutdown logic
    print("System shutting down. Cleaning up...")
    loop_task.cancel()
    try:
        await loop_task
    except asyncio.CancelledError:
        print("Background loop stopped.")

app = FastAPI(title="Face-Matching Photo Distribution System", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize Services
cloudinary_service = CloudinaryService(
    os.getenv("CLOUDINARY_CLOUD_NAME"),
    os.getenv("CLOUDINARY_API_KEY"),
    os.getenv("CLOUDINARY_API_SECRET")
)

mongo_service = MongoDBService(
    os.getenv("MONGODB_URI"),
    os.getenv("DATABASE_NAME", "photo_distribution_db")
)

face_service = FaceRecognitionService()

# Mount Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    file_path = "app/static/favicon.ico"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    from fastapi import Response
    return Response(status_code=204)


from fastapi.responses import StreamingResponse
import json

# SSE implementation
subscribers = []

async def notify_subscribers(data: dict):
    """
    Push data to all active SSE subscribers.
    """
    if not subscribers:
        return
    
    message = f"data: {json.dumps(data)}\n\n"
    for queue in subscribers:
        await queue.put(message)

async def process_new_photos():
    """
    Background task to fetch images from Cloudinary and process them.
    Using Cloudinary Search API to only get 'unprocessed' photos.
    """
    print("Checking for new photos (Unprocessed)...")
    resources = cloudinary_service.list_unprocessed(folder="event_photos")
    
    if not resources:
        print("No new unprocessed photos found.")
        return

    for res in resources:
        url = res["secure_url"]
        public_id = res["public_id"]
        
        # Double check MongoDB just in case
        if mongo_service.photos.find_one({"public_id": public_id}):
            print(f"Photo {public_id} already in DB, marking as processed in Cloudinary.")
            cloudinary_service.mark_as_processed(public_id)
            continue
            
        print(f"Processing new photo: {public_id}")
        
        # Download and resize
        response = requests.get(url)
        if response.status_code == 200:
            img_bytes = face_service.resize_image(response.content)
            encodings = face_service.get_face_encodings(img_bytes)
            
            if encodings:
                # Save to DB
                mongo_service.save_photo_metadata(url, public_id, encodings)
                
                # Mark as processed in Cloudinary
                cloudinary_service.mark_as_processed(public_id)
                
                # Push to SSE
                await notify_subscribers({
                    "type": "new_photo",
                    "data": {"url": url, "public_id": public_id}
                })
                
                # Check for matches with registered users
                users = mongo_service.users.find({"encoding": {"$exists": True}})

                bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
                if bot_token and bot_token != "your_telegram_bot_token":
                    bot = Bot(token=bot_token)
                    
                    for user in users:
                        user_enc = np.array(user["encoding"])
                        import face_recognition
                        matches = face_recognition.compare_faces(encodings, user_enc, tolerance=0.6)
                        
                        if any(matches) and "telegram_id" in user:
                            try:
                                await bot.send_photo(
                                    chat_id=user["telegram_id"],
                                    photo=url,
                                    caption="Found a photo of you! 📸"
                                )
                            except Exception as e:
                                print(f"Failed to send photo to user {user['telegram_id']}: {e}")


@app.get("/api/stream")
async def stream():
    """
    SSE endpoint to stream new photo updates.
    """
    queue = asyncio.Queue()
    subscribers.append(queue)
    
    async def event_generator():
        try:
            while True:
                data = await queue.get()
                yield data
        except asyncio.CancelledError:
            subscribers.remove(queue)
            raise
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/")
async def read_index():
    return {"message": "PDS API is running. Use the React frontend to interact."}

@app.get("/api/stats")
async def get_stats():
    try:
        total_photos = mongo_service.photos.count_documents({})
        total_users = mongo_service.users.count_documents({"encoding": {"$exists": True}})
        
        # Count all encodings found across all photos
        pipeline = [
            {"$project": {"count": {"$size": "$encodings"}}},
            {"$group": {"_id": None, "total": {"$sum": "$count"}}}
        ]
        result = list(mongo_service.photos.aggregate(pipeline))
        total_encodings = result[0]["total"] if result else 0

        return {
            "total_photos": total_photos,
            "total_users": total_users,
            "total_encodings": total_encodings,
            "recent_matches": "Calculated on sync"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/recent-photos")
async def get_recent_photos():
    try:
        # Get last 12 photos
        photos = list(mongo_service.photos.find({}, {"_id": 0, "url": 1, "public_id": 1}).sort("_id", -1).limit(12))
        return photos
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/register-web")
async def register_web(file: UploadFile = File(...), web_id: str = Form(None)):
    try:
        if not web_id:
            web_id = str(uuid.uuid4())
            
        contents = await file.read()
        # Resize for faster processing
        resized_bytes = face_service.resize_image(contents)
        encodings = face_service.get_face_encodings(resized_bytes)
        
        if not encodings:
            return {"error": "No face detected in the selfie. Please try again."}
        
        # We take the first face found
        mongo_service.save_web_user(web_id, encodings[0])
        
        return {
            "web_id": web_id,
            "message": "Registration successful! We will find your photos soon."
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/my-photos")
async def get_my_photos(web_id: str):
    try:
        user_enc = mongo_service.get_web_user_encoding(web_id)
        if not user_enc:
            return {"error": "User not found. Please register first."}
            
        matched_urls = mongo_service.find_matches_for_user(user_enc)
        return {"photos": matched_urls}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/download-all")
async def download_all(web_id: str):
    try:
        user_enc = mongo_service.get_web_user_encoding(web_id)
        if not user_enc:
            return {"error": "User not found. Please register first."}
            
        matched_urls = mongo_service.find_matches_for_user(user_enc)
        if not matched_urls:
            return {"error": "No photos found for this ID."}

        async def fetch_image(client, url, index):
            try:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    return f"event_photo_{index+1}.jpg", response.content
            except Exception as e:
                print(f"Failed to download {url}: {e}")
            return None, None

        zip_buffer = io.BytesIO()
        async with httpx.AsyncClient() as client:
            tasks = [fetch_image(client, url, i) for i, url in enumerate(matched_urls)]
            results = await asyncio.gather(*tasks)

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in results:
                if filename and content:
                    zip_file.writestr(filename, content)
        
        zip_buffer.seek(0)
        
        if zip_buffer.getbuffer().nbytes == 0:
            return {"error": "Empty zip archive."}

        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment; filename=pds_photos_{web_id[:8]}.zip"}
        )
    except Exception as e:
        return {"error": str(e)}

@app.post("/process-photos")
async def trigger_processing(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_new_photos)
    return {"message": "Photo processing started in background."}

# Entry point for Telegram Bot
def run_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token and token != "your_telegram_bot_token":
        telegram_service = TelegramService(
            token,
            mongo_service,
            process_new_photos
        )
        telegram_service.run()
    else:
        print("Telegram Bot Token not configured. Bot skipped.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
