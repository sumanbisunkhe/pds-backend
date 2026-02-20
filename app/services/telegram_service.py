from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import os
import asyncio
from app.services.face_recognition_service import FaceRecognitionService

class TelegramService:
    def __init__(self, token, mongo_service, photo_processing_callback):
        self.token = token
        self.mongo_service = mongo_service
        self.photo_processing_callback = photo_processing_callback
        self.face_service = FaceRecognitionService()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Welcome to the FOTO! 📸\n\n"
            "Please send me a clear selfie so I can send you your photos."
        )

    async def handle_selfie(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        try:
            photo_file = await update.message.photo[-1].get_file(connect_timeout=30, read_timeout=30)
            image_bytes = await photo_file.download_as_bytearray()
        except Exception as e:
            print(f"Failed to download selfie from Telegram: {e}")
            await update.message.reply_text("Failed to download your photo. Telegram servers might be slow. Please try again.")
            return
        
        await update.message.reply_text("Processing your selfie... ⏳")
        
        try:
            # Resize image to speed up processing
            resized_bytes = self.face_service.resize_image(bytes(image_bytes))
            
            # Get encoding - run in threadpool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            encodings = await loop.run_in_executor(
                None, 
                self.face_service.get_face_encodings, 
                resized_bytes
            )
            
            if not encodings:
                await update.message.reply_text("Couldn't find a face in your photo. Please try again with a clearer selfie.")
                return
            
            # Save the first face found
            user_encoding = encodings[0]
            self.mongo_service.save_user_encoding(user.id, user_encoding)
            
            await update.message.reply_text("Selfie registered! I'm now looking for your photos... 🔍")
            
            # Find already processed matches - also run match logic in threadpool if it gets heavy
            matches = await loop.run_in_executor(
                None,
                self.mongo_service.find_matches_for_user,
                user_encoding
            )
            
            if matches:
                await update.message.reply_text(f"Found {len(matches)} matches!")
                for photo_url in matches:
                    await update.message.reply_photo(photo=photo_url)
            else:
                await update.message.reply_text("No matches found yet. I'll notify you as soon as I find some!")
        except Exception as e:
            print(f"Error handling selfie for user {user.id}: {e}")
            await update.message.reply_text("An error occurred while processing your selfie. Please try again later.")

    def run(self):
        application = ApplicationBuilder().token(self.token).build()
        
        start_handler = CommandHandler('start', self.start)
        selfie_handler = MessageHandler(filters.PHOTO, self.handle_selfie)
        
        application.add_handler(start_handler)
        application.add_handler(selfie_handler)
        
        application.run_polling()
